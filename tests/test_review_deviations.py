"""Review assesses each recorded deviation without changing the Check run.

A Claim can carry more than one deviation. Accept and Must be fixed require text.
Not assessed is the absence of an entry. The report stores the assessments beside
the existing decision, and a signed report stays unchanged.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from checks.defaults import created_curbpack
from claims.bind import build_claim, write_claim
from common.canonical import version_digest
from common.errors import ModelError
from common.jsonio import read_json, write_json
from common.signing import generate_keypair
from common.store import load_requirement, save_pack, save_requirement
from requirements.extract.pipeline import draft_pack
from review.compile import (
    compile_report,
    load_report,
    read_report_signature,
    record_decision,
    save_report_assessments,
    save_report_signature,
    save_report_update,
    sign_report,
    write_report,
)
from review.present import present_raw_run
from studio.compile.impl.pdf import compile_pdf
from studio.review.review_page import review_page
from tests.test_rev03_review import (
    _pack,
    _post_redirect,
    _serve,
    _workspace,
)


def _requirement() -> dict:
    return {
        "id": "REQ-A",
        "pack_id": "house",
        "namespace": "RISE/house",
        "remediation_hint": "Use the requirement version from this run.",
        "source": {
            "framework": "test",
            "instrument": "fixture",
            "identifier": "FIX-1",
            "language": "en",
            "url": "https://example.test/law",
        },
        "references": [{"nr": 1, "locator": "1", "law_text": "The product documents the risk."}],
    }


def _claim(requirement: dict) -> dict:
    return build_claim(
        claim_id="claim-a",
        requirement=requirement,
        source="documents",
        args={"path": "docs/a.md"},
        checks=[
            {"check": "exist", "args": {"paths": ["docs/a.md"]}},
            {"check": "exist", "args": {"paths": ["docs/b.md"]}},
        ],
        description="The files are the evidence for this Requirement.",
    )


def _run(claim: dict, *, binding: str = "match", checks: list[dict] | None = None) -> dict:
    recorded = checks or [
        {
            "index": 0,
            "check": "exist",
            "args": claim["checks"][0]["args"],
            "status": "fail",
            "detail": "docs/a.md is absent",
            "remediation_hint": "Add docs/a.md.",
        },
        {
            "index": 1,
            "check": "exist",
            "args": claim["checks"][1]["args"],
            "status": "skipped",
            "detail": "docs/b.md was not checked",
        },
    ]
    status = "fail" if any(item["status"] == "fail" for item in recorded) else (
        "skipped" if any(item["status"] == "skipped" for item in recorded) else "pass"
    )
    row = {
        "id": claim["id"],
        "digest": version_digest(claim),
        "status": status,
        "namespace": claim["namespace"],
        "pack_id": claim["pack_id"],
        "requirement_id": claim["requirement_id"],
        "requirement_digest": claim["requirement_digest"],
        "binding": binding,
        "checks": recorded,
    }
    if binding != "missing":
        row["actual_digest"] = claim["requirement_digest"] if binding == "match" else "a" * 64
    return {
        "tool": "curbcheck",
        "tool_version": "0.0.1a",
        "packs": [{"id": "house", "version": "0.1.0", "digest": "abc"}],
        "claims": [row],
    }


def _assessment(claim: dict, index: int, disposition: str, text: str) -> dict:
    return {
        "kind": "check",
        "claim_id": claim["id"],
        "claim_digest": version_digest(claim),
        "index": index,
        "disposition": disposition,
        "text": text,
    }


class DeviationAssessmentTest(unittest.TestCase):
    def test_two_deviations_on_one_claim_are_assessed_separately(self):
        requirement = _requirement()
        claim = _claim(requirement)
        run = _run(claim)
        report = compile_report(
            run_result=run,
            requirements=[requirement],
            claims=[claim],
            assessments=[
                _assessment(claim, 0, "accept", "The missing note is out of scope for this review."),
                _assessment(claim, 1, "must_fix", "Check docs/b.md."),
            ],
        )
        self.assertEqual(report["run_result"], run)
        self.assertEqual(report["run_result"]["claims"][0]["status"], "fail")
        self.assertEqual(report["run_result"]["claims"][0]["checks"][0]["status"], "fail")
        self.assertEqual(report["run_result"]["claims"][0]["checks"][1]["status"], "skipped")
        self.assertEqual(
            [item["index"] for item in report["assessments"]],
            [0, 1],
        )
        self.assertEqual(report["assessments"][0]["disposition"], "accept")
        self.assertEqual(report["assessments"][1]["disposition"], "must_fix")
        self.assertNotIn("decision", report)

    def test_pass_with_a_stale_binding_stays_pass_and_stale(self):
        requirement = _requirement()
        claim = _claim(requirement)
        run = _run(
            claim,
            binding="stale",
            checks=[
                {
                    "index": 0,
                    "check": "exist",
                    "args": claim["checks"][0]["args"],
                    "status": "pass",
                },
                {
                    "index": 1,
                    "check": "exist",
                    "args": claim["checks"][1]["args"],
                    "status": "pass",
                },
            ],
        )
        report = compile_report(
            run_result=run,
            requirements=[requirement],
            claims=[claim],
            assessments=[
                {
                    "kind": "binding",
                    "claim_id": claim["id"],
                    "claim_digest": version_digest(claim),
                    "namespace": claim["namespace"],
                    "pack_id": claim["pack_id"],
                    "requirement_id": claim["requirement_id"],
                    "requirement_digest": claim["requirement_digest"],
                    "binding": "stale",
                    "disposition": "must_fix",
                    "text": "Rebind the Claim to the current Requirement.",
                }
            ],
        )
        row = report["run_result"]["claims"][0]
        self.assertEqual(row["status"], "pass")
        self.assertEqual(row["binding"], "stale")
        self.assertEqual(row["checks"][0]["status"], "pass")
        self.assertEqual(report["assessments"][0]["binding"], "stale")

    def test_blank_justification_or_correction_is_rejected(self):
        requirement = _requirement()
        claim = _claim(requirement)
        run = _run(claim)
        for disposition in ("accept", "must_fix"):
            with self.assertRaises(ModelError) as caught:
                compile_report(
                    run_result=run,
                    requirements=[requirement],
                    claims=[claim],
                    assessments=[_assessment(claim, 0, disposition, "   ")],
                )
            self.assertEqual(caught.exception.field, "assessments[0].text")

    def test_assessments_survive_compile_reload_pdf_and_signing(self):
        requirement = _requirement()
        claim = _claim(requirement)
        run = _run(claim)
        report = compile_report(
            run_result=run,
            requirements=[requirement],
            claims=[claim],
            assessments=[
                _assessment(claim, 0, "must_fix", "Add docs/a.md."),
                _assessment(claim, 1, "accept", "Skipping docs/b.md is accepted for this run."),
            ],
        )
        private, public = generate_keypair()
        sealed = sign_report(
            record_decision(report, "I reviewed the two deviations."),
            name="Ada Reviewer",
            private_key=private,
            at="2026-11-20T12:00:00Z",
        )
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            path = folder / "review-report_20261120T120000Z.json"
            write_report(path, sealed)
            loaded = load_report(path)
            self.assertEqual(loaded["assessments"], sealed["assessments"])
            reading = read_report_signature(loaded, {"Ada Reviewer": public})
            self.assertTrue(reading["verifiable"])
            changed = dict(loaded)
            changed["assessments"] = [dict(loaded["assessments"][0], text="A different correction.")]
            self.assertFalse(read_report_signature(changed, {"Ada Reviewer": public})["verifiable"])
            pdf = folder / "review.pdf"
            compile_pdf(path, pdf)
            from pypdf import PdfReader

            text = "\n".join(page.extract_text() or "" for page in PdfReader(pdf).pages)
        self.assertLess(text.index("Outstanding deviations requiring correction"), text.index("Accepted deviations"))
        self.assertLess(text.index("Accepted deviations"), text.index("Passing checks"))
        self.assertIn("Add docs/a.md.", text)
        self.assertIn("Skipping docs/b.md is accepted for this run.", text)
        self.assertIn("Add docs/a.md.", text[text.index("Check remediation"):])
        self.assertIn("Use the requirement version from this run.", text)

    def test_a_signed_report_and_an_old_report_keep_their_bytes(self):
        requirement = _requirement()
        claim = _claim(requirement)
        plain = compile_report(run_result=_run(claim), requirements=[requirement], claims=[claim])
        self.assertNotIn("assessments", plain)
        private, _public = generate_keypair()
        sealed = sign_report(
            record_decision(plain, "No structured assessments on this older shape."),
            name="Ada Reviewer",
            private_key=private,
            at="2026-11-20T12:00:00Z",
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review-report_20261120T120000Z.json"
            write_report(path, sealed)
            before = path.read_bytes()
            with self.assertRaises(ModelError):
                save_report_assessments(
                    path,
                    [_assessment(claim, 0, "accept", "Too late.")],
                )
            self.assertEqual(path.read_bytes(), before)
            self.assertNotIn("assessments", load_report(path))

    def test_a_failed_save_or_sign_does_not_leave_assessments_behind(self):
        requirement = _requirement()
        claim = _claim(requirement)
        plain = compile_report(run_result=_run(claim), requirements=[requirement], claims=[claim])
        decided = record_decision(plain, "First reading.")
        private, _public = generate_keypair()
        rejected = _assessment(claim, 9, "accept", "This Check was not recorded.")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review-report_20261120T120000Z.json"
            write_report(path, decided)
            before = path.read_bytes()
            with self.assertRaises(ModelError):
                save_report_update(
                    path,
                    decision="A later reading.",
                    assessments=[rejected],
                )
            self.assertEqual(path.read_bytes(), before)
            unsigned = Path(tmp) / "review-report_20261120T120001Z.json"
            write_report(unsigned, plain)
            unsigned_before = unsigned.read_bytes()
            with self.assertRaises(ModelError):
                save_report_signature(
                    unsigned,
                    name="Ada Reviewer",
                    private_key=private,
                    at="2026-11-20T12:00:00Z",
                    assessments=[_assessment(claim, 0, "must_fix", "Add docs/a.md.")],
                )
            self.assertEqual(unsigned.read_bytes(), unsigned_before)
            self.assertNotIn("assessments", load_report(unsigned))

    def test_assessments_are_not_accepted_for_a_different_run(self):
        requirement = _requirement()
        claim = _claim(requirement)
        other = build_claim(
            claim_id="claim-b",
            requirement=requirement,
            source="documents",
            args={"path": "docs/c.md"},
            checks=[{"check": "exist", "args": {"paths": ["docs/c.md"]}}],
            description="Another file is the evidence.",
        )
        other_run = _run(claim)
        other_run["claims"][0]["id"] = other["id"]
        other_run["claims"][0]["digest"] = version_digest(other)
        with self.assertRaises(ModelError):
            compile_report(
                run_result=other_run,
                requirements=[requirement],
                claims=[other],
                assessments=[_assessment(claim, 0, "accept", "This belongs to the other run.")],
            )

    def test_compile_refuses_a_newer_requirement_and_recovers_the_recorded_one(self):
        historical = _requirement()
        claim = _claim(historical)
        run = _run(claim)
        current = dict(historical)
        current["remediation_hint"] = "Guidance written after the Check run."
        with self.assertRaises(ModelError) as caught:
            compile_report(run_result=run, requirements=[current], claims=[claim])
        self.assertIn("was not substituted", caught.exception.expected)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = draft_pack()
            pack["id"] = historical["pack_id"]
            pack["namespace"] = historical["namespace"]
            pack_dir = root / "curbpack" / "packs" / pack["id"] / pack["version"]
            save_pack(pack_dir, pack)
            save_requirement(pack_dir, historical)
            stored = load_requirement(pack_dir / f"{historical['id']}.json")
            claim = _claim(stored)
            run = _run(claim)
            write_claim(root / "curbpack" / "claims", claim)
            write_json(
                root / "curbpack.json",
                created_curbpack(
                    packs=[pack["id"]],
                    packs_dir="curbpack/packs",
                    claims_dir="curbpack/claims",
                    results_dir="curbpack/results",
                    reports_dir="curbpack/reports",
                ),
            )
            _git(root, "init")
            _git(root, "add", "curbpack.json", "curbpack")
            _git(root, "commit", "-m", "record the requirement")
            changed = load_requirement(pack_dir / f"{stored['id']}.json")
            changed["remediation_hint"] = "Guidance written after the Check run."
            save_requirement(pack_dir, changed)
            current = load_requirement(pack_dir / f"{stored['id']}.json")
            self.assertNotEqual(version_digest(current), claim["requirement_digest"])
            report = compile_report(
                run_result=run,
                requirements=[current],
                claims=[claim],
                repo=root,
            )
        self.assertEqual(
            report["requirements"][0]["remediation_hint"],
            stored["remediation_hint"],
        )
        self.assertEqual(version_digest(report["requirements"][0]), claim["requirement_digest"])
        self.assertEqual(report["run_result"]["claims"][0]["checks"][0]["status"], "fail")

    def test_review_shows_both_hints_and_the_recorded_requirement(self):
        historical = _requirement()
        current = dict(historical)
        current["remediation_hint"] = "Current working-copy guidance."
        claim = _claim(historical)
        current_claim = build_claim(
            claim_id=claim["id"],
            requirement=current,
            source="documents",
            args={"path": "docs/a.md"},
            checks=claim["checks"],
            description=claim["description"],
        )
        run = _run(claim)
        chain = {
            "claims": [
                {
                    "requirement": {
                        "location": "historical",
                        "digest": claim["requirement_digest"],
                        "object": historical,
                    },
                    "claim": {"location": "historical", "digest": run["claims"][0]["digest"], "object": claim},
                    "checks": [],
                    "binding": "match",
                }
            ]
        }
        presentation = present_raw_run(
            run_result=run,
            claims_by_id={current_claim["id"]: current_claim},
            requirements_by_id={current["id"]: current},
            claim_readings={},
            requirement_readings={},
            expanded=None,
            chain=chain,
        )
        self.assertEqual(presentation["groups"][0]["id"], "REQ-A")
        shown = presentation["groups"][0]["claims"][0]
        self.assertEqual(shown["requirement_hint"], "Use the requirement version from this run.")
        self.assertEqual(shown["requirement_hint_from"], "historical")
        self.assertNotEqual(shown["inspect_requirement_id"], "")
        page = review_page(
            {"run_result": run, "claims": []},
            None,
            door={
                "repo_id": "alpha",
                "selected_result": "/tmp/run-result_20261120T120000Z.json",
                "presentation": presentation,
            },
        ).decode()
        self.assertIn('data-check-remediation', page)
        self.assertIn('aria-label="Check remediation"', page)
        self.assertNotIn("Check remediation:", page)
        self.assertIn("Add docs/a.md.", page)
        self.assertIn('data-hint-from="historical"', page)
        self.assertIn('aria-label="Requirement remediation"', page)
        self.assertNotIn("Requirement remediation:", page)
        self.assertIn("Use the requirement version from this run.", page)
        for row in page.split("<tr>"):
            self.assertFalse(
                "Add docs/a.md." in row and "Use the requirement version from this run." in row
            )
        self.assertIn('class="comment-mark"', page)
        self.assertNotIn("comment-mark has-comment", page)
        commented = review_page(
            {
                "run_result": run,
                "claims": [],
                "assessments": [_assessment(claim, 0, "must_fix", "Add docs/a.md.")],
            },
            None,
            door={
                "repo_id": "alpha",
                "selected_result": "/tmp/run-result_20261120T120000Z.json",
                "presentation": presentation,
            },
        ).decode()
        self.assertIn("comment-mark has-comment", commented)
        self.assertIn('class="doc-icon"', commented)
        self.assertNotIn("Current working-copy guidance.", page)
        self.assertIn(">Accept</option>", page)
        self.assertIn(">Must be fixed</option>", page)
        self.assertIn(">Not assessed</option>", page)
        self.assertIn(">Re-run Checks</button>", page)
        self.assertIn(">Create New Report</button>", page)
        self.assertIn(">Back to Claims</a>", page)
        self.assertIn("Unsaved assessments will be lost.", page)

    def test_rebind_does_not_move_the_recorded_run_under_the_live_requirement(self):
        old = _requirement()
        new = dict(old)
        new["id"] = "REQ-NEW"
        old_claim = _claim(old)
        live = build_claim(
            claim_id=old_claim["id"],
            requirement=new,
            source="documents",
            args={"path": "docs/a.md"},
            checks=old_claim["checks"],
            description=old_claim["description"],
        )
        run = _run(old_claim)
        presentation = present_raw_run(
            run_result=run,
            claims_by_id={live["id"]: live},
            requirements_by_id={new["id"]: new},
            claim_readings={},
            requirement_readings={},
            expanded=None,
            chain={"claims": []},
        )
        self.assertEqual(presentation["groups"][0]["id"], "REQ-A")
        self.assertNotEqual(presentation["groups"][0]["id"], "REQ-NEW")
        self.assertEqual(
            presentation["groups"][0]["claims"][0]["requirement_hint_from"],
            "unresolved",
        )


class RerunChecksTest(unittest.TestCase):
    def test_re_run_uses_the_full_check_and_opens_the_new_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace, repo = _workspace("Alpha", Path(tmp) / "alpha")
            _pack(repo, "REQ-SHARED")
            pack_dir = repo / "tree" / "packs" / "cra-baseline" / draft_pack()["version"]
            requirement = load_requirement(pack_dir / "REQ-SHARED.json")
            claim = build_claim(
                claim_id="two-checks",
                requirement=requirement,
                source="documents",
                args={"path": "docs/a.md"},
                checks=[
                    {"check": "exist", "args": {"paths": ["docs/a.md"]}},
                    {"check": "exist", "args": {"paths": ["docs/b.md"]}},
                ],
                description="Both files are the evidence.",
            )
            write_claim(repo / "kept" / "claims", claim)
            (repo / "docs").mkdir()
            (repo / "docs" / "a.md").write_text("a\n", encoding="utf-8")
            (repo / "docs" / "b.md").write_text("b\n", encoding="utf-8")
            existing = repo / "runs" / "out" / "run-result_20260101T000000Z.json"
            write_json(existing, {"tool": "curbcheck", "tool_version": "0.0.1a", "packs": [], "claims": []})
            before = existing.read_bytes()
            with _serve(workspace) as base:
                location = _post_redirect(
                    base + "/check",
                    {"repo_id": "alpha", "action": "check", "return_to": "/review"},
                )
            self.assertIn("/review?", location)
            self.assertIn("result=", location)
            self.assertNotIn("/check?", location)
            self.assertEqual(existing.read_bytes(), before)
            created = [
                path
                for path in (repo / "runs" / "out").glob("run-result_*.json")
                if path != existing
            ]
            self.assertEqual(len(created), 1)
            result = read_json(created[0])
            self.assertEqual(len(result["claims"]), 1)
            self.assertEqual(len(result["claims"][0]["checks"]), 2)
            self.assertEqual(
                [item["check"] for item in result["claims"][0]["checks"]],
                ["exist", "exist"],
            )


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "-c", "user.email=review@example.com", "-c", "user.name=Review", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout
