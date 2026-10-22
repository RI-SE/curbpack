"""One Requirement, one Claim, several Checks, nested results, and a review appendix."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checks.run import build_run_result, process_exit_code
from claims.bind import build_claim, read_claims, rebind, sign_claim, write_claim
from common.canonical import version_digest
from common.signing import generate_keypair
from review.compile import compile_report


class ClaimWorkflowTest(unittest.TestCase):
    def test_one_claim_runs_both_checks_and_keeps_its_signature(self):
        private, public = generate_keypair()
        path = "docs/risk.md"
        proposal = build_claim(
            claim_id="claim-risk",
            requirement_id="REQ-A",
            source="documents",
            args={"path": path},
            checks=[],
            description="The reviewed risk note supports the Requirement.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "docs").mkdir()
            (repo / "docs" / "risk.md").write_text("no secrets here\n", encoding="utf-8")
            write_claim(repo / "claims", proposal)
            self.assertEqual(read_claims(repo / "claims")[0]["checks"], [])
            configured = rebind(
                proposal,
                checks=[
                    {"check": "exist", "args": {"paths": [path]}},
                    {"check": "contents", "args": {"path": path, "probes": [{"kind": "pattern", "pattern": "SECRET"}]}},
                ],
            )
            write_claim(repo / "claims", configured)
            packs = [{"id": "house", "version": "0.1.0", "digest": "abc"}]
            ran = build_run_result(repo, read_claims(repo / "claims"), packs)
            self.assertEqual(len(ran["claims"]), 1)
            row = ran["claims"][0]
            self.assertEqual(row["digest"], version_digest(configured))
            self.assertEqual(row["status"], "pass")
            self.assertEqual([item["index"] for item in row["checks"]], [0, 1])
            self.assertEqual(process_exit_code(ran), 0)
            sealed = sign_claim(configured, name="QA", private_key=private, at="2026-10-14T12:00:00Z")
            write_claim(repo / "claims", sealed)
            (repo / "docs" / "risk.md").write_text("SECRET\n", encoding="utf-8")
            failed = build_run_result(repo, read_claims(repo / "claims"), packs)
            failed_row = failed["claims"][0]
            self.assertEqual(failed_row["status"], "fail")
            self.assertEqual(failed_row["checks"][0]["status"], "pass")
            self.assertEqual(failed_row["checks"][1]["status"], "fail")
            self.assertIn("SECRET", failed_row["checks"][1]["detail"])
            self.assertEqual(failed_row["digest"], version_digest(sealed))
            self.assertEqual(process_exit_code(failed), 1)
            other = build_claim(
                claim_id="claim-other",
                requirement_id="REQ-B",
                source="git",
                args={"path": "README.md"},
                checks=[{"check": "exist", "args": {"paths": ["README.md"]}}],
                description="README.md is separate evidence.",
            )
            (repo / "README.md").write_text("readme\n", encoding="utf-8")
            write_claim(repo / "claims", other)
            mixed = build_run_result(repo, read_claims(repo / "claims"), packs)
            by_id = {row["id"]: row for row in mixed["claims"]}
            self.assertEqual(by_id["claim-risk"]["status"], "fail")
            self.assertEqual(by_id["claim-other"]["status"], "pass")
            report = compile_report(
                run_result=mixed,
                requirements=[_requirement("REQ-A"), _requirement("REQ-B")],
                claims=read_claims(repo / "claims"),
                trust={"QA": public},
            )
            self.assertEqual(report["appendix"], [
                {
                    "id": "claim-other",
                    "requirement_id": "REQ-B",
                    "reason": "No signed block and no signed Git commit. The object is unsigned.",
                }
            ])
            self.assertNotIn("appendix", report["run_result"])


def _requirement(requirement_id: str) -> dict:
    return {
        "id": requirement_id,
        "pack_id": "house",
        "source": {
            "framework": "test",
            "instrument": "fixture",
            "identifier": "FIX-1",
            "language": "en",
            "url": "https://example.test/law",
        },
        "references": [{"nr": 1, "locator": "1", "law_text": "The product documents the risk."}],
    }


if __name__ == "__main__":
    unittest.main()
