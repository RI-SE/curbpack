"""Stage 02/03 producers: locus checks, forbidden fields, and llm.json diagnostics."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from common.errors import ModelError
from requirements.extract.adapter import ADAPTERS, load_adapter
from requirements.extract.pipeline import draft_pack
from requirements.workspace import extract_section


def _provisions() -> list[dict]:
    return [
        {"locus": "3", "law_text": "an assessment of the cybersecurity risks"},
        {"locus": "1(a)", "law_text": "a statement of the intended purpose"},
    ]


def _interpret_payload(rows: list[dict]) -> str:
    return json.dumps({"provisions": rows})


def _hints_payload(rows: list[dict]) -> str:
    return json.dumps({"provisions": rows})


def _good_interpret_rows() -> list[dict]:
    return [
        {"locus": "3", "id": "CRA-ANNEX-VII-RISK", "locator": "VII.3"},
        # Pipeline fixture only. Not a CRA id convention.
        {"locus": "1(a)", "id": "FIXTURE-VII-1A", "locator": "VII.1(a)"},
    ]


def _sample_proposals() -> list[dict]:
    return [
        {
            "locus": "3",
            "id": "CRA-ANNEX-VII-RISK",
            "locator": "VII.3",
            "discovery_hints": {
                "concepts": ["risk assessment"],
                "path_hints": ["*risk*assessment*", "*THREAT*"],
                "sources": [{"source": "documents"}],
            },
        },
        {"locus": "1(a)", "id": "FIXTURE-VII-1A", "locator": "VII.1(a)"},
    ]


def _file_bytes(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


class InterpretProducerTest(unittest.TestCase):
    def setUp(self):
        from requirements.extract.produce import interpret

        self.interpret = interpret
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.guidance = Path(self.tmp.name) / "interpret.txt"
        self.guidance.write_text("provisions:\n{provisions}\n", encoding="utf-8")

    def test_extra_locus_is_rejected(self):
        rows = _good_interpret_rows() + [{"locus": "9", "id": "SKIP", "locator": "VII.9"}]

        def complete(_prompt: str, _settings: dict) -> str:
            return _interpret_payload(rows)

        with self.assertRaises(ModelError):
            self.interpret(_provisions(), guidance=self.guidance, complete=complete)

    def test_missing_locus_is_rejected(self):
        def complete(_prompt: str, _settings: dict) -> str:
            return _interpret_payload([_good_interpret_rows()[0]])

        with self.assertRaises(ModelError):
            self.interpret(_provisions(), guidance=self.guidance, complete=complete)

    def test_claim_or_search_is_rejected(self):
        base = _good_interpret_rows()

        def with_claim(_prompt: str, _settings: dict) -> str:
            rows = [dict(base[0], claim="vii-3"), base[1]]
            return _interpret_payload(rows)

        def with_search(_prompt: str, _settings: dict) -> str:
            rows = [dict(base[0], search={"concepts": ["risk"]}), base[1]]
            return _interpret_payload(rows)

        with self.assertRaises(ModelError):
            self.interpret(_provisions(), guidance=self.guidance, complete=with_claim)
        with self.assertRaises(ModelError):
            self.interpret(_provisions(), guidance=self.guidance, complete=with_search)

    def test_single_call_returns_proposals_and_one_llm_note(self):
        def complete(_prompt: str, _settings: dict) -> str:
            return _interpret_payload(_good_interpret_rows())

        proposals, notes = self.interpret(
            _provisions(), guidance=self.guidance, complete=complete
        )
        self.assertEqual([row["locus"] for row in proposals], ["3", "1(a)"])
        self.assertEqual(len(notes), 1)
        note = notes[0]
        self.assertEqual(note["stage"], "interpret")
        self.assertEqual(note["strategy"], "single_call")
        self.assertEqual(note["model"], "qwen3-coder:30b")
        self.assertEqual(note["temperature"], 0.2)
        self.assertEqual(note["endpoint"], "http://127.0.0.1:11434")
        self.assertEqual(note["prompt"], str(self.guidance))
        self.assertRegex(note["prompt_sha256"], r"^[0-9a-f]{64}$")
        self.assertNotIn("max_rounds", note)


class HintsProducerTest(unittest.TestCase):
    def setUp(self):
        from requirements.extract.produce import discovery_hints

        self.discovery_hints = discovery_hints
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.guidance = Path(self.tmp.name) / "discovery_hints.txt"
        self.guidance.write_text("provisions:\n{provisions}\n", encoding="utf-8")

    def test_forbidden_fields_on_hints_are_rejected(self):
        def complete(_prompt: str, _settings: dict) -> str:
            return _hints_payload(
                [
                    {
                        "locus": "3",
                        "id": "CRA-ANNEX-VII-RISK",
                        "discovery_hints": {"concepts": ["risk"]},
                    },
                    {"locus": "1(a)", "discovery_hints": {"concepts": ["purpose"]}},
                ]
            )

        with self.assertRaises(ModelError):
            self.discovery_hints(_provisions(), guidance=self.guidance, complete=complete)


class CraXmlGuidanceTest(unittest.TestCase):
    def test_interpret_guidance_keeps_strength_pointable(self):
        text = (ADAPTERS / "cra-xml" / "prompts" / "interpret.txt").read_text(encoding="utf-8")
        self.assertIn("{provisions}", text)
        self.assertIn("shall", text)
        self.assertIn("Where applicable", text)
        self.assertIn("is not MAY", text)
        self.assertIn("Do not return a bare array", text)
        self.assertIn("claim", text)

    def test_discovery_guidance_asks_for_actionable_hints(self):
        text = (ADAPTERS / "cra-xml" / "prompts" / "discovery_hints.txt").read_text(encoding="utf-8")
        self.assertIn("{provisions}", text)
        self.assertIn("path_hints", text)
        self.assertIn("expected_evidence", text)
        self.assertIn("process description", text)
        self.assertIn("test result", text)
        self.assertNotIn("optionally path_hints", text)
        self.assertIn("not evidence", text)


class NisGuidanceTest(unittest.TestCase):
    def test_discovery_guidance_asks_for_actionable_hints(self):
        text = (ADAPTERS / "nis" / "prompts" / "discovery_hints.txt").read_text(encoding="utf-8")
        self.assertIn("{provisions}", text)
        self.assertIn("path_hints", text)
        self.assertIn("expected_evidence", text)
        self.assertIn("process description", text)
        self.assertIn("test result", text)
        self.assertNotIn("optionally path_hints", text)
        self.assertNotIn("optionally path_hints, sources", text)
        self.assertIn("Do not leave concepts, path_hints, or expected_evidence empty", text)
        self.assertIn("not evidence", text)


class StrategyReductionTest(unittest.TestCase):
    """multi_prompt keeps its recorded last-file reduction.
    propose_critique_revise sends the critique and the passage to revise.
    """

    def setUp(self):
        from requirements.extract.produce import interpret

        self.interpret = interpret
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_multi_prompt_discards_every_result_except_the_last_file(self):
        directory = Path(self.tmp.name) / "prompts"
        directory.mkdir()
        (directory / "a.txt").write_text("A\n{provisions}\n", encoding="utf-8")
        (directory / "b.txt").write_text("B\n{provisions}\n", encoding="utf-8")

        def complete(prompt: str, _settings: dict) -> str:
            if prompt.startswith("A\n"):
                return _interpret_payload(
                    [
                        {"locus": "3", "id": "FROM-A", "locator": "VII.3"},
                        {"locus": "1(a)", "id": "FROM-A-1A", "locator": "VII.1(a)"},
                    ]
                )
            return _interpret_payload(_good_interpret_rows())

        proposals, notes = self.interpret(
            _provisions(),
            guidance=directory,
            strategy="multi_prompt",
            complete=complete,
        )
        self.assertEqual(len(notes), 2)
        self.assertEqual(proposals[0]["id"], "CRA-ANNEX-VII-RISK")
        self.assertNotIn("FROM-A", [row["id"] for row in proposals])

    def test_revise_call_receives_critique_text_and_passage(self):
        guidance = Path(self.tmp.name) / "interpret.txt"
        guidance.write_text("provisions:\n{provisions}\n", encoding="utf-8")
        seen: list[tuple[str, str]] = []
        critique = json.dumps(
            {
                "findings": [
                    {
                        "field": "note",
                        "aspect": "CRITIQUE-MARKER missing a supported note",
                        "quote": "cybersecurity risks",
                        "locator": "VII.3",
                    }
                ]
            }
        )

        def complete(prompt: str, settings: dict) -> str:
            seen.append((settings["role"], prompt))
            if settings["role"] == "critique":
                return critique
            if "intended purpose" in prompt:
                return _interpret_payload([_good_interpret_rows()[1]])
            return _interpret_payload([_good_interpret_rows()[0]])

        proposals, notes = self.interpret(
            _provisions(),
            guidance=guidance,
            strategy="propose_critique_revise",
            max_rounds=1,
            complete=complete,
        )
        self.assertEqual(
            [role for role, _prompt in seen],
            ["propose", "critique", "revise", "propose", "critique", "revise"],
        )
        self.assertEqual(len(notes), 6)
        self.assertEqual([row["locus"] for row in proposals], ["3", "1(a)"])
        for prompt in (item[1] for item in seen if item[0] == "revise"):
            self.assertIn("CRITIQUE-MARKER", prompt)
            self.assertTrue(
                "cybersecurity risks" in prompt or "intended purpose" in prompt
            )


class TwoGuidanceRunsTest(unittest.TestCase):
    def setUp(self):
        from requirements.extract.produce import interpret

        self.interpret = interpret
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "workspace"
        self.root.mkdir()
        self.cra = load_adapter(ADAPTERS / "cra" / "adapter.json")
        self.adapter_dir = ADAPTERS / "cra"
        self.adapter_before = _file_bytes(self.adapter_dir)

    def test_two_guidance_paths_write_two_work_dirs_with_different_prompt_sha(self):
        first_guidance = Path(self.tmp.name) / "prompt-a.txt"
        second_guidance = Path(self.tmp.name) / "prompt-b.txt"
        first_guidance.write_text("guidance A\n{provisions}\n", encoding="utf-8")
        second_guidance.write_text("guidance B\n{provisions}\n", encoding="utf-8")

        def complete(_prompt: str, _settings: dict) -> str:
            return _interpret_payload(_good_interpret_rows())

        _proposals_a, notes_a = self.interpret(
            _provisions(), guidance=first_guidance, complete=complete
        )
        _proposals_b, notes_b = self.interpret(
            _provisions(), guidance=second_guidance, complete=complete
        )
        first = extract_section(
            self.root,
            self.adapter_dir,
            self.cra,
            "VII",
            _sample_proposals(),
            draft_pack(),
            at="2026-10-13T090000Z",
            llm_notes=notes_a,
        )
        before_first = _file_bytes(first["copy"])
        second = extract_section(
            self.root,
            self.adapter_dir,
            self.cra,
            "VII",
            _sample_proposals(),
            draft_pack(),
            at="2026-10-13T143000Z",
            llm_notes=notes_b,
        )
        self.assertEqual(_file_bytes(first["copy"]), before_first)
        self.assertEqual(_file_bytes(self.adapter_dir), self.adapter_before)
        llm_a = json.loads((first["work"] / "llm.json").read_text(encoding="utf-8"))
        llm_b = json.loads((second["work"] / "llm.json").read_text(encoding="utf-8"))
        self.assertNotEqual(llm_a["llm"][0]["prompt_sha256"], llm_b["llm"][0]["prompt_sha256"])
        self.assertNotEqual(llm_a["llm"][0]["prompt"], llm_b["llm"][0]["prompt"])
        self.assertFalse((first["copy"] / "llm.json").exists())
        self.assertFalse((second["copy"] / "llm.json").exists())


if __name__ == "__main__":
    unittest.main()
