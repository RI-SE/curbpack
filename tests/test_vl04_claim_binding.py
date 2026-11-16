"""VL-04: a Claim records the Requirement version it was assessed against."""

from __future__ import annotations

import unittest

from common.canonical import version_digest
from common.validate import validate_claim
from requirements.extract.pipeline import extract_annex_vii_risk


def _claim(requirement: dict) -> dict:
    return {
        "id": "claim-annex-vii-risk",
        "requirement_id": requirement["id"],
        "source": "documents",
        "args": {"path": "docs/annex-vii/risk_assessment.md"},
        "description": "The reviewed file is the evidence for this Requirement.",
        "checks": [],
    }


class ClaimBindingFieldsTest(unittest.TestCase):
    def test_binding_fields_are_accepted_and_still_optional(self):
        requirement = extract_annex_vii_risk()
        plain = validate_claim(_claim(requirement))
        self.assertNotIn("namespace", plain)
        self.assertNotIn("pack_id", plain)
        self.assertNotIn("requirement_digest", plain)

        bound = _claim(requirement)
        bound["namespace"] = requirement["namespace"]
        bound["pack_id"] = requirement["pack_id"]
        bound["requirement_digest"] = version_digest(requirement)
        accepted = validate_claim(bound)
        self.assertEqual(accepted["namespace"], requirement["namespace"])
        self.assertEqual(accepted["pack_id"], requirement["pack_id"])
        self.assertEqual(accepted["requirement_digest"], version_digest(requirement))
