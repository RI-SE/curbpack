"""propose_critique_revise: critique reaches revise, stops, and leaves a trace."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from common.errors import ModelError
from requirements.extract.assemble import assemble_requirements
from requirements.extract.produce import interpret, proposals_from_producers


def _provision() -> list[dict]:
    return [{"locus": "3", "law_text": "an assessment of the cybersecurity risks"}]


def _row(**extra) -> dict:
    row = {"locus": "3", "id": "CRA-ANNEX-VII-RISK", "locator": "VII.3"}
    row.update(extra)
    return row


def _payload(row: dict) -> str:
    return json.dumps({"provisions": [row]})


def _finding(field: str = "note", aspect: str = "missing a supported note") -> str:
    return json.dumps(
        {"findings": [{"field": field, "aspect": aspect, "quote": "risks", "locator": "VII.3"}]}
    )


def _events(trace: Path) -> list[dict]:
    return [json.loads(line) for line in (trace / "events.jsonl").read_text(encoding="utf-8").splitlines() if line]


def _stops(trace: Path) -> list[dict]:
    return [event for event in _events(trace) if event["event"] == "stop"]


def _canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ReviseLoopTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.guidance = Path(self.tmp.name) / "interpret.txt"
        self.guidance.write_text("provisions:\n{provisions}\n", encoding="utf-8")

    def _run(self, complete, *, max_rounds=1, provisions=None, trace_name="trace", should_abort=None):
        trace = Path(self.tmp.name) / trace_name
        proposals, notes = interpret(
            provisions or _provision(),
            guidance=self.guidance,
            strategy="propose_critique_revise",
            max_rounds=max_rounds,
            complete=complete,
            trace_dir=trace,
            should_abort=should_abort,
        )
        return proposals, notes, trace

    def test_empty_critique_stops_without_revise_or_legal_claim(self):
        def complete(_prompt, settings):
            self.assertEqual(settings["timeout"], 600)
            settings["prompt_tokens"] = 4
            settings["completion_tokens"] = 9
            if settings["role"] == "critique":
                return json.dumps({"findings": []})
            return _payload(_row(note="draft"))

        proposals, notes, trace = self._run(complete)
        roles = [event["role"] for event in _events(trace) if event["event"] == "model_call"]
        self.assertEqual(roles, ["propose", "critique"])
        self.assertEqual(_stops(trace)[0]["reason"], "no_issues_reported")
        self.assertNotIn("legally_correct", (trace / "events.jsonl").read_text(encoding="utf-8"))
        self.assertEqual(proposals[0]["note"], "draft")
        self.assertIn(
            '{"provisions":[ one object for this provision ]}',
            (trace / "calls" / "0001.prompt.txt").read_text(encoding="utf-8"),
        )
        self.assertEqual(notes[0]["strategy"], "propose_critique_revise")
        self.assertEqual(notes[0]["max_rounds"], 1)
        self.assertNotIn("findings", notes[0])
        call = next(event for event in _events(trace) if event["event"] == "model_call")
        self.assertEqual(call["prompt_tokens"], 4)
        self.assertEqual(call["completion_tokens"], 9)

    def test_max_rounds_is_a_hard_cap(self):
        revisions = {"n": 0}

        def complete(_prompt, settings):
            if settings["role"] == "critique":
                return _finding()
            if settings["role"] == "revise":
                revisions["n"] += 1
                return _payload(_row(note=f"edit-{revisions['n']}"))
            return _payload(_row(note="edit-0"))

        proposals, _notes, trace = self._run(complete, max_rounds=10)
        self.assertEqual(revisions["n"], 10)
        self.assertEqual(proposals[0]["note"], "edit-10")
        self.assertEqual(_stops(trace)[0]["reason"], "max_rounds")

    def test_invalid_revision_keeps_the_last_valid_candidate(self):
        def complete(_prompt, settings):
            if settings["role"] == "revise":
                return "NOT-JSON"
            if settings["role"] == "critique":
                return _finding()
            return _payload(_row(note="kept"))

        proposals, _notes, trace = self._run(complete)
        self.assertEqual(proposals[0]["note"], "kept")
        self.assertEqual(_stops(trace)[0]["reason"], "invalid_response")
        attempts = [event["attempt"] for event in _events(trace) if event.get("role") == "revise"]
        self.assertEqual(attempts, [1, 2, 3])
        text = "\n".join(path.read_text(encoding="utf-8") for path in (trace / "calls").glob("*.response.txt"))
        self.assertIn("NOT-JSON", text)

    def test_regression_does_not_drop_an_unchallenged_field(self):
        def complete(_prompt, settings):
            if settings["role"] == "critique":
                return _finding(field="scope", aspect="scope was not supported")
            if settings["role"] == "revise":
                return _payload(_row())
            return _payload(_row(note="kept"))

        proposals, _notes, trace = self._run(complete, max_rounds=2)
        self.assertEqual(proposals[0]["note"], "kept")
        rejected = [event for event in _events(trace) if event["event"] == "revision"]
        self.assertEqual(rejected[0]["decision"], "reject")
        self.assertIn("dropped note", rejected[0]["reason"])

    def test_identical_revision_stops_for_no_actionable_change(self):
        def complete(_prompt, settings):
            if settings["role"] == "critique":
                return _finding()
            return _payload(_row(note="same"))

        _proposals, _notes, trace = self._run(complete, max_rounds=4)
        self.assertEqual(_stops(trace)[0]["reason"], "no_actionable_change")
        revises = [event for event in _events(trace) if event.get("role") == "revise"]
        self.assertEqual(len(revises), 1)

    def test_trace_replays_the_accepted_candidate_without_llm_notes(self):
        def complete(_prompt, settings):
            if settings["role"] == "critique":
                return _finding(field="note")
            if settings["role"] == "revise":
                return _payload(_row(note="accepted"))
            return _payload(_row(note="first"))

        _proposals, notes, trace = self._run(complete)
        self.assertNotIn("accepted", json.dumps(notes))
        stop = _stops(trace)[0]
        loaded = json.loads((trace / stop["candidate"]).read_text(encoding="utf-8"))
        self.assertEqual(loaded["note"], "accepted")
        self.assertEqual(_sha(_canonical(loaded)), stop["candidate_sha256"])
        accepted = [event for event in _events(trace) if event["event"] == "revision" and event["decision"] == "accept"]
        self.assertEqual(len(accepted), 1)
        manifest = json.loads((trace / "manifest.json").read_text(encoding="utf-8"))
        digest = hashlib.sha256((trace / "events.jsonl").read_bytes()).hexdigest()
        self.assertEqual(manifest["events_sha256"], digest)
        self.assertEqual(manifest["outputs"][0]["stop"], stop["reason"])
        self.assertEqual(manifest["outputs"][0]["candidate_sha256"], stop["candidate_sha256"])

    def test_prompt_hash_is_stable_and_a_later_run_does_not_touch_the_first(self):
        def complete(_prompt, settings):
            if settings["role"] == "critique":
                return json.dumps({"findings": []})
            return _payload(_row())

        _a, _notes, first = self._run(complete, trace_name="run-a")
        before = (first / "events.jsonl").read_bytes()
        _b, _notes, second = self._run(complete, trace_name="run-b")
        self.assertEqual((first / "events.jsonl").read_bytes(), before)
        first_call = next(event for event in _events(first) if event["event"] == "model_call")
        second_call = next(event for event in _events(second) if event["event"] == "model_call")
        self.assertEqual(first_call["prompt_sha256"], second_call["prompt_sha256"])
        self.assertNotEqual(json.loads((first / "manifest.json").read_text())["run_id"], json.loads((second / "manifest.json").read_text())["run_id"])

    def test_abort_between_calls_leaves_a_terminal_event(self):
        calls = {"n": 0}

        def should_abort():
            return calls["n"] >= 1

        def complete(_prompt, _settings):
            calls["n"] += 1
            return _payload(_row())

        with self.assertRaises(ModelError) as caught:
            self._run(complete, should_abort=should_abort)
        self.assertEqual(caught.exception.field, "aborted")
        self.assertEqual(calls["n"], 1)
        trace = Path(self.tmp.name) / "trace"
        kinds = [event["event"] for event in _events(trace)]
        self.assertIn("abort", kinds)
        self.assertEqual(kinds[-1], "run_end")
        self.assertEqual(_events(trace)[-1]["status"], "aborted")
        self.assertIn("not cancelled", json.dumps(_events(trace)))

    def test_existing_trace_directory_is_refused_before_any_call(self):
        trace = Path(self.tmp.name) / "trace"
        trace.mkdir()
        calls = {"n": 0}

        def complete(_prompt, _settings):
            calls["n"] += 1
            return _payload(_row())

        with self.assertRaises(ModelError):
            interpret(
                _provision(),
                guidance=self.guidance,
                strategy="propose_critique_revise",
                max_rounds=1,
                complete=complete,
                trace_dir=trace,
            )
        self.assertEqual(calls["n"], 0)

    def test_single_call_rejects_a_trace_directory(self):
        trace = Path(self.tmp.name) / "trace"

        def complete(_prompt, _settings):
            return _payload(_row())

        with self.assertRaises(ModelError):
            interpret(_provision(), guidance=self.guidance, complete=complete, trace_dir=trace)
        self.assertFalse(trace.exists())

    def test_secrets_are_redacted_in_the_prompt_snapshot(self):
        self.guidance.write_text("Authorization: super-secret\n{provisions}\n", encoding="utf-8")

        def complete(_prompt, settings):
            if settings["role"] == "critique":
                return json.dumps({"findings": []})
            return _payload(_row())

        _proposals, _notes, trace = self._run(complete)
        prompt = (trace / "calls" / "0001.prompt.txt").read_text(encoding="utf-8")
        self.assertNotIn("super-secret", prompt)
        self.assertIn("[redacted]", prompt)

    def test_output_is_accepted_by_assembly_and_leaves_other_files_alone(self):
        frozen = Path(self.tmp.name) / "2026-10-13T134627Z"
        frozen.mkdir()
        (frozen / "pack.json").write_bytes(b'{"id":"frozen"}')
        reference = Path(self.tmp.name) / "reference.json"
        reference.write_bytes(b"gold")

        def complete(_prompt, settings):
            if settings["role"] == "critique":
                return json.dumps({"findings": []})
            return _payload(_row(note="draft"))

        proposals, _notes, _trace = self._run(complete)
        requirements, exclusions = assemble_requirements(
            _provision(),
            proposals,
            adapter={
                "id": "cra-xml",
                "pack_id": "cra-xml-baseline",
                "source": {
                    "framework": "EU",
                    "instrument": "CRA",
                    "identifier": "CELEX:32024R2847",
                    "language": "en",
                    "url": "https://example.test/cra",
                },
            },
        )
        self.assertEqual(exclusions, [])
        self.assertEqual(requirements[0]["id"], "CRA-ANNEX-VII-RISK")
        self.assertEqual(requirements[0]["references"][0]["law_text"], "an assessment of the cybersecurity risks")
        self.assertEqual((frozen / "pack.json").read_bytes(), b'{"id":"frozen"}')
        self.assertEqual(reference.read_bytes(), b"gold")

    def test_both_stages_share_one_trace_and_return_every_locus(self):
        adapter = Path(self.tmp.name) / "adapter"
        (adapter / "prompts").mkdir(parents=True)
        (adapter / "prompts" / "interpret.txt").write_text("INTERPRET\n{provisions}\n", encoding="utf-8")
        (adapter / "prompts" / "discovery_hints.txt").write_text("HINTS\n{provisions}\n", encoding="utf-8")
        provisions = [
            {"locus": "3", "law_text": "an assessment of the cybersecurity risks"},
            {"locus": "1(a)", "law_text": "a statement of the intended purpose"},
        ]

        def complete(prompt, settings):
            if settings["role"] == "critique":
                return json.dumps({"findings": []})
            self.assertEqual(settings["max_rounds"], 2)
            locus = "1(a)" if "intended purpose" in prompt else "3"
            if settings["stage"] == "discovery_hints":
                return json.dumps({"provisions": [{"locus": locus}]})
            rows = {
                "3": {"locus": "3", "id": "CRA-ANNEX-VII-RISK", "locator": "VII.3"},
                "1(a)": {"locus": "1(a)", "id": "FIXTURE-VII-1A", "locator": "VII.1(a)"},
            }
            return json.dumps({"provisions": [rows[locus]]})

        trace = Path(self.tmp.name) / "both"
        proposals, _notes = proposals_from_producers(
            provisions,
            adapter_dir=adapter,
            strategy="propose_critique_revise",
            max_rounds=2,
            complete=complete,
            trace_dir=trace,
        )
        self.assertEqual([row["locus"] for row in proposals], ["3", "1(a)", "3", "1(a)"])
        stages = [event["stage"] for event in _events(trace) if event["event"] == "stage_start"]
        self.assertEqual(stages, ["interpret", "discovery_hints"])
        self.assertEqual(len([event for event in _events(trace) if event["event"] == "run_start"]), 1)
        self.assertIn(str(adapter), _events(trace)[0]["adapter_dir"])


class GuidanceFileTest(unittest.TestCase):
    def test_loop_guidance_has_no_reference_answer(self):
        root = Path(__file__).resolve().parents[1] / "requirements" / "extract" / "guidance"
        for name in ("critique.txt", "revise.txt"):
            text = (root / name).read_text(encoding="utf-8")
            self.assertNotIn("bill of materials", text.lower())
            self.assertNotIn("VII.2", text)


if __name__ == "__main__":
    unittest.main()
