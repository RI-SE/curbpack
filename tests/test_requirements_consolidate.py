"""Consolidation suggestions do not write the working copy."""

from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from common.canonical import version_digest
from common.errors import ModelError
from common.signing import generate_keypair
from common.store import load_requirement, save_requirement
from requirements.editing import apply_edits, publish_requirement, seal_pack_directory
from requirements.extract.pipeline import draft_pack, extract_annex_vii_risk
from requirements.workspace import create_extraction_copy, publish_pack


def _bytes(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


class ConsolidateSuggestTest(unittest.TestCase):
    def setUp(self):
        from requirements.consolidate import preview_consolidation, suggest_consolidations

        self.preview_consolidation = preview_consolidation
        self.suggest_consolidations = suggest_consolidations
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.base = extract_annex_vii_risk()
        self.copy = create_extraction_copy(
            self.root, "cra-baseline", draft_pack(), at="2026-10-13T090000Z"
        )

    def test_shared_locator_is_suggested_and_note_conflict_needs_a_choice(self):
        other = copy.deepcopy(self.base)
        other.pop("signed", None)
        other["id"] = "FIXTURE-VII-1A"
        other["references"] = [
            {
                "nr": 1,
                "locator": "VII.3",
                "law_text": "a different passage with the same locator",
            }
        ]
        left = apply_edits(self.base, {"note": "Keep the first note."})
        right = apply_edits(other, {"note": "Keep the second note."})
        save_requirement(self.copy, left)
        save_requirement(self.copy, right)
        before = _bytes(self.copy)
        suggestions = self.suggest_consolidations(self.copy)
        self.assertEqual(_bytes(self.copy), before)
        match = next(item for item in suggestions if set(item["ids"]) == {"CRA-ANNEX-VII-RISK", "FIXTURE-VII-1A"})
        self.assertIn("VII.3", match["reason"])
        references = [
            {"locator": "VII.3", "law_text": left["references"][0]["law_text"]},
            {"locator": "VII.3", "law_text": right["references"][0]["law_text"]},
        ]
        blocked = self.preview_consolidation(
            self.copy,
            ["CRA-ANNEX-VII-RISK", "FIXTURE-VII-1A"],
            "CRA-ANNEX-VII-RISK",
            {},
            references,
        )
        self.assertEqual(_bytes(self.copy), before)
        self.assertIn("note", blocked["conflicts"])
        chosen = self.preview_consolidation(
            self.copy,
            ["CRA-ANNEX-VII-RISK", "FIXTURE-VII-1A"],
            "CRA-ANNEX-VII-RISK",
            {"note": "Keep the first note."},
            references,
        )
        self.assertEqual(chosen["conflicts"], [])
        self.assertEqual([item["nr"] for item in chosen["requirement"]["references"]], [1, 2])
        self.assertEqual(chosen["requirement"]["note"], "Keep the first note.")
        self.assertNotIn("signed", chosen["requirement"])
        self.assertEqual(_bytes(self.copy), before)


class ApplyConsolidationTest(unittest.TestCase):
    def setUp(self):
        from requirements.consolidate import apply_consolidation

        self.apply_consolidation = apply_consolidation
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.base = extract_annex_vii_risk()
        self.copy = create_extraction_copy(
            self.root, "cra-baseline", draft_pack(), at="2026-10-13T090000Z"
        )
        self.private, self.public = generate_keypair()

    def _pair(self, *, sign_second: bool = False):
        other = copy.deepcopy(self.base)
        other.pop("signed", None)
        other["id"] = "FIXTURE-VII-1A"
        other["references"] = [
            {"nr": 1, "locator": "VII.1(a)", "law_text": "a statement of the intended purpose"}
        ]
        left = apply_edits(self.base, {"note": "Keep the first note."})
        right = apply_edits(other, {"note": "Keep the first note."})
        if sign_second:
            source = dict(right["source"])
            source["edition"] = "2024-11-20"
            right = apply_edits(right, {"source": source})
            right = publish_requirement(
                right, name="Ada Jurist", private_key=self.private, at="2026-10-12T09:00:00Z"
            )
        save_requirement(self.copy, left, published=False)
        save_requirement(self.copy, right, published=sign_second)
        return left, right

    def _references(self, left: dict, right: dict) -> list[dict]:
        return [
            {"locator": "VII.3", "law_text": left["references"][0]["law_text"]},
            {"locator": "VII.1(a)", "law_text": right["references"][0]["law_text"]},
        ]

    def test_merge_removes_the_unsigned_sibling_and_publishes_without_it(self):
        left, right = self._pair()
        merged = self.apply_consolidation(
            self.copy,
            ["CRA-ANNEX-VII-RISK", "FIXTURE-VII-1A"],
            "CRA-ANNEX-VII-RISK",
            {"note": "Keep the first note."},
            self._references(left, right),
            digests={
                "CRA-ANNEX-VII-RISK": version_digest(left),
                "FIXTURE-VII-1A": version_digest(right),
            },
        )
        self.assertNotIn("signed", merged)
        self.assertEqual([item["nr"] for item in merged["references"]], [1, 2])
        self.assertFalse((self.copy / "FIXTURE-VII-1A.json").exists())
        saved = load_requirement(self.copy / "CRA-ANNEX-VII-RISK.json")
        self.assertEqual(saved["references"][1]["law_text"], "a statement of the intended purpose")
        source = dict(saved["source"])
        source["edition"] = "2024-11-20"
        signed = publish_requirement(
            apply_edits(saved, {"source": source, "remediation_hint": "Published after the merge."}),
            name="Ada Jurist",
            private_key=self.private,
            at="2026-10-12T09:00:00Z",
        )
        save_requirement(self.copy, signed, published=True)
        seal_pack_directory(self.copy, name="Ada Jurist", private_key=self.private, at="2026-10-12T10:00:00Z")
        released = publish_pack(
            self.root,
            self.copy,
            version="0.1.0",
            trust={"Ada Jurist": self.public},
        )
        names = [path.name for path in released.iterdir()]
        self.assertIn("CRA-ANNEX-VII-RISK.json", names)
        self.assertNotIn("FIXTURE-VII-1A.json", names)

    def test_conflict_and_signed_and_stale_digest_do_not_delete(self):
        left, right = self._pair()
        right = apply_edits(right, {"note": "A different note."})
        save_requirement(self.copy, right)
        before = _bytes(self.copy)
        with self.assertRaises(ModelError):
            self.apply_consolidation(
                self.copy,
                ["CRA-ANNEX-VII-RISK", "FIXTURE-VII-1A"],
                "CRA-ANNEX-VII-RISK",
                {},
                self._references(left, right),
                digests={
                    "CRA-ANNEX-VII-RISK": version_digest(left),
                    "FIXTURE-VII-1A": version_digest(right),
                },
            )
        self.assertEqual(_bytes(self.copy), before)

        signed_left, signed_right = self._pair_in("2026-10-13T143000Z", sign_second=True)
        signed_before = _bytes(self._dir("2026-10-13T143000Z"))
        with self.assertRaises(ModelError):
            self.apply_consolidation(
                self._dir("2026-10-13T143000Z"),
                ["CRA-ANNEX-VII-RISK", "FIXTURE-VII-1A"],
                "CRA-ANNEX-VII-RISK",
                {"note": signed_left.get("note")},
                self._references(signed_left, signed_right),
                digests={
                    "CRA-ANNEX-VII-RISK": version_digest(signed_left),
                    "FIXTURE-VII-1A": version_digest(signed_right),
                },
            )
        self.assertTrue((self._dir("2026-10-13T143000Z") / "FIXTURE-VII-1A.json").exists())
        self.assertIn("signed", load_requirement(self._dir("2026-10-13T143000Z") / "FIXTURE-VII-1A.json"))
        self.assertEqual(_bytes(self._dir("2026-10-13T143000Z")), signed_before)

        stale_left, stale_right = self._pair_in("2026-10-13T150000Z")
        directory = self._dir("2026-10-13T150000Z")
        stale = version_digest(stale_right)
        changed = apply_edits(stale_right, {"note": "changed after the digest was read"})
        save_requirement(directory, changed)
        snapshot = _bytes(directory)
        with self.assertRaises(ModelError):
            self.apply_consolidation(
                directory,
                ["CRA-ANNEX-VII-RISK", "FIXTURE-VII-1A"],
                "CRA-ANNEX-VII-RISK",
                {"note": "Keep the first note."},
                self._references(stale_left, stale_right),
                digests={
                    "CRA-ANNEX-VII-RISK": version_digest(stale_left),
                    "FIXTURE-VII-1A": stale,
                },
            )
        self.assertEqual(_bytes(directory), snapshot)

    def _dir(self, stamp: str) -> Path:
        return self.root / "cra-baseline" / stamp

    def _pair_in(self, stamp: str, *, sign_second: bool = False):
        self.copy = create_extraction_copy(self.root, "cra-baseline", draft_pack(), at=stamp)
        return self._pair(sign_second=sign_second)
