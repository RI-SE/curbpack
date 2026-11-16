"""VL-05: Review locates the Requirement and Claim a Run Result recorded."""

from __future__ import annotations

import subprocess
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


class HistoricalRequirementTest(unittest.TestCase):
    def test_a_changed_requirement_is_recovered_from_the_commit_that_matches(self):
        """VL-05 GWT-02, GWT-04, and GWT-05. The current file is not substituted for a missing digest."""
        requirement = extract_annex_vii_risk()
        requirement["note"] = "historical note"
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
            _git(root, "init")
            _git(root, "add", "curbpack.json", "curbpack")
            _git(root, "commit", "-m", "record the requirement")
            recorded_commit = _git(root, "rev-parse", "HEAD").strip()
            recorded = version_digest(stored)
            pack_dir = root / "curbpack" / "packs" / stored["pack_id"] / "0.1.0"
            changed = load_requirement(pack_dir / f"{stored['id']}.json")
            changed["note"] = "current note"
            save_requirement(pack_dir, changed)
            _git(root, "add", "curbpack")
            _git(root, "commit", "-m", "change the requirement")
            requirement_path = root / "curbpack" / "packs" / stored["pack_id"] / "0.1.0" / f"{stored['id']}.json"
            before = requirement_path.read_bytes()
            status_before = _git(root, "status", "--porcelain")
            row = _row(stored, claim, recorded)
            missing = dict(row, id="claim-missing-digest", requirement_digest="missing-digest")
            chain = resolve_chain(root, {"claims": [row, missing]})
            found = chain["claims"][0]
            absent = chain["claims"][1]
            self.assertEqual(found["requirement"]["location"], "historical")
            self.assertEqual(found["requirement"]["commit"], recorded_commit)
            self.assertEqual(version_digest(found["requirement"]["object"]), recorded)
            self.assertEqual(found["requirement"]["object"]["note"], "historical note")
            self.assertEqual(found["claim"]["location"], "current")
            self.assertEqual(found["claim"]["object"]["requirement_digest"], recorded)
            self.assertEqual(
                found["checks"],
                [{"index": 0, "check": "exist", "args": {"paths": ["docs/present.md"]}, "corresponds": True}],
            )
            self.assertEqual(absent["requirement"]["location"], "unresolved")
            self.assertIsNone(absent["requirement"]["object"])
            self.assertNotEqual(version_digest(changed), recorded)
            self.assertEqual(requirement_path.read_bytes(), before)
            self.assertEqual(_git(root, "status", "--porcelain"), status_before)

    def test_a_directory_without_git_still_resolves_the_current_object(self):
        """History is unavailable. A current digest match is still reported."""
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
            missing = _row(stored, claim, "missing-digest")
            chain = resolve_chain(root, {"claims": [_row(stored, claim, recorded), missing]})
            self.assertEqual(chain["claims"][0]["requirement"]["location"], "current")
            self.assertEqual(chain["claims"][1]["requirement"]["location"], "unresolved")
            self.assertEqual(chain["claims"][1]["requirement"]["history"], "unavailable")
            self.assertIsNone(chain["claims"][1]["requirement"]["object"])


class HistoricalClaimTest(unittest.TestCase):
    def test_a_changed_claim_is_recovered_and_a_missing_requirement_stays_separate(self):
        """VL-05 GWT-03 and GWT-08. One unresolved Requirement does not drop the Claim that resolves."""
        requirement = extract_annex_vii_risk()
        evidence = [{"check": "exist", "args": {"paths": ["docs/present.md"]}}]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            claim = build_claim(
                claim_id="claim-edited",
                requirement=requirement,
                source="documents",
                args={"path": "docs/present.md"},
                checks=evidence,
                description="The file is the evidence for this Requirement.",
            )
            kept = build_claim(
                claim_id="claim-kept",
                requirement=requirement,
                source="documents",
                args={"path": "docs/present.md"},
                checks=evidence,
                description="This Claim stays current.",
            )
            stored = _repo(root, requirement, claim)
            for item in (claim, kept):
                item["requirement_digest"] = version_digest(stored)
                write_claim(root / "curbpack" / "claims", item)
            _git(root, "init")
            _git(root, "add", "curbpack.json", "curbpack")
            _git(root, "commit", "-m", "record the claims")
            recorded_commit = _git(root, "rev-parse", "HEAD").strip()
            recorded_claim = version_digest(claim)
            claim["description"] = "The description changed after the run."
            write_claim(root / "curbpack" / "claims", claim)
            _git(root, "add", "curbpack")
            _git(root, "commit", "-m", "change the claim")
            claim_path = root / "curbpack" / "claims" / "claim-edited.json"
            historical = _row(stored, claim, version_digest(stored))
            historical["digest"] = recorded_claim
            kept_row = _row(stored, kept, "missing-digest")
            bare = {
                "id": "claim-edited",
                "digest": recorded_claim,
                "status": "pass",
                "checks": historical["checks"],
            }
            result_path = root / "run-result.json"
            write_json(result_path, {"claims": [bare]})
            before = claim_path.read_bytes()
            result_before = result_path.read_bytes()
            status_before = _git(root, "status", "--porcelain")
            chain = resolve_chain(root, {"claims": [historical, kept_row, bare]})
            found, partial, old = chain["claims"]
            self.assertEqual(found["claim"]["location"], "historical")
            self.assertEqual(found["claim"]["commit"], recorded_commit)
            self.assertEqual(version_digest(found["claim"]["object"]), recorded_claim)
            self.assertEqual(found["claim"]["object"]["description"], "The file is the evidence for this Requirement.")
            self.assertEqual(
                found["checks"],
                [{"index": 0, "check": "exist", "args": {"paths": ["docs/present.md"]}, "corresponds": True}],
            )
            self.assertEqual(partial["requirement"]["location"], "unresolved")
            self.assertIsNone(partial["requirement"]["object"])
            self.assertEqual(partial["claim"]["location"], "current")
            self.assertEqual(partial["claim"]["object"]["id"], "claim-kept")
            self.assertEqual(old["requirement"]["location"], "unresolved")
            self.assertIsNone(old["requirement"]["object"])
            self.assertEqual(old["claim"]["location"], "historical")
            self.assertEqual(claim_path.read_bytes(), before)
            self.assertEqual(result_path.read_bytes(), result_before)
            self.assertEqual(_git(root, "status", "--porcelain"), status_before)


def _row(stored: dict, claim: dict, requirement_digest: str) -> dict:
    return {
        "id": claim["id"],
        "digest": version_digest(claim),
        "namespace": stored["namespace"],
        "pack_id": stored["pack_id"],
        "requirement_id": stored["id"],
        "requirement_digest": requirement_digest,
        "status": "pass",
        "checks": [
            {"index": 0, "check": "exist", "args": {"paths": ["docs/present.md"]}, "status": "pass"}
        ],
    }


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "-c", "user.email=review@example.com", "-c", "user.name=Review", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout
