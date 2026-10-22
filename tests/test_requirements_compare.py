"""Compare reads two Pack snapshots and does not write either one."""

from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from common.canonical import version_digest
from common.errors import ModelError
from common.store import load_requirement, save_requirement
from requirements.editing import apply_edits
from requirements.extract.pipeline import draft_pack, extract_annex_vii_risk
from requirements.workspace import create_extraction_copy


def _bytes(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def _with_id(requirement: dict, requirement_id: str, locator: str, law_text: str) -> dict:
    out = copy.deepcopy(requirement)
    out.pop("signed", None)
    out["id"] = requirement_id
    out["references"] = [{"nr": 1, "locator": locator, "law_text": law_text}]
    return out


class CompareCopiesTest(unittest.TestCase):
    def setUp(self):
        from requirements.compare import compare_copies

        self.compare_copies = compare_copies
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.base = extract_annex_vii_risk()

    def _pair(self):
        left = create_extraction_copy(self.root, "cra-baseline", draft_pack(), at="2026-10-13T090000Z")
        right = create_extraction_copy(self.root, "cra-baseline", draft_pack(), at="2026-10-13T143000Z")
        return left, right

    def _assert_unchanged(self, left: Path, right: Path, before_left: dict, before_right: dict) -> None:
        self.assertEqual(_bytes(left), before_left)
        self.assertEqual(_bytes(right), before_right)

    def test_identical_copies_are_unchanged(self):
        left, right = self._pair()
        save_requirement(left, self.base)
        save_requirement(right, self.base)
        before_left, before_right = _bytes(left), _bytes(right)
        result = self.compare_copies(left, right)
        self.assertEqual(result["unchanged"], ["CRA-ANNEX-VII-RISK"])
        self.assertEqual(result["changed"], [])
        self.assertEqual(result["only_left"], [])
        self.assertEqual(result["only_right"], [])
        self._assert_unchanged(left, right, before_left, before_right)

    def test_changed_hint_and_source_args_are_listed(self):
        left, right = self._pair()
        save_requirement(left, self.base)
        hints = copy.deepcopy(self.base["discovery_hints"])
        hints["sources"][0]["args"] = {"path": "docs"}
        changed = apply_edits(
            self.base,
            {"remediation_hint": "A different hint.", "discovery_hints": hints},
        )
        save_requirement(right, changed)
        before_left, before_right = _bytes(left), _bytes(right)
        result = self.compare_copies(left, right)
        self.assertEqual(
            result["changed"],
            [
                {
                    "id": "CRA-ANNEX-VII-RISK",
                    "fields": ["discovery_hints", "discovery_hints.sources[].args", "remediation_hint"],
                }
            ],
        )
        self._assert_unchanged(left, right, before_left, before_right)

    def test_added_and_removed_ids_stay_on_their_side(self):
        left, right = self._pair()
        other = _with_id(self.base, "FIXTURE-VII-1A", "VII.1(a)", "a statement of the intended purpose")
        save_requirement(left, self.base)
        save_requirement(left, other)
        save_requirement(right, self.base)
        before_left, before_right = _bytes(left), _bytes(right)
        removed = self.compare_copies(left, right)
        self.assertEqual(removed["only_left"], ["FIXTURE-VII-1A"])
        self.assertEqual(removed["unchanged"], ["CRA-ANNEX-VII-RISK"])
        self._assert_unchanged(left, right, before_left, before_right)

        added_left, added_right = self._pair_at("2026-10-13T150000Z", "2026-10-13T160000Z")
        save_requirement(added_left, self.base)
        save_requirement(added_right, self.base)
        save_requirement(added_right, other)
        before_left, before_right = _bytes(added_left), _bytes(added_right)
        added = self.compare_copies(added_left, added_right)
        self.assertEqual(added["only_right"], ["FIXTURE-VII-1A"])
        self.assertEqual(added["only_left"], [])
        self._assert_unchanged(added_left, added_right, before_left, before_right)

    def test_two_locators_match_two_requirements_without_writing(self):
        left, right = self._pair()
        combined = copy.deepcopy(self.base)
        combined["references"] = [
            {"nr": 1, "locator": "VII.3", "law_text": self.base["references"][0]["law_text"]},
            {"nr": 2, "locator": "VII.1(a)", "law_text": "a statement of the intended purpose"},
        ]
        save_requirement(left, combined)
        save_requirement(right, _with_id(self.base, "FIXTURE-VII-3", "VII.3", combined["references"][0]["law_text"]))
        save_requirement(
            right,
            _with_id(self.base, "FIXTURE-VII-1A", "VII.1(a)", "a statement of the intended purpose"),
        )
        before_left, before_right = _bytes(left), _bytes(right)
        result = self.compare_copies(left, right)
        self.assertEqual(
            result["possible_split"],
            [{"left_id": "CRA-ANNEX-VII-RISK", "right_ids": ["FIXTURE-VII-1A", "FIXTURE-VII-3"]}],
        )
        self.assertEqual(result["possible_consolidation"], [])
        self.assertEqual(result["only_left"], [])
        self.assertEqual(result["only_right"], [])
        self.assertEqual(result["ambiguous"], [])
        self._assert_unchanged(left, right, before_left, before_right)

    def test_one_locator_matching_two_requirements_is_ambiguous(self):
        left, right = self._pair()
        save_requirement(left, self.base)
        save_requirement(right, _with_id(self.base, "FIXTURE-A", "VII.3", self.base["references"][0]["law_text"]))
        save_requirement(right, _with_id(self.base, "FIXTURE-B", "VII.3", self.base["references"][0]["law_text"]))
        before_left, before_right = _bytes(left), _bytes(right)
        result = self.compare_copies(left, right)
        self.assertEqual(result["possible_split"], [])
        self.assertEqual(result["possible_consolidation"], [])
        self.assertEqual(result["ambiguous"], [{"locator": "VII.3", "left_id": "CRA-ANNEX-VII-RISK", "right_ids": ["FIXTURE-A", "FIXTURE-B"]}])
        self._assert_unchanged(left, right, before_left, before_right)

    def _pair_at(self, left_at: str, right_at: str):
        left = create_extraction_copy(self.root, "cra-baseline", draft_pack(), at=left_at)
        right = create_extraction_copy(self.root, "cra-baseline", draft_pack(), at=right_at)
        return left, right


class CompareTransferTest(unittest.TestCase):
    def setUp(self):
        from requirements.compare import apply_transfer, preview_transfer

        self.apply_transfer = apply_transfer
        self.preview_transfer = preview_transfer
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.base = extract_annex_vii_risk()

    def test_one_field_transfer_keeps_source_bytes_and_destination_args(self):
        source = create_extraction_copy(self.root, "cra-baseline", draft_pack(), at="2026-10-13T090000Z")
        destination = create_extraction_copy(self.root, "cra-baseline", draft_pack(), at="2026-10-13T143000Z")
        hints = copy.deepcopy(self.base["discovery_hints"])
        hints["sources"][0]["args"] = {"path": "docs"}
        source_requirement = apply_edits(self.base, {"remediation_hint": "from the source"})
        destination_requirement = apply_edits(
            self.base,
            {"discovery_hints": hints, "remediation_hint": "old hint"},
        )
        save_requirement(source, source_requirement)
        save_requirement(destination, destination_requirement)
        before_source = _bytes(source)
        preview = self.preview_transfer(
            destination,
            "CRA-ANNEX-VII-RISK",
            {"remediation_hint": "from the source"},
        )
        self.assertEqual(preview["errors"], [])
        self.assertEqual(preview["requirement"]["remediation_hint"], "from the source")
        self.assertEqual(preview["requirement"]["discovery_hints"]["sources"][0]["args"], {"path": "docs"})
        self.assertEqual(_bytes(source), before_source)
        self.apply_transfer(
            source,
            destination,
            "CRA-ANNEX-VII-RISK",
            {"remediation_hint": "from the source"},
            source_digest=version_digest(source_requirement),
            destination_digest=version_digest(destination_requirement),
        )
        saved = load_requirement(destination / "CRA-ANNEX-VII-RISK.json")
        self.assertEqual(saved["remediation_hint"], "from the source")
        self.assertEqual(saved["discovery_hints"]["sources"][0]["args"], {"path": "docs"})
        self.assertEqual(_bytes(source), before_source)

    def test_stale_destination_digest_writes_nothing(self):
        source = create_extraction_copy(self.root, "cra-baseline", draft_pack(), at="2026-10-13T090000Z")
        destination = create_extraction_copy(self.root, "cra-baseline", draft_pack(), at="2026-10-13T143000Z")
        source_requirement = apply_edits(self.base, {"remediation_hint": "from the source"})
        destination_requirement = apply_edits(self.base, {"remediation_hint": "old hint"})
        save_requirement(source, source_requirement)
        save_requirement(destination, destination_requirement)
        stale = version_digest(destination_requirement)
        replacement = apply_edits(destination_requirement, {"remediation_hint": "changed on disk"})
        save_requirement(destination, replacement)
        before_destination = _bytes(destination)
        before_source = _bytes(source)
        with self.assertRaises(ModelError):
            self.apply_transfer(
                source,
                destination,
                "CRA-ANNEX-VII-RISK",
                {"remediation_hint": "from the source"},
                source_digest=version_digest(source_requirement),
                destination_digest=stale,
            )
        self.assertEqual(_bytes(destination), before_destination)
        self.assertEqual(_bytes(source), before_source)

    def test_published_directory_is_not_a_destination(self):
        source = create_extraction_copy(self.root, "cra-baseline", draft_pack(), at="2026-10-13T090000Z")
        published = self.root / "published" / "cra-baseline" / "0.1.0"
        published.mkdir(parents=True)
        marker = published / "pack.json"
        marker.write_text("{}\n", encoding="utf-8")
        source_requirement = apply_edits(self.base, {"remediation_hint": "from the source"})
        save_requirement(source, source_requirement)
        before = marker.read_bytes()
        with self.assertRaises(ModelError):
            self.preview_transfer(published, "CRA-ANNEX-VII-RISK", {"remediation_hint": "from the source"})
        with self.assertRaises(ModelError):
            self.apply_transfer(
                source,
                published,
                "CRA-ANNEX-VII-RISK",
                {"remediation_hint": "from the source"},
                source_digest=version_digest(source_requirement),
                destination_digest=None,
            )
        self.assertEqual(marker.read_bytes(), before)

    def test_extraction_review_updates_only_the_chosen_field(self):
        from requirements.compare import apply_extraction_choices, extraction_review

        working = create_extraction_copy(self.root, "cra-baseline", draft_pack(), at="2026-10-13T090000Z")
        proposal = create_extraction_copy(self.root, "cra-baseline", draft_pack(), at="2026-10-13T143000Z")
        current = apply_edits(self.base, {"note": "already edited", "remediation_hint": "keep this"})
        incoming = apply_edits(self.base, {"note": "from extraction", "remediation_hint": "from extraction"})
        save_requirement(working, current)
        save_requirement(proposal, incoming)
        review = extraction_review(working, proposal)
        names = [field["name"] for field in review["updates"][0]["fields"]]
        self.assertIn("note", names)
        self.assertIn("remediation_hint", names)
        before_proposal = _bytes(proposal)
        apply_extraction_choices(
            working,
            proposal,
            [
                {
                    "id": "CRA-ANNEX-VII-RISK",
                    "fields": ["note"],
                    "source_digest": review["updates"][0]["source_digest"],
                    "destination_digest": review["updates"][0]["destination_digest"],
                }
            ],
        )
        saved = load_requirement(working / "CRA-ANNEX-VII-RISK.json")
        self.assertEqual(saved["note"], "from extraction")
        self.assertEqual(saved["remediation_hint"], "keep this")
        self.assertEqual(_bytes(proposal), before_proposal)

    def test_one_changed_value_leaves_the_other_value(self):
        from requirements.compare import apply_extraction_choices, extraction_review

        working = create_extraction_copy(self.root, "cra-baseline", draft_pack(), at="2026-10-13T090000Z")
        proposal = create_extraction_copy(self.root, "cra-baseline", draft_pack(), at="2026-10-13T143000Z")
        current_hints = copy.deepcopy(self.base["discovery_hints"])
        proposed_hints = copy.deepcopy(current_hints)
        current_hints["concepts"] = ["alpha", "beta"]
        proposed_hints["concepts"] = ["ALPHA", "BETA"]
        merged = copy.deepcopy(current_hints)
        merged["concepts"] = ["ALPHA", "beta"]
        current = apply_edits(self.base, {"discovery_hints": current_hints, "note": "keep this"})
        incoming = apply_edits(self.base, {"discovery_hints": proposed_hints, "note": "from extraction"})
        save_requirement(working, current)
        save_requirement(proposal, incoming)
        review = extraction_review(working, proposal)
        apply_extraction_choices(
            working,
            proposal,
            [
                {
                    "id": "CRA-ANNEX-VII-RISK",
                    "fields": [],
                    "partial": {"discovery_hints": merged},
                    "source_digest": review["updates"][0]["source_digest"],
                    "destination_digest": review["updates"][0]["destination_digest"],
                }
            ],
        )
        saved = load_requirement(working / "CRA-ANNEX-VII-RISK.json")
        self.assertEqual(saved["discovery_hints"]["concepts"], ["ALPHA", "beta"])
        self.assertEqual(saved["note"], "keep this")
        invented = copy.deepcopy(merged)
        invented["concepts"] = ["nope", "beta"]
        with self.assertRaises(ModelError):
            apply_extraction_choices(
                working,
                proposal,
                [
                    {
                        "id": "CRA-ANNEX-VII-RISK",
                        "fields": [],
                        "partial": {"discovery_hints": invented},
                        "source_digest": review["updates"][0]["source_digest"],
                        "destination_digest": version_digest(saved),
                    }
                ],
            )


class ExtractReviewPageTest(unittest.TestCase):
    def test_page_leaves_unchecked_fields_and_updates_the_chosen_one(self):
        import threading
        import urllib.parse
        import urllib.request
        from http.server import ThreadingHTTPServer

        from app.server import Workspace, make_handler
        from requirements.compare import extraction_review
        from requirements.workspace import mark_selected, read_selection

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        base = extract_annex_vii_risk()
        working = create_extraction_copy(root, "cra-baseline", draft_pack(), at="2026-10-13T090000Z")
        proposal = create_extraction_copy(root, "cra-baseline", draft_pack(), at="2026-10-13T143000Z")
        save_requirement(working, apply_edits(base, {"note": "already edited", "remediation_hint": "keep this"}))
        save_requirement(proposal, apply_edits(base, {"note": "from extraction", "remediation_hint": "from extraction"}))
        mark_selected(root, "cra-baseline", working.name)
        review = extraction_review(working, proposal)
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(httpd.shutdown)
        base_url = f"http://127.0.0.1:{httpd.server_address[1]}"
        page = urllib.request.urlopen(
            base_url
            + "/requirements/extract/review?proposal=2026-10-13T143000Z&destination=2026-10-13T090000Z"
        ).read().decode("utf-8")
        self.assertIn("Use the new definition", page)
        self.assertNotIn("Update Note", page)
        self.assertNotIn("what to look for", page)
        self.assertIn("Red", page)
        self.assertIn("that value only", page)
        self.assertIn("diff-pick", page)
        self.assertIn("already edited", page)
        self.assertIn("from extraction", page)
        self.assertIn("/vendor/jsondiffpatch.js", page)
        self.assertNotIn("<p>Your copy</p>", page)
        vendor = urllib.request.urlopen(base_url + "/vendor/jsondiffpatch.js")
        self.assertEqual(vendor.status, 200)
        self.assertIn(b"jsondiffpatch", vendor.read(400))
        self.assertNotIn('type="checkbox" name="field" value="CRA-ANNEX-VII-RISK|note" checked', page)
        item = review["updates"][0]
        form = urllib.parse.urlencode(
            {
                "proposal": "2026-10-13T143000Z",
                "destination": "2026-10-13T090000Z",
                "pair": f"CRA-ANNEX-VII-RISK|{item['source_digest']}|{item['destination_digest']}",
                "field": "CRA-ANNEX-VII-RISK|note",
            }
        ).encode("utf-8")
        brought = urllib.request.urlopen(
            urllib.request.Request(base_url + "/requirements/extract/review", data=form, method="POST")
        ).read().decode("utf-8")
        self.assertIn("Updated the fields you chose", brought)
        saved = load_requirement(working / "CRA-ANNEX-VII-RISK.json")
        self.assertEqual(saved["note"], "from extraction")
        self.assertEqual(saved["remediation_hint"], "keep this")
        self.assertEqual(read_selection(root)["timestamp"], working.name)
