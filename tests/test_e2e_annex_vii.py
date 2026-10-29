"""End-to-end Annex VII.3 acceptance criteria, without the UI."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from checks.run import process_exit_code, run_and_write
from claims.bind import build_claim, rebind, write_claim
from common.canonical import version_digest
from common.jsonio import write_json
from common.signing import generate_keypair, read_signature
from common.store import load_claim, load_requirement, save_pack, save_requirement
from discovery.door import created_curbpack
from discovery.search import discover_candidates
from requirements.extract.pipeline import draft_pack, extract_annex_vii_risk
from requirements.editing import apply_edits, publish_requirement, seal_pack_directory, working_copy
from review.compile import compile_report, read_report_signature, record_decision, sign_report, worktree_sentence
from review.gitseal import read_claim_signature
from scaffold.stub import is_stub, write_stub


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _commit(repo: Path, message: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=poc2@example.com", "-c", "user.name=PoC2", "commit", "-m", message)


def _good(repo: Path, header: str = "## Identified Risks") -> str:
    text = f"""# Risk Assessment

## Product Overview

{repo.name} is a product with digital elements. This file records the assessment for that product.

{header}

Unauthenticated access and a bad update are the risks considered for {repo.name}. Mitigations are local authentication and signed updates.
"""
    while len(text.encode("utf-8")) < 220:
        text += f"Further notes for {repo.name}.\n"
    return text


class AnnexViiScenarioTest(unittest.TestCase):
    def test_requirement_to_review_uses_the_same_objects(self):
        jurist_private, jurist_public = generate_keypair()
        reviewer_private, reviewer_public = generate_keypair()
        trust = {"Ada Jurist": jurist_public, "External Reviewer": reviewer_public}

        requirement = extract_annex_vii_risk()
        source = dict(requirement["source"])
        source["edition"] = "2024-11-20"
        requirement = apply_edits(
            requirement,
            {
                "source": source,
                "remediation_hint": "The file should be the product's own assessment, not a placeholder.",
                "discovery_hints": {
                    "concepts": ["risk assessment", "cybersecurity risk"],
                    "path_hints": ["*risk*assessment*", "*THREAT*"],
                    "sources": [{"source": "documents"}, {"source": "git"}],
                    "expected_evidence": ["process description"],
                },
            },
        )
        published = publish_requirement(
            requirement,
            name="Ada Jurist",
            private_key=jurist_private,
            at="2026-10-12T09:00:00Z",
        )
        self.assertTrue(read_signature(published, trust, what="requirement")["verifiable"])
        published_digest = version_digest(published)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = draft_pack()
            pack_dir = root / "packs" / "cra-baseline"
            repo = root / "sample-product"
            repo.mkdir()
            save_pack(pack_dir, pack)
            save_requirement(pack_dir, published)
            seal_pack_directory(pack_dir, name="Ada Jurist", private_key=jurist_private, at="2026-10-12T09:30:00Z")
            reloaded = load_requirement(pack_dir / "CRA-ANNEX-VII-RISK.json", published=True)
            self.assertEqual(reloaded, published)
            version_dir = repo / "curbpack" / "packs" / "cra-baseline" / pack["version"]
            shutil.copytree(pack_dir, version_dir)
            hints = created_curbpack()["search_hints"]
            hints["exclude_path_globs"] = ["**/node_modules/**", "*FUTURE_*"]
            hints["prefer_path_globs"] = ["**/README*", "**/docs/**"]
            write_json(
                repo / "curbpack.json",
                created_curbpack(packs=["cra-baseline"], search_hints=hints),
            )
            (repo / "README.md").write_text("sample-product readme\n", encoding="utf-8")
            (repo / "marketing.md").write_text("A cybersecurity risk is mentioned here.\n", encoding="utf-8")
            (repo / "docs").mkdir()
            (repo / "docs" / "threat-model-draft.md").write_text("draft\n", encoding="utf-8")
            (repo / "FUTURE_plan.md").write_text("risk assessment later\n", encoding="utf-8")
            config = json.loads((repo / "curbpack.json").read_text(encoding="utf-8"))
            candidates = discover_candidates(repo, reloaded, config)
            candidate_paths = [item["path"] for item in candidates]
            self.assertIn("docs/threat-model-draft.md", candidate_paths)
            self.assertIn("marketing.md", candidate_paths)
            self.assertNotIn("FUTURE_plan.md", candidate_paths)
            self.assertFalse((repo / "curbpack" / "claims").exists())

            stub = write_stub(repo, "docs/annex-vii/risk_assessment.md")
            self.assertTrue(is_stub(stub))
            risk_path = "docs/annex-vii/risk_assessment.md"
            probes = [
                {"kind": "size", "bytes": 200, "op": ">="},
                {
                    "kind": "headers",
                    "headers": ["# Risk Assessment", "## Product Overview", "## Identified Risks"],
                },
                {"kind": "token"},
            ]
            risk = build_claim(
                claim_id="claim-risk",
                requirement_id="CRA-ANNEX-VII-RISK",
                source="documents",
                args={"path": risk_path},
                checks=[
                    {"check": "exist", "args": {"paths": [risk_path]}},
                    {"check": "contents", "args": {"path": risk_path, "probes": probes}},
                ],
                severity="high",
                description="The reviewed risk assessment is the evidence for this Requirement.",
            )
            readme_claim = build_claim(
                claim_id="claim-readme",
                requirement_id="CRA-ANNEX-VII-RISK",
                source="documents",
                args={"path": "README.md"},
                checks=[{"check": "exist", "args": {"paths": ["README.md"]}}],
                severity="high",
                description="README.md is separate evidence.",
            )
            proposal = build_claim(
                claim_id="claim-proposal",
                requirement_id="CRA-ANNEX-VII-RISK",
                source="documents",
                args={"path": "marketing.md"},
                checks=[],
                description="A saved proposal that is not executed.",
            )
            write_claim(repo / "curbpack" / "claims", risk)
            write_claim(repo / "curbpack" / "claims", readme_claim)
            write_claim(repo / "curbpack" / "claims", proposal)
            (repo / "curbpack" / "claims" / "claim-readme.json").unlink()

            _git(repo, "init", "-b", "main")
            _commit(repo, "bind the stub")
            failed, failed_code = run_and_write(repo, None, repo / ".curbpack" / "run-result.json")
            self.assertEqual(failed_code, 1)
            by_id = {row["id"]: row for row in failed["claims"]}
            self.assertEqual(by_id["claim-risk"]["checks"][0]["status"], "pass")
            self.assertEqual(by_id["claim-risk"]["checks"][1]["status"], "fail")
            self.assertEqual(by_id["claim-risk"]["status"], "fail")
            self.assertNotIn("claim-readme", by_id)
            self.assertNotIn("claim-proposal", by_id)
            self.assertEqual(failed["worktree"], "clean")

            stub.write_text(_good(repo), encoding="utf-8")
            self.assertFalse(is_stub(stub))
            _commit(repo, "write the assessment")
            passed, passed_code = run_and_write(repo, None, repo / ".curbpack" / "run-result.json")
            self.assertEqual(passed_code, 0)
            self.assertTrue(all(row["status"] == "pass" for row in passed["claims"]))
            self.assertTrue(all(item["status"] == "pass" for row in passed["claims"] for item in row["checks"]))

            target = repo / "docs" / "security" / "risk_assessment.md"
            target.parent.mkdir(parents=True)
            stub.rename(target)
            moved, moved_code = run_and_write(repo, None, repo / ".curbpack" / "run-result.json")
            self.assertEqual(moved_code, 1)
            moved_row = {row["id"]: row for row in moved["claims"]}["claim-risk"]
            self.assertEqual(moved_row["status"], "fail")
            self.assertEqual(moved_row["checks"][0]["status"], "fail")
            self.assertIn("is absent", moved_row["checks"][0]["detail"])
            self.assertEqual(moved_row["checks"][1]["status"], "fail")
            self.assertIn("is absent", moved_row["checks"][1]["detail"])
            self.assertNotIn("header", moved_row["checks"][1]["detail"])

            new_path = "docs/security/risk_assessment.md"
            risk = rebind(
                load_claim(repo / "curbpack" / "claims" / "claim-risk.json"),
                args={"path": new_path},
                checks=[
                    {"check": "exist", "args": {"paths": [new_path]}},
                    {"check": "contents", "args": {"path": new_path, "probes": copy_probes(risk)}},
                ],
            )
            write_claim(repo / "curbpack" / "claims", risk)
            self.assertEqual(version_digest(load_requirement(version_dir / "CRA-ANNEX-VII-RISK.json", published=True)), published_digest)
            _commit(repo, "point claims at the new path")
            restored, restored_code = run_and_write(repo, None, repo / ".curbpack" / "run-result.json")
            self.assertEqual(restored_code, 0)

            target.write_text(_good(repo, header="## Risks we accept"), encoding="utf-8")
            renamed, _ = run_and_write(repo, None, repo / ".curbpack" / "run-result.json")
            renamed_row = next(row for row in renamed["claims"] if row["id"] == "claim-risk")
            self.assertEqual(renamed_row["status"], "fail")
            self.assertEqual(renamed_row["checks"][0]["status"], "pass")
            self.assertEqual(renamed_row["checks"][1]["status"], "fail")
            self.assertIn("## Identified Risks", renamed_row["checks"][1]["detail"])
            probes = copy_probes(risk)
            for probe in probes:
                if probe["kind"] == "headers":
                    probe["headers"] = ["# Risk Assessment", "## Product Overview", "## Risks we accept"]
            risk = rebind(
                risk,
                checks=[
                    {"check": "exist", "args": {"paths": [new_path]}},
                    {"check": "contents", "args": {"path": new_path, "probes": probes}},
                ],
            )
            write_claim(repo / "curbpack" / "claims", risk)
            self.assertEqual(version_digest(load_requirement(version_dir / "CRA-ANNEX-VII-RISK.json", published=True)), published_digest)
            _commit(repo, "follow the header the team uses")
            green, green_code = run_and_write(repo, None, repo / ".curbpack" / "run-result.json")
            self.assertEqual(green_code, 0)

            report = compile_report(
                run_result=green,
                requirements=[load_requirement(version_dir / "CRA-ANNEX-VII-RISK.json", published=True)],
                claims=[load_claim(repo / "curbpack" / "claims" / "claim-risk.json")],
            )
            self.assertEqual(report["run_result"], green)
            self.assertNotIn("signed", report)
            self.assertNotIn("compliant", report)
            self.assertNotIn("git_note", report)
            self.assertNotIn("limits", report)
            self.assertNotIn("packs", report)
            self.assertEqual(report["run_result"]["worktree"], "clean")
            self.assertEqual(worktree_sentence(report["run_result"]), "The worktree was clean.")
            self.assertEqual(report["appendix"][0]["id"], "claim-risk")
            self.assertIn("unsigned", report["appendix"][0]["reason"])
            self.assertEqual(report["run_result"]["claims"][0]["status"], "pass")
            unsigned = read_report_signature(report, trust)
            self.assertFalse(unsigned["verifiable"])

            decided = record_decision(
                report,
                "The file describes risks for this product. I am not concluding that the product meets CRA. Currency of the assessment is a different requirement and is not in this binding.",
            )
            sealed = sign_report(
                decided,
                name="External Reviewer",
                private_key=reviewer_private,
                at="2026-10-12T16:00:00Z",
            )
            report_reading = read_report_signature(sealed, trust)
            requirement_reading = read_signature(sealed["requirements"][0], trust, what="requirement")
            self.assertTrue(report_reading["verifiable"])
            self.assertEqual(report_reading["what"], "review report")
            self.assertEqual(report_reading["who"], "External Reviewer")
            self.assertTrue(requirement_reading["verifiable"])
            self.assertEqual(requirement_reading["who"], "Ada Jurist")
            self.assertNotEqual(report_reading["version"], requirement_reading["version"])
            claim_reading = read_claim_signature(
                sealed["claims"][0],
                trust,
                repo=repo,
                relative="curbpack/claims/claim-risk.json",
            )
            self.assertFalse(claim_reading["verifiable"])
            self.assertNotEqual(claim_reading.get("who"), "PoC2")

            target.write_text(target.read_text(encoding="utf-8") + "\nUncommitted sentence.\n", encoding="utf-8")
            dirty, dirty_code = run_and_write(repo, None, repo / ".curbpack" / "run-result.json")
            self.assertEqual(dirty["worktree"], "dirty")
            self.assertEqual(dirty_code, 0)
            dirty_report = compile_report(
                run_result=dirty,
                requirements=report["requirements"],
                claims=report["claims"],
            )
            self.assertNotIn("git_note", dirty_report)
            self.assertEqual(dirty_report["run_result"]["worktree"], "dirty")
            self.assertIn("not verification of that commit", worktree_sentence(dirty_report["run_result"]))

            later = apply_edits(published, {"remediation_hint": "Say which product the assessment belongs to."})
            later_pack = draft_pack()
            later_pack["version"] = "0.2.0"
            later_published = publish_requirement(later, name="Ada Jurist", private_key=jurist_private, at="2026-12-01T08:00:00Z")
            self.assertNotEqual(version_digest(later_published), published_digest)
            local = working_copy(published, draft_pack())
            self.assertEqual(local["origin"]["version"], "0.1.0")
            self.assertNotEqual(later_pack["version"], local["origin"]["version"])


def copy_probes(claim: dict) -> list[dict]:
    for item in claim["checks"]:
        if item["check"] == "contents":
            return json.loads(json.dumps(item["args"]["probes"]))
    raise AssertionError("contents check missing")


if __name__ == "__main__":
    unittest.main()
