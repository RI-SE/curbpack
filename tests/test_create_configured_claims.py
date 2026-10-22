"""Create writes one Claim for the evidence and does not overwrite an existing file."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checks.run import run_claim
from claims.bind import (
    build_claim,
    create_configured_claims,
    read_claim_seal,
    sign_claim,
    suggest_claim_id,
    write_claim,
)
from common.jsonio import read_json
from common.signing import generate_keypair


def _checks(path: str) -> list[dict]:
    return [
        {"check": "exist", "args": {"paths": [path]}},
        {"check": "contents", "args": {"path": path, "probes": [{"kind": "pattern", "pattern": "SECRET"}]}},
    ]


class CreateConfiguredClaimsTest(unittest.TestCase):
    def test_two_checks_create_one_claim_and_a_repeat_is_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "docs").mkdir()
            (repo / "docs" / "a.md").write_text("risk\n", encoding="utf-8")
            claims = repo / "claims"
            outcomes = create_configured_claims(
                claims,
                requirement_id="REQ-A",
                known_ids=["REQ-A", "REQ-B"],
                source="documents",
                args={"path": "docs/a.md"},
                checks=_checks("docs/a.md"),
                description="docs/a.md is the reviewed evidence.",
            )
            self.assertEqual([item["outcome"] for item in outcomes], ["created"])
            claim_id = suggest_claim_id("REQ-A", "docs/a.md")
            claim = read_json(claims / f"{claim_id}.json")
            self.assertEqual(claim["requirement_id"], "REQ-A")
            self.assertEqual(claim["source"], "documents")
            self.assertEqual(claim["args"], {"path": "docs/a.md"})
            self.assertEqual([item["check"] for item in claim["checks"]], ["exist", "contents"])
            self.assertNotIn("signed", claim)
            self.assertEqual(len(list(claims.glob("*.json"))), 1)
            before = (claims / f"{claim_id}.json").read_bytes()
            again = create_configured_claims(
                claims,
                requirement_id="REQ-A",
                known_ids=["REQ-A"],
                source="documents",
                args={"path": "docs/a.md"},
                checks=_checks("docs/a.md"),
                description="docs/a.md is the reviewed evidence.",
            )
            self.assertEqual([item["outcome"] for item in again], ["unchanged"])
            self.assertEqual((claims / f"{claim_id}.json").read_bytes(), before)
            result = run_claim(repo, claim)
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["checks"][0]["index"], 0)
            self.assertEqual(result["checks"][0]["status"], "pass")
            self.assertEqual(result["checks"][1]["status"], "pass")

    def test_existing_signed_claim_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            claims = Path(tmp)
            claim_id = suggest_claim_id("REQ-A", "docs/a.md")
            private, public = generate_keypair()
            existing = sign_claim(
                build_claim(
                    claim_id=claim_id,
                    requirement_id="REQ-A",
                    source="documents",
                    args={"path": "docs/other.md"},
                    checks=[{"check": "exist", "args": {"paths": ["docs/other.md"]}}],
                    description="An earlier binding.",
                ),
                name="QA",
                private_key=private,
                at="2026-10-14T08:00:00Z",
            )
            write_claim(claims, existing)
            before = (claims / f"{claim_id}.json").read_bytes()
            outcomes = create_configured_claims(
                claims,
                requirement_id="REQ-A",
                known_ids=["REQ-A"],
                source="documents",
                args={"path": "docs/a.md"},
                checks=_checks("docs/a.md"),
                description="docs/a.md is the reviewed evidence.",
            )
            self.assertEqual(outcomes[0]["outcome"], "blocked")
            self.assertTrue(outcomes[0]["signed"])
            self.assertEqual((claims / f"{claim_id}.json").read_bytes(), before)
            self.assertEqual(len(list(claims.glob("*.json"))), 1)
            reading = read_claim_seal(read_json(claims / f"{claim_id}.json"), {"QA": public})
            self.assertTrue(reading["verifiable"])

    def test_invalid_check_blocks_the_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            claims = Path(tmp)
            outcomes = create_configured_claims(
                claims,
                requirement_id="REQ-A",
                known_ids=["REQ-A"],
                source="documents",
                args={"path": "docs/a.md"},
                checks=[{"check": "contents", "args": {"path": "docs/a.md", "probes": [{"kind": "pattern", "pattern": ""}]}}],
                description="docs/a.md is the reviewed evidence.",
            )
            self.assertEqual(outcomes[0]["outcome"], "blocked")
            self.assertFalse(claims.exists() and any(claims.glob("*.json")))


if __name__ == "__main__":
    unittest.main()
