"""M1: Annex VII.3 travels from the annex text to a persisted Requirement."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from common.canonical import version_digest
from common.errors import ModelError
from common.signing import generate_keypair, read_signature
from common.store import load_pack_directory, load_requirement, save_pack, save_requirement
from common.validate import validate_requirement
from requirements.extract.atomize import atomize
from requirements.extract.pipeline import FIXTURE, draft_pack, extract_annex_vii_risk
from requirements.editing import (
    accept_published_version,
    apply_edits,
    approve_working_copy,
    publish_requirement,
    read_pack_seal,
    seal_pack_directory,
    working_copy,
)


class ExtractRequirementTest(unittest.TestCase):
    def test_annex_vii_point_3_is_an_unsigned_draft(self):
        requirement = extract_annex_vii_risk()
        self.assertEqual(requirement["id"], "CRA-ANNEX-VII-RISK")
        self.assertEqual(requirement["pack_id"], "cra-baseline")
        self.assertNotIn("signed", requirement)
        self.assertNotIn("origin", requirement)
        self.assertNotIn("strength", requirement)
        for forbidden in ("law_text", "search", "claim", "locus"):
            self.assertNotIn(forbidden, requirement)
        reference = requirement["references"][0]
        self.assertEqual(reference["nr"], 1)
        self.assertEqual(reference["locator"], "VII.3")
        self.assertIn("cybersecurity risks", reference["law_text"])
        self.assertNotIn("shall", reference["law_text"].lower())
        hints = requirement["discovery_hints"]
        self.assertIn("risk assessment", hints["concepts"])
        self.assertIn("*risk*assessment*", hints["path_hints"])
        self.assertIn("*THREAT*", hints["path_hints"])
        self.assertEqual(hints["sources"][0], {"source": "documents"})
        self.assertEqual(requirement["source"]["identifier"], "CELEX:32024R2847")
        self.assertEqual(requirement["source"]["language"], "en")
        self.assertNotIn("edition", requirement["source"])

    def test_atomizer_still_finds_every_mapped_locus(self):
        atoms = atomize(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(
            [item["locus"] for item in atoms],
            ["1(a)", "1(b)", "1(c)", "1(d)", "2(a)", "2(b)", "2(c)", "3", "4", "5", "6", "7", "8"],
        )

    def test_top_level_claim_is_rejected(self):
        requirement = extract_annex_vii_risk()
        requirement["claim"] = "vii-3-cybersecurity-risk-assessment"
        with self.assertRaises(ModelError) as caught:
            validate_requirement(requirement)
        self.assertIn("claim", str(caught.exception))


class EditAndPersistTest(unittest.TestCase):
    def test_edit_save_and_reload_keep_unrelated_fields(self):
        requirement = extract_annex_vii_risk()
        source = dict(requirement["source"])
        source["edition"] = "2024-11-20"
        edited = apply_edits(
            requirement,
            {
                "source": source,
                "remediation_hint": "Populate a product-specific risk assessment (no placeholders).",
                "note": "Kept across later edits.",
            },
        )
        edited = apply_edits(
            edited,
            {"remediation_hint": "The file should be the product's own assessment, not a placeholder."},
        )
        self.assertEqual(edited["note"], "Kept across later edits.")
        self.assertEqual(edited["source"]["edition"], "2024-11-20")
        self.assertNotIn("signed", edited)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save_pack(root, draft_pack())
            save_requirement(root, edited)
            pack, requirements = load_pack_directory(root)
            self.assertEqual(pack["version"], "0.1.0")
            self.assertEqual(requirements[0], edited)
            self.assertEqual(load_requirement(root / "CRA-ANNEX-VII-RISK.json"), edited)

    def test_publisher_signature_does_not_cover_a_working_copy(self):
        private, public = generate_keypair()
        trust = {"Ada Jurist": public}
        requirement = extract_annex_vii_risk()
        source = dict(requirement["source"])
        source["edition"] = "2024-11-20"
        draft = apply_edits(
            requirement,
            {
                "source": source,
                "remediation_hint": "The file should be the product's own assessment, not a placeholder.",
            },
        )
        published = publish_requirement(
            draft,
            name="Ada Jurist",
            private_key=private,
            at="2026-10-12T09:00:00Z",
        )
        reading = read_signature(published, trust, what="requirement")
        self.assertTrue(reading["verifiable"])
        self.assertEqual(reading["who"], "Ada Jurist")
        self.assertEqual(reading["when"], "2026-10-12T09:00:00Z")
        self.assertEqual(reading["version"], version_digest(published))
        self.assertNotIn("origin", published)

        copy = working_copy(published, draft_pack())
        self.assertEqual(copy["origin"], {"pack": "cra-baseline", "version": "0.1.0"})
        self.assertNotIn("signed", copy)
        unsigned = read_signature(copy, trust, what="requirement")
        self.assertFalse(unsigned["verifiable"])
        self.assertIn("unsigned", unsigned["reason"])

        approved = approve_working_copy(
            copy,
            name="Ada Jurist",
            private_key=private,
            at="2026-10-15T09:00:00Z",
        )
        local = read_signature(approved, trust, what="requirement")
        self.assertTrue(local["verifiable"])
        self.assertNotEqual(local["version"], reading["version"])

    def test_missing_key_is_not_reported_as_verified(self):
        private, _public = generate_keypair()
        published = publish_requirement(
            _with_edition(extract_annex_vii_risk()),
            name="Ada Jurist",
            private_key=private,
            at="2026-10-12T09:00:00Z",
        )
        reading = read_signature(published, {}, what="requirement")
        self.assertFalse(reading["verifiable"])
        self.assertIn("not available", reading["reason"])

    def test_changed_hint_is_a_new_payload_and_needs_acceptance(self):
        private, public = generate_keypair()
        trust = {"Ada Jurist": public}
        first = publish_requirement(
            _with_edition(extract_annex_vii_risk()),
            name="Ada Jurist",
            private_key=private,
            at="2026-10-12T09:00:00Z",
        )
        local = approve_working_copy(
            working_copy(first, draft_pack()),
            name="Kalle",
            private_key=private,
            at="2026-10-15T09:00:00Z",
        )
        hints = copy_hints(first)
        hints["path_hints"] = list(hints["path_hints"]) + ["*cybersecurity*risk*"]
        later_pack = draft_pack()
        later_pack["version"] = "0.2.0"
        later = apply_edits(first, {"discovery_hints": hints, "remediation_hint": "Updated advice."})
        later = publish_requirement(later, name="Ada Jurist", private_key=private, at="2026-12-01T08:00:00Z")
        self.assertEqual(local["origin"]["version"], "0.1.0")
        self.assertNotEqual(version_digest(later), version_digest(first))
        taken = accept_published_version(later, later_pack)
        self.assertEqual(taken["origin"]["version"], "0.2.0")
        self.assertNotIn("signed", taken)
        self.assertFalse(read_signature(taken, trust, what="requirement")["verifiable"])

    def test_pack_directory_seal_breaks_when_a_file_changes(self):
        private, public = generate_keypair()
        trust = {"Pack Sealer": public}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save_pack(root, draft_pack())
            save_requirement(root, _with_edition(extract_annex_vii_risk()))
            seal_pack_directory(root, name="Pack Sealer", private_key=private, at="2026-10-12T10:00:00Z")
            sealed = read_pack_seal(root, trust)
            self.assertTrue(sealed["verifiable"])
            self.assertEqual(sealed["what"], "pack directory")
            path = root / "CRA-ANNEX-VII-RISK.json"
            path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            broken = read_pack_seal(root, trust)
            self.assertFalse(broken["verifiable"])


def _with_edition(requirement: dict) -> dict:
    source = dict(requirement["source"])
    source["edition"] = "2024-11-20"
    return apply_edits(
        requirement,
        {
            "source": source,
            "remediation_hint": "The file should be the product's own assessment, not a placeholder.",
        },
    )


def copy_hints(requirement: dict) -> dict:
    return {
        key: list(value) if isinstance(value, list) else value
        for key, value in requirement["discovery_hints"].items()
    }


if __name__ == "__main__":
    unittest.main()
