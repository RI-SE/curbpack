"""M3: several claims can point at one requirement and survive a rebind."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checks.run import run_claim
from claims.bind import build_claim, read_claims, rebind, retire_claim, write_claim
from common.canonical import version_digest
from common.errors import CheckError, ModelError
from common.signing import generate_keypair, sign_object
from common.validate import validate_claim
from requirements.extract.pipeline import extract_annex_vii_risk


def _claim(claim_id: str, requirement_id: str, path: str, checks: list[dict]) -> dict:
    return build_claim(
        claim_id=claim_id,
        requirement_id=requirement_id,
        source="documents",
        args={"path": path},
        checks=checks,
        description="The reviewed file is the evidence for this Requirement.",
        severity="high",
    )


class ClaimsTest(unittest.TestCase):
    def test_two_claims_round_trip_and_rebind_leaves_the_requirement(self):
        requirement = extract_annex_vii_risk()
        before = version_digest(requirement)
        risk_path = "docs/annex-vii/risk_assessment.md"
        risk = _claim(
            "claim-risk",
            requirement["id"],
            risk_path,
            [
                {"check": "exist", "args": {"paths": [risk_path]}},
                {
                    "check": "contents",
                    "args": {
                        "path": risk_path,
                        "probes": [
                            {"kind": "size", "bytes": 200, "op": ">="},
                            {"kind": "headers", "headers": ["# Risk Assessment"]},
                            {"kind": "token"},
                        ],
                    },
                },
            ],
        )
        readme = _claim(
            "claim-readme",
            requirement["id"],
            "README.md",
            [{"check": "exist", "args": {"paths": ["README.md"]}}],
        )
        private, public = generate_keypair()
        sealed = sign_object(risk, name="QA", private_key=private, at="2026-10-12T12:00:00Z")
        moved_path = "docs/security/risk_assessment.md"
        moved = rebind(
            sealed,
            args={"path": moved_path},
            checks=[
                {"check": "exist", "args": {"paths": [moved_path]}},
                {
                    "check": "contents",
                    "args": {
                        "path": moved_path,
                        "probes": risk["checks"][1]["args"]["probes"],
                    },
                },
            ],
        )
        self.assertNotIn("signed", moved)
        self.assertEqual(moved["args"]["path"], moved_path)
        self.assertEqual(moved["checks"][0]["args"]["paths"], [moved_path])
        self.assertEqual(version_digest(requirement), before)
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_claim(directory, risk)
            write_claim(directory, readme)
            write_claim(directory, moved)
            loaded = {claim["id"]: claim for claim in read_claims(directory)}
            self.assertEqual(loaded["claim-risk"], moved)
            self.assertEqual(loaded["claim-readme"]["requirement_id"], requirement["id"])
            retire_claim(directory, "claim-readme")
            self.assertEqual([claim["id"] for claim in read_claims(directory)], ["claim-risk"])
        self.assertTrue(public)

    def test_unchecked_claim_reloads_and_is_not_a_pass(self):
        claim = build_claim(
            claim_id="claim-proposal",
            requirement_id="CRA-ANNEX-VII-RISK",
            source="documents",
            args={"path": "docs/annex-vii/risk_assessment.md"},
            checks=[],
            description="A saved proposal with nothing to execute.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_claim(directory, claim)
            self.assertEqual(read_claims(directory), [claim])
            from checks.run import build_run_result, process_exit_code

            result = build_run_result(directory, [claim], [{"id": "cra-baseline", "version": "0.1.0", "digest": "abc"}])
        self.assertEqual(result["claims"], [])
        self.assertEqual(process_exit_code(result), 1)

    def test_unknown_check_is_rejected_and_unimplemented_does_not_pass(self):
        with self.assertRaises(CheckError):
            _claim("claim-nope", "CRA-ANNEX-VII-RISK", "docs/a.md", [{"check": "nope", "args": {}}])
        fresh = _claim(
            "claim-fresh",
            "CRA-ANNEX-VII-RISK",
            "docs/annex-vii/risk_assessment.md",
            [{"check": "fresh", "args": {"path": "docs/annex-vii/risk_assessment.md", "max_age_days": 90}}],
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = run_claim(Path(tmp), fresh)
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["checks"][0]["status"], "fail")
        self.assertIn("not implemented", result["checks"][0]["detail"])

    def test_top_level_check_is_not_a_claim(self):
        with self.assertRaises(ModelError):
            validate_claim(
                {
                    "id": "old",
                    "requirement_id": "CRA-ANNEX-VII-RISK",
                    "check": "exist",
                    "args": {"paths": ["docs/a.md"]},
                    "description": "old shape",
                }
            )

    def test_stored_single_check_file_is_rewritten_as_checks(self):
        from common.jsonio import read_json, write_json
        from common.store import load_claim

        legacy = {
            "id": "CRA-ANNEX-VII-DESCRIPTION-SOFTWARE-VERSIONS-CHANGELOG.md-contents",
            "requirement_id": "CRA-ANNEX-VII-DESCRIPTION-SOFTWARE-VERSIONS",
            "check": "contents",
            "args": {
                "path": "CHANGELOG.md",
                "probes": [{"kind": "words", "n": 20, "op": ">="}],
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f"{legacy['id']}.json"
            write_json(path, legacy)
            loaded = load_claim(path)
            stored = read_json(path)
        self.assertEqual(loaded["args"], {"path": "CHANGELOG.md"})
        self.assertEqual(loaded["checks"][0]["check"], "contents")
        self.assertEqual(loaded["checks"][0]["args"]["probes"][0]["kind"], "words")
        self.assertNotIn("check", stored)
        self.assertEqual(stored["source"], "documents")


if __name__ == "__main__":
    unittest.main()
