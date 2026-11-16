"""VL-05: Review locates the Requirement and Claim a Run Result recorded."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from claims.bind import build_claim, write_claim
from common.canonical import version_digest
from common.jsonio import write_json
from common.store import load_requirement, save_pack, save_requirement
from requirements.extract.pipeline import draft_pack, extract_annex_vii_risk
from studio.review.resolve import resolve_chain


def _repo(root: Path, requirement: dict, claim: dict) -> dict:
    pack = draft_pack()
    pack["id"] = requirement["pack_id"]
    pack["namespace"] = requirement["namespace"]
    pack_dir = root / "curbpack" / "packs" / pack["id"] / pack["version"]
    save_pack(pack_dir, pack)
    save_requirement(pack_dir, requirement)
    stored = load_requirement(pack_dir / f"{requirement['id']}.json")
    write_claim(root / "curbpack" / "claims", claim)
    write_json(
        root / "curbpack.json",
        {
            "packs": [pack["id"]],
            "packs_dir": "curbpack/packs",
            "claims_dir": "curbpack/claims",
            "results_dir": "curbpack/results",
            "reports_dir": "curbpack/reports",
            "namespace_base": "RISE",
            "search_hints": {},
        },
    )
    return stored


class CurrentChainTest(unittest.TestCase):
    def test_a_current_requirement_and_claim_match_the_recorded_digests(self):
        """VL-05 GWT-01 and GWT-04. The current objects are reported when the digests match."""
        requirement = extract_annex_vii_risk()
        evidence = [{"check": "exist", "args": {"paths": ["docs/present.md"]}}]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            claim = build_claim(
                claim_id="claim-current",
                requirement=requirement,
                source="documents",
                args={"path": "docs/present.md"},
                checks=evidence,
                description="The file is the evidence for this Requirement.",
            )
            stored = _repo(root, requirement, claim)
            claim["requirement_digest"] = version_digest(stored)
            write_claim(root / "curbpack" / "claims", claim)
            recorded = version_digest(stored)
            row = {
                "id": claim["id"],
                "digest": version_digest(claim),
                "namespace": stored["namespace"],
                "pack_id": stored["pack_id"],
                "requirement_id": stored["id"],
                "requirement_digest": recorded,
                "binding": "match",
                "actual_digest": recorded,
                "status": "pass",
                "checks": [
                    {"index": 0, "check": "exist", "args": {"paths": ["docs/present.md"]}, "status": "pass"}
                ],
            }
            chain = resolve_chain(root, {"claims": [row]})
            item = chain["claims"][0]
            self.assertEqual(item["requirement"]["location"], "current")
            self.assertEqual(item["requirement"]["digest"], recorded)
            self.assertEqual(version_digest(item["requirement"]["object"]), recorded)
            self.assertEqual(item["claim"]["location"], "current")
            self.assertEqual(item["claim"]["digest"], version_digest(claim))
            self.assertEqual(item["claim"]["object"]["namespace"], stored["namespace"])
            self.assertEqual(item["claim"]["object"]["pack_id"], stored["pack_id"])
            self.assertEqual(item["claim"]["object"]["requirement_id"], stored["id"])
            self.assertEqual(item["claim"]["object"]["requirement_digest"], recorded)
            self.assertEqual(
                item["checks"],
                [{"index": 0, "check": "exist", "args": {"paths": ["docs/present.md"]}, "corresponds": True}],
            )
