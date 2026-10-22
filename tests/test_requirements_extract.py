"""Requirements extract: adapter load and stage 00."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from common.errors import ModelError
from requirements.extract.assemble import assemble_requirements
from requirements.extract.adapter import ADAPTERS, load_adapter, section_text, stage00
from requirements.extract.atomize import atomize
from requirements.extract.pipeline import draft_pack
from requirements.workspace import (
    create_extraction_copy,
    extract_section,
    list_working_copies,
    load_working_copy,
    select_working_copy,
)


class AdapterLoadTest(unittest.TestCase):
    def test_stub_adapter_refuses_section_text(self):
        adapter = load_adapter(ADAPTERS / "medtech" / "adapter.json")
        with self.assertRaises(ModelError):
            section_text(ADAPTERS / "medtech", adapter, "VII")

    def test_cra_stage00_lists_annex_vii_ready(self):
        adapter = load_adapter(ADAPTERS / "cra" / "adapter.json")
        listed = stage00(adapter)
        vii = next(item for item in listed["sections"] if item["id"] == "VII")
        self.assertTrue(vii["in_scope"])
        self.assertTrue(vii["ready"])
        self.assertIn("cybersecurity risks", section_text(ADAPTERS / "cra", adapter, "VII"))


class AssembleProposalTest(unittest.TestCase):
    def setUp(self):
        self.cra = load_adapter(ADAPTERS / "cra" / "adapter.json")

    def test_assemble_writes_valid_proposals_and_lists_the_rest(self):
        # Locus 8 is a provision with no proposal. Locus 9 is a proposal with
        # no provision. The plan sample used locus 9 for both, which cannot
        # be an unknown locus and an unproposed provision at once.
        provisions = [
            {"locus": "3", "law_text": "an assessment of the cybersecurity risks"},
            {"locus": "1(a)", "law_text": "a statement of the intended purpose"},
            {"locus": "8", "law_text": "not in the proposals"},
        ]
        proposals = [
            {"locus": "3", "id": "CRA-ANNEX-VII-RISK", "locator": "VII.3",
             "discovery_hints": {"concepts": ["risk assessment"]}},
            # Pipeline fixture only. Not a CRA id convention.
            {"locus": "1(a)", "id": "FIXTURE-VII-1A", "locator": "VII.1(a)"},
            {"locus": "9", "id": "SKIP", "locator": "VII.9"},
        ]
        requirements, exclusions = assemble_requirements(provisions, proposals, adapter=self.cra)
        self.assertEqual([item["id"] for item in requirements], ["CRA-ANNEX-VII-RISK", "FIXTURE-VII-1A"])
        self.assertNotIn("signed", requirements[0])
        self.assertNotIn("origin", requirements[0])
        self.assertNotIn("locus", requirements[0])
        self.assertEqual(requirements[0]["references"][0]["law_text"], provisions[0]["law_text"])
        self.assertEqual(requirements[0]["discovery_hints"], {"concepts": ["risk assessment"]})
        self.assertNotIn("edition", requirements[0]["source"])
        self.assertEqual(
            exclusions,
            [
                {"locus": "8", "reason": "no proposal"},
                {"locus": "9", "reason": "unknown locus"},
            ],
        )

    def test_claim_or_search_on_a_proposal_is_rejected(self):
        provisions = [{"locus": "3", "law_text": "an assessment of the cybersecurity risks"}]
        proposal = {"locus": "3", "id": "CRA-ANNEX-VII-RISK", "locator": "VII.3"}
        with self.assertRaises(ModelError):
            assemble_requirements(provisions, [{**proposal, "claim": "vii-3"}], adapter=self.cra)
        with self.assertRaises(ModelError):
            assemble_requirements(provisions, [{**proposal, "search": {"concepts": ["risk"]}}], adapter=self.cra)

    def test_missing_id_excludes_that_locus_and_keeps_the_sibling(self):
        provisions = [
            {"locus": "3", "law_text": "an assessment of the cybersecurity risks"},
            {"locus": "1(a)", "law_text": "a statement of the intended purpose"},
        ]
        proposals = [
            {"locus": "3", "id": "CRA-ANNEX-VII-RISK", "locator": "VII.3"},
            {"locus": "1(a)", "locator": "VII.1(a)"},
        ]
        requirements, exclusions = assemble_requirements(provisions, proposals, adapter=self.cra)
        self.assertEqual([item["id"] for item in requirements], ["CRA-ANNEX-VII-RISK"])
        self.assertEqual(exclusions, [{"locus": "1(a)", "reason": "missing id"}])


class WorkingCopyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_two_extract_directories_do_not_overwrite(self):
        root = Path(self.tmp.name)
        pack = draft_pack()
        first = create_extraction_copy(root, "cra-baseline", pack, at="2026-10-13T090000Z")
        second = create_extraction_copy(root, "cra-baseline", pack, at="2026-10-13T143000Z")
        marker = first / "REQ-A.json"
        marker.write_text("keep\n", encoding="utf-8")
        with self.assertRaises(ModelError):
            create_extraction_copy(root, "cra-baseline", pack, at="2026-10-13T090000Z")
        self.assertEqual(marker.read_text(encoding="utf-8"), "keep\n")
        self.assertEqual(
            list_working_copies(root, "cra-baseline"),
            ["2026-10-13T090000Z", "2026-10-13T143000Z"],
        )
        self.assertEqual(select_working_copy(root, "cra-baseline", "2026-10-13T090000Z"), first)
        with self.assertRaises(ModelError):
            select_working_copy(root, "cra-baseline", "missing")
        self.assertNotEqual(first, second)


def _sample_proposals() -> list[dict]:
    return [
        {"locus": "3", "id": "CRA-ANNEX-VII-RISK", "locator": "VII.3",
         "discovery_hints": {"concepts": ["risk assessment"],
                             "path_hints": ["*risk*assessment*", "*THREAT*"],
                             "sources": [{"source": "documents"}]}},
        {"locus": "1(a)", "id": "FIXTURE-VII-1A", "locator": "VII.1(a)"},
    ]


def _file_bytes(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


class ExtractSectionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cra = load_adapter(ADAPTERS / "cra" / "adapter.json")

    def test_extract_section_writes_two_requirements_in_a_new_copy(self):
        raw = (ADAPTERS / "cra").joinpath("../../data/annex_vii.txt").resolve()
        text = raw.read_text(encoding="utf-8")
        atoms = {item["locus"]: item["law_text"] for item in atomize(text)}
        result = extract_section(
            Path(self.tmp.name),
            ADAPTERS / "cra",
            self.cra,
            "VII",
            _sample_proposals(),
            draft_pack(),
            at="2026-10-13T090000Z",
        )
        pack, requirements = load_working_copy(result["copy"])
        self.assertEqual(pack["id"], "cra-baseline")
        self.assertEqual({item["id"] for item in requirements}, {"CRA-ANNEX-VII-RISK", "FIXTURE-VII-1A"})
        by_id = {item["id"]: item for item in requirements}
        self.assertEqual(by_id["FIXTURE-VII-1A"]["references"][0]["law_text"], atoms["1(a)"])
        coverage = json.loads((result["work"] / "coverage.json").read_text(encoding="utf-8"))
        self.assertEqual(coverage["status"], "incomplete")
        written = [row["locus"] for row in coverage["loci"] if row["status"] == "written"]
        self.assertEqual(sorted(written), ["1(a)", "3"])
        self.assertTrue(any(row["status"] == "excluded" for row in coverage["loci"]))

    def test_second_extract_leaves_the_first_copy_byte_identical(self):
        root = Path(self.tmp.name)
        first = extract_section(
            root, ADAPTERS / "cra", self.cra, "VII", _sample_proposals(), draft_pack(),
            at="2026-10-13T090000Z",
        )
        before = _file_bytes(first["copy"])
        extract_section(
            root, ADAPTERS / "cra", self.cra, "VII", _sample_proposals(), draft_pack(),
            at="2026-10-13T143000Z",
        )
        self.assertEqual(_file_bytes(first["copy"]), before)


class WorkingCopySelectionTest(unittest.TestCase):
    def setUp(self):
        from requirements.workspace import mark_selected, selected_copy

        self.mark_selected = mark_selected
        self.selected_copy = selected_copy
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_marking_a_later_copy_does_not_change_either_directory(self):
        root = Path(self.tmp.name)
        pack = draft_pack()
        first = create_extraction_copy(root, "cra-baseline", pack, at="2026-10-13T090000Z")
        second = create_extraction_copy(root, "cra-baseline", pack, at="2026-10-13T143000Z")
        before_first = _file_bytes(first)
        before_second = _file_bytes(second)
        self.assertIsNone(self.selected_copy(root, "cra-baseline"))
        self.mark_selected(root, "cra-baseline", "2026-10-13T090000Z")
        self.assertEqual(self.selected_copy(root, "cra-baseline"), first)
        self.mark_selected(root, "cra-baseline", "2026-10-13T143000Z")
        self.assertEqual(self.selected_copy(root, "cra-baseline"), second)
        self.assertEqual(_file_bytes(first), before_first)
        self.assertEqual(_file_bytes(second), before_second)
        self.assertFalse((first / "selection.json").exists())
        self.assertFalse((second / "selection.json").exists())
        with self.assertRaises(ModelError):
            self.mark_selected(root, "cra-baseline", "missing")
        self.assertEqual(self.selected_copy(root, "cra-baseline"), second)
        second.rename(second.parent / "gone")
        self.assertIsNone(self.selected_copy(root, "cra-baseline"))
