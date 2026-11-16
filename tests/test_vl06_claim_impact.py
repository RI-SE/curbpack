"""VL-06: a changed Requirement shows the Claims bound to its previous digest."""

from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from claims.bind import build_claim
from claims.impact import claims_affected_by_requirement
from common.canonical import version_digest
from requirements.editing import apply_edits
from requirements.extract.pipeline import extract_annex_vii_risk


class AffectedClaimsTest(unittest.TestCase):
    def test_a_changed_requirement_lists_the_claim_bound_to_the_previous_digest(self):
        """VL-06 VL06-01. The Requirement change is reported and the Claim is not modified."""
        requirement = extract_annex_vii_risk()
        claim = build_claim(
            claim_id="claim-bound",
            requirement=requirement,
            source="documents",
            args={"path": "docs/present.md"},
            checks=[{"check": "exist", "args": {"paths": ["docs/present.md"]}}],
            description="The file is the evidence for this Requirement.",
        )
        other = build_claim(
            claim_id="claim-other",
            requirement=apply_edits(requirement, {"note": "An older note."}),
            source="documents",
            args={"path": "docs/other.md"},
            checks=[],
            description="This Claim was bound to an older payload.",
        )
        changed = apply_edits(requirement, {"note": "The note changed."})
        before = copy.deepcopy(claim)
        found = claims_affected_by_requirement([claim, other], requirement, changed)
        self.assertEqual([item["id"] for item in found], ["claim-bound"])
        self.assertEqual(found[0]["recorded"]["namespace"], requirement["namespace"])
        self.assertEqual(found[0]["recorded"]["pack_id"], requirement["pack_id"])
        self.assertEqual(found[0]["recorded"]["requirement_id"], requirement["id"])
        self.assertEqual(found[0]["recorded"]["requirement_digest"], version_digest(requirement))
        self.assertEqual(found[0]["current"]["namespace"], changed["namespace"])
        self.assertEqual(found[0]["current"]["pack_id"], changed["pack_id"])
        self.assertEqual(found[0]["current"]["requirement_id"], changed["id"])
        self.assertEqual(found[0]["current"]["digest"], version_digest(changed))
        self.assertEqual(claim, before)

    def test_an_unchanged_digest_reports_no_newly_stale_claim(self):
        """VL-06 VL06-02. A save that keeps the payload digest adds no stale Claim."""
        requirement = extract_annex_vii_risk()
        claim = build_claim(
            claim_id="claim-bound",
            requirement=requirement,
            source="documents",
            args={"path": "docs/present.md"},
            checks=[],
            description="The file is the evidence for this Requirement.",
        )
        self.assertEqual(claims_affected_by_requirement([claim], requirement, requirement), [])

    def test_a_run_result_and_a_review_report_stay_unchanged(self):
        """VL-06 VL06-07. Listing affected Claims does not rewrite historical records."""
        requirement = extract_annex_vii_risk()
        claim = build_claim(
            claim_id="claim-bound",
            requirement=requirement,
            source="documents",
            args={"path": "docs/present.md"},
            checks=[],
            description="The file is the evidence for this Requirement.",
        )
        changed = apply_edits(requirement, {"note": "The note changed."})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_result = root / "run-result.json"
            report = root / "review-report.json"
            run_result.write_text('{"claims":[]}\n', encoding="utf-8")
            report.write_text('{"decision":"recorded"}\n', encoding="utf-8")
            run_bytes = run_result.read_bytes()
            report_bytes = report.read_bytes()
            claims_affected_by_requirement([claim], requirement, changed)
            self.assertEqual(run_result.read_bytes(), run_bytes)
            self.assertEqual(report.read_bytes(), report_bytes)
