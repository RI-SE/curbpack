"""The remediation PDF is a reading of one signed seal."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader

from common.jsonio import write_json
from common.signing import generate_keypair, read_signature
from studio.compile.impl.remedy_pdf import write_remedy_pdf
from studio.review.impl.items import check_digest, sign_remedy_document
from studio.review.impl.remedy_markdown import parse_remedy_markdown
from studio.review.impl.remedy_report import publish_remedy_reading, published_remedy_file, remedy_account


def _run() -> dict:
    return {
        "claims": [
            {
                "id": "claim-a",
                "binding": "match",
                "checks": [
                    {"check": "contents", "status": "fail", "args": {"path": "SECURITY.md"}},
                    {"check": "exist", "status": "fail", "args": {"paths": ["README.md"]}},
                    {"check": "contents", "status": "fail", "args": {"path": "docs/SECURITY.md"}},
                ],
            },
            {"id": "claim-b", "binding": "stale", "checks": []},
        ]
    }


def _item(claim_id: str, digest: str, **extra) -> dict:
    item = {"key": {"claim_id": claim_id, "check_digest": digest}, "decision": "must_fix"}
    item.update(extra)
    return item


class RemedyAccountTest(unittest.TestCase):
    def setUp(self):
        run = _run()
        checks = run["claims"][0]["checks"]
        self.green = check_digest("contents", {"path": "SECURITY.md"})
        self.retired = check_digest("exist", {"paths": ["README.md"]})
        self.regressed = check_digest("contents", {"path": "docs/SECURITY.md"})
        self.items = [
            _item(
                "claim-a",
                self.green,
                decision="pass",
                remediation_history=[
                    {"date": "2026-11-25T10:00:00Z", "remediation": "Replaced the placeholder.", "transition": "must_fix -> pass"}
                ],
            ),
            _item(
                "claim-a",
                self.retired,
                remediation_history=[
                    {"date": "2026-11-25T10:05:00Z", "remediation": "The check no longer applies.", "action": "retire"}
                ],
            ),
            _item(
                "claim-a",
                self.regressed,
                decision="must_fix",
                comment="Still failing after the full Check.",
                remediation_history=[
                    {"date": "2026-11-25T10:10:00Z", "remediation": "Check", "transition": "must_fix -> pass"},
                    {"date": "2026-11-25T11:00:00Z", "remediation": "Check", "transition": "pass -> fail"},
                ],
            ),
        ]
        del checks

    def test_the_account_separates_green_retired_open_and_what_went_wrong(self):
        document = {
            "items": self.items,
            "remedy": True,
            "notes": "Y and P still fail outside this round.",
            "reference": {"run": "run-result_20261124T142519Z", "review": "review-report_20261124T143249Z.json"},
            "full_checks": ["run-result_20261125T110000Z"],
            "outside": [
                {"run": "run-result_20261125T110000Z", "choice": "ok", "checks": [{"claim_id": "claim-c", "check": "contents"}]},
                {"run": "run-result_20261125T100000Z", "choice": "rolled_back", "checks": [{"claim_id": "claim-a", "check": "exist"}]},
            ],
            "signed": {"name": "Urban", "at": "2026-11-25T12:00:00Z", "signature": "seal"},
        }
        account = remedy_account(document, _run())
        self.assertEqual(account["original"], 4)
        self.assertEqual(account["remediated"], 1)
        self.assertEqual(account["retired"], 1)
        self.assertEqual(account["remaining"], 2)
        self.assertEqual(account["outside_new"], 1)
        self.assertTrue(account["full_check_ran"])
        self.assertEqual(account["regressed"][0]["check"], "contents (docs/SECURITY.md)")
        self.assertIn("verified by a full Check", account["outcome"])
        self.assertIn("1 new deviation was detected", account["outcome"])
        self.assertEqual(account["rolled_back"][0]["check"], "exist")
        self.assertEqual(account["notes"], "Y and P still fail outside this round.")

    def test_a_missing_full_check_is_stated(self):
        account = remedy_account({"items": self.items, "remedy": True}, _run())
        self.assertFalse(account["full_check_ran"])
        self.assertIn("A full Check was not run", account["outcome"])
        self.assertNotIn("no new deviations", account["outcome"])

    def test_the_pdf_is_written_once_and_names_the_appendix(self):
        private, public = generate_keypair()
        sealed = sign_remedy_document(
            self.items,
            name="Urban",
            private_key=private,
            at="2026-11-25T12:00:00Z",
            notes="Y and P still fail outside this round.",
            reference={
                "run": "run-result_20261124T142519Z",
                "review": "review-report_20261124T143249Z.json",
                "reviewer": "Ada Reviewer",
                "reviewed_at": "2026-11-24T14:32:49Z",
            },
            full_checks=["run-result_20261125T110000Z"],
            outside=[
                {"run": "run-result_20261125T110000Z", "choice": "ok", "checks": [{"claim_id": "claim-c", "check": "contents"}]}
            ],
        )
        self.assertEqual(sealed["reference"]["run"], "run-result_20261124T142519Z")
        self.assertEqual(sealed["reference"]["reviewer"], "Ada Reviewer")
        self.assertEqual(sealed["full_checks"], ["run-result_20261125T110000Z"])
        self.assertTrue(read_signature(sealed, {"Urban": public}, what="remedy report")["verifiable"])
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            json_path = folder / "remedy-report_20261125T120000Z.json"
            write_json(json_path, sealed)
            md_path, pdf_path = publish_remedy_reading(sealed, _run(), json_path)
            markdown = md_path.read_text(encoding="utf-8")
            self.assertIn("## Remediation summary", markdown)
            self.assertIn("## Appendix. Deviations at sign-off", markdown)
            self.assertIn("Signed by Ada Reviewer at 2026-11-24T14:32:49Z.", markdown)
            self.assertNotIn("Appendix. Full Check", markdown)
            self.assertNotIn("run-result_20261125T110000Z\n", markdown)
            self.assertIn("Still failing after the full Check.", markdown)
            self.assertNotIn("were red again", markdown)
            self.assertEqual(parse_remedy_markdown(markdown)[0], ("h1", "Remediation report"))
            text = "\n".join(page.extract_text() or "" for page in PdfReader(pdf_path).pages)
            self.assertIn("Remediation summary", text)
            self.assertIn("claim-a", text)
            self.assertIn("does not approve", text)
            self.assertIn("Appendix. Deviations at sign-off", text)
            self.assertIn("Still failing after the full Check.", text)
            self.assertIn("run-result_20261125T110000Z", text)
            self.assertIn("The signature covers the JSON", text)
            with self.assertRaises(FileExistsError):
                write_remedy_pdf(markdown, pdf_path)
            self.assertEqual(
                published_remedy_file(folder, {"remedy_revoked": []}).name,
                "remedy-report_20261125T120000Z.md",
            )
            self.assertIsNone(published_remedy_file(folder, {}, "../other.md"))
