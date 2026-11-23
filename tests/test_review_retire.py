"""Retire is a review decision. It can name a passing Check.

The recorded run stays as it was. Claim files change only when the report is
signed and removal was chosen. A Claim that still has a Check is signed again.
A Claim with none left is deleted.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from claims.bind import build_claim, write_claim
from common.canonical import version_digest
from common.errors import ModelError
from common.jsonio import read_json
from common.signing import generate_keypair, read_signature
from common.store import load_claim, save_claim
from review.compile import compile_report, load_report, record_decision, save_report_signature, write_report
from studio.compile.impl.pdf import compile_pdf
from studio.review.review_page import review_page
from tests.test_review_deviations import _assessment, _claim, _requirement, _run


def _pass_run(claim: dict) -> dict:
    run = _run(
        claim,
        checks=[
            {"index": 0, "check": "exist", "args": claim["checks"][0]["args"], "status": "pass"},
            {"index": 1, "check": "exist", "args": claim["checks"][1]["args"], "status": "pass"},
        ],
    )
    return run


class RetireAssessmentTest(unittest.TestCase):
    def test_a_passing_check_can_be_retired_without_changing_the_run(self):
        requirement = _requirement()
        claim = _claim(requirement)
        run = _pass_run(claim)
        report = compile_report(
            run_result=run,
            requirements=[requirement],
            claims=[claim],
            assessments=[_assessment(claim, 0, "retire", "This check no longer applies.")],
            remove_retired_checks=False,
        )
        self.assertEqual(report["run_result"], run)
        self.assertEqual(report["run_result"]["claims"][0]["checks"][0]["status"], "pass")
        self.assertEqual(report["remove_retired_checks"], False)
        self.assertEqual(report["assessments"][0]["text"], "This check no longer applies.")

    def test_retire_requires_text_and_the_removal_choice(self):
        requirement = _requirement()
        claim = _claim(requirement)
        run = _pass_run(claim)
        with self.assertRaises(ModelError) as blank:
            compile_report(
                run_result=run,
                requirements=[requirement],
                claims=[claim],
                assessments=[_assessment(claim, 0, "retire", " ")],
                remove_retired_checks=False,
            )
        self.assertEqual(blank.exception.field, "assessments[0].text")
        with self.assertRaises(ModelError) as missing:
            compile_report(
                run_result=run,
                requirements=[requirement],
                claims=[claim],
                assessments=[_assessment(claim, 0, "retire", "No longer applies.")],
            )
        self.assertEqual(missing.exception.field, "remove_retired_checks")

    def test_accept_still_cannot_assess_a_passing_check_and_a_binding_cannot_be_retired(self):
        requirement = _requirement()
        claim = _claim(requirement)
        run = _pass_run(claim)
        with self.assertRaises(ModelError):
            compile_report(
                run_result=run,
                requirements=[requirement],
                claims=[claim],
                assessments=[_assessment(claim, 0, "accept", "Looks fine.")],
            )
        stale = _run(claim, binding="stale")
        with self.assertRaises(ModelError) as caught:
            compile_report(
                run_result=stale,
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
                        "disposition": "retire",
                        "text": "Drop the binding.",
                    }
                ],
                remove_retired_checks=True,
            )
        self.assertEqual(caught.exception.field, "assessments[0].disposition")
        report = compile_report(
            run_result=run,
            requirements=[requirement],
            claims=[claim],
            assessments=[_assessment(claim, 0, "must_fix", "The check does not cover the requirement.")],
        )
        self.assertEqual(report["assessments"][0]["disposition"], "must_fix")
        self.assertEqual(report["run_result"]["claims"][0]["checks"][0]["status"], "pass")

    def test_signed_items_record_must_fix_on_a_pass_and_a_change_does_not_verify(self):
        from common.jsonio import write_json
        from review.compile import read_report_signature
        from studio.review.impl.items import check_digest, items_from_run, report_items_path

        requirement = _requirement()
        claim = _claim(requirement)
        run = _pass_run(claim)
        report = record_decision(
            compile_report(run_result=run, requirements=[requirement], claims=[claim]),
            "The passing check is not enough.",
        )
        folder = Path(tempfile.mkdtemp())
        path = folder / "review-report_20261123T120000Z.json"
        write_report(path, report)
        items = items_from_run(run)
        digest = check_digest("exist", claim["checks"][0]["args"])
        for item in items:
            if item["key"]["check_digest"] == digest:
                item["decision"] = "must_fix"
                item["comment"] = "The check does not cover the requirement."
        private, public = generate_keypair()
        sealed = save_report_signature(
            path,
            name="Ada Reviewer",
            private_key=private,
            at="2026-11-23T12:00:00Z",
            items=items,
        )
        self.assertEqual(sealed["assessments"][0]["disposition"], "must_fix")
        self.assertEqual(sealed["assessments"][0]["text"], "The check does not cover the requirement.")
        self.assertEqual(sealed["run_result"]["claims"][0]["checks"][0]["status"], "pass")
        self.assertEqual(sealed["items_digest"], version_digest({"items": items}))
        stored_items = read_json(report_items_path(path))
        trust = {"Ada Reviewer": public}
        self.assertTrue(read_signature(stored_items, trust, what="review items")["verifiable"])
        self.assertTrue(read_report_signature(sealed, trust)["verifiable"])
        changed = next(item for item in stored_items["items"] if item.get("decision") == "must_fix")
        changed["decision"] = "pass"
        write_json(report_items_path(path), stored_items)
        self.assertFalse(read_signature(read_json(report_items_path(path)), trust, what="review items")["verifiable"])
        forged = dict(sealed)
        forged["items_digest"] = "0" * 64
        self.assertFalse(read_report_signature(forged, trust)["verifiable"])

    def test_an_old_report_without_retire_stays_valid(self):
        requirement = _requirement()
        claim = _claim(requirement)
        report = compile_report(
            run_result=_run(claim),
            requirements=[requirement],
            claims=[claim],
            assessments=[_assessment(claim, 0, "accept", "Out of scope.")],
        )
        self.assertNotIn("remove_retired_checks", report)


class RetireOnSignTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.claims = Path(self.tmp.name) / "claims"
        self.claims.mkdir()
        self.report_path = Path(self.tmp.name) / "review-report.json"
        self.private, self.public = generate_keypair()
        self.trust = {"Ada Reviewer": self.public}

    def _prepare(self, claim, assessments, *, removal: bool, run=None):
        requirement = _requirement()
        report = compile_report(
            run_result=run or _run(claim),
            requirements=[requirement],
            claims=[claim],
            assessments=assessments,
            remove_retired_checks=removal,
        )
        report = record_decision(report, "Retire the checks that no longer apply.")
        write_report(self.report_path, report)
        write_claim(self.claims, claim)
        return report

    def _sign(self):
        return save_report_signature(
            self.report_path,
            name="Ada Reviewer",
            private_key=self.private,
            at="2026-01-01T00:00:00Z",
            claims_dir=self.claims,
            trust=self.trust,
        )

    def test_signing_without_removal_leaves_the_claim_file(self):
        requirement = _requirement()
        claim = _claim(requirement)
        before = version_digest(claim)
        self._prepare(claim, [_assessment(claim, 0, "retire", "Document only.")], removal=False)
        signed = self._sign()
        self.assertIn("signed", signed)
        self.assertEqual(version_digest(load_claim(self.claims / "claim-a.json")), before)
        self.assertEqual(load_report(self.report_path)["run_result"]["claims"][0]["checks"][0]["status"], "fail")

    def test_signing_removes_one_check_and_signs_the_claim_again(self):
        requirement = _requirement()
        claim = _claim(requirement)
        self._prepare(claim, [_assessment(claim, 0, "retire", "The first check is finished.")], removal=True)
        embedded = read_json(self.report_path)["run_result"]
        self._sign()
        stored = load_report(self.report_path)
        self.assertEqual(stored["run_result"], embedded)
        live = load_claim(self.claims / "claim-a.json")
        self.assertEqual(live["checks"], [claim["checks"][1]])
        reading = read_signature(live, self.trust, what="claim")
        self.assertTrue(reading["verifiable"])
        self.assertEqual(reading["who"], "Ada Reviewer")

    def test_signing_deletes_a_claim_when_its_last_check_is_retired(self):
        requirement = _requirement()
        claim = _claim(requirement)
        self._prepare(
            claim,
            [
                _assessment(claim, 0, "retire", "First check is finished."),
                _assessment(claim, 1, "retire", "Second check is finished."),
            ],
            removal=True,
        )
        self._sign()
        self.assertFalse((self.claims / "claim-a.json").is_file())
        self.assertEqual(len(load_report(self.report_path)["claims"][0]["checks"]), 2)

    def test_a_changed_claim_is_not_signed_and_not_modified(self):
        requirement = _requirement()
        claim = _claim(requirement)
        self._prepare(claim, [_assessment(claim, 0, "retire", "Remove the first check.")], removal=True)
        edited = build_claim(
            claim_id=claim["id"],
            requirement=requirement,
            source="documents",
            args={"path": "docs/a.md"},
            checks=[{"check": "exist", "args": {"paths": ["docs/other.md"]}}],
            description="The files are the evidence for this Requirement.",
        )
        write_claim(self.claims, edited)
        with self.assertRaises(ModelError) as caught:
            self._sign()
        self.assertIn("claim-a", caught.exception.expected)
        self.assertNotIn("signed", read_json(self.report_path))
        self.assertEqual(load_claim(self.claims / "claim-a.json")["checks"], edited["checks"])

    def test_a_failed_second_claim_is_named_and_the_retry_finishes_only_that_claim(self):
        requirement = _requirement()
        first = _claim(requirement)
        second = build_claim(
            claim_id="claim-b",
            requirement=requirement,
            source="documents",
            args={"path": "docs/b.md"},
            checks=[
                {"check": "exist", "args": {"paths": ["docs/b.md"]}},
                {"check": "exist", "args": {"paths": ["docs/c.md"]}},
            ],
            description="The other file is the evidence.",
        )
        run = _run(first)
        run["claims"].append(
            {
                "id": second["id"],
                "digest": version_digest(second),
                "status": "fail",
                "namespace": second["namespace"],
                "pack_id": second["pack_id"],
                "requirement_id": second["requirement_id"],
                "requirement_digest": second["requirement_digest"],
                "binding": "match",
                "actual_digest": second["requirement_digest"],
                "checks": [
                    {
                        "index": 0,
                        "check": "exist",
                        "args": second["checks"][0]["args"],
                        "status": "fail",
                        "detail": "docs/b.md is absent",
                    },
                    {
                        "index": 1,
                        "check": "exist",
                        "args": second["checks"][1]["args"],
                        "status": "pass",
                    },
                ],
            }
        )
        report = compile_report(
            run_result=run,
            requirements=[requirement],
            claims=[first, second],
            assessments=[
                _assessment(first, 0, "retire", "Retire the first check."),
                _assessment(second, 0, "retire", "Retire the other claim."),
            ],
            remove_retired_checks=True,
        )
        report = record_decision(report, "Retire both.")
        write_report(self.report_path, report)
        write_claim(self.claims, first)
        write_claim(self.claims, second)
        real_save = save_claim

        def fail_second(directory, claim):
            if claim["id"] == "claim-b":
                raise OSError("disk full")
            return real_save(directory, claim)

        with mock.patch("studio.review.impl.retire.save_claim", fail_second):
            with self.assertRaises(ModelError) as caught:
                self._sign()
        self.assertIn("claim-b", caught.exception.expected)
        self.assertNotIn("claim-a", caught.exception.expected)
        self.assertIn("signed", load_report(self.report_path))
        self.assertEqual(load_claim(self.claims / "claim-a.json")["checks"], [first["checks"][1]])
        self.assertEqual(load_claim(self.claims / "claim-b.json")["checks"], second["checks"])
        self._sign()
        self.assertEqual(load_claim(self.claims / "claim-b.json")["checks"], [second["checks"][1]])
        self.assertEqual(load_claim(self.claims / "claim-a.json")["checks"], [first["checks"][1]])


class RetirePdfTest(unittest.TestCase):
    def test_a_retired_failure_is_not_an_outstanding_correction(self):
        requirement = _requirement()
        claim = _claim(requirement)
        report = compile_report(
            run_result=_run(claim),
            requirements=[requirement],
            claims=[claim],
            assessments=[_assessment(claim, 0, "retire", "The missing note is retired.")],
            remove_retired_checks=False,
        )
        report = record_decision(report, "Retire that failure.")
        folder = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: None)
        source = folder / "report.json"
        target = folder / "review.pdf"
        write_report(source, report)
        compile_pdf(source, target)
        from pypdf import PdfReader

        text = "\n".join(page.extract_text() or "" for page in PdfReader(target).pages)
        self.assertIn("Retired checks", text)
        self.assertIn("The missing note is retired.", text)
        self.assertNotIn("Checks need follow-up", text)
        findings = text.split("Review findings", 1)[1]
        self.assertLess(findings.index("Retired checks"), findings.index("Passing checks"))


class RetireSignPromptTest(unittest.TestCase):
    def test_retry_wording_appears_only_after_the_report_is_signed(self):
        report = {
            "decision": "Read.",
            "remove_retired_checks": True,
            "run_result": {},
        }
        door = {
            "repo_id": "alpha",
            "report_path": "report.json",
            "retirement_pending": ["purpose-note"],
        }
        unsigned = review_page(report, None, saved=True, door=door).decode()
        self.assertIn("Signing will modify or delete Claim files.", unsigned)
        self.assertIn(">review-sign</button>", unsigned)
        self.assertNotIn("Try retirement again", unsigned)
        self.assertNotIn("were not updated", unsigned)
        signed = dict(report)
        signed["signed"] = {"name": "Ada", "at": "2026-01-01T00:00:00Z", "signature": "YQ=="}
        page = review_page(signed, None, saved=True, door=door).decode()
        self.assertIn("Try retirement again", page)
        self.assertIn("purpose-note", page)
        self.assertIn("does not sign the report again", page)
