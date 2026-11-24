"""One directory owns one Check, one Review, and one Remedy."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from common.jsonio import write_json
from studio.check.check_model import _annotate_rounds, _performed_checks, new_check_run_path
from studio.check.check_page import check_page


def _body() -> dict:
    return {"tool": "curbcheck", "tool_version": "0", "packs": [], "claims": []}


class CheckDirectoryTest(unittest.TestCase):
    def test_identical_runs_do_not_share_a_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            first = folder / "run-result_20261124T072314Z"
            second = folder / "run-result_20261124T091500Z"
            first.mkdir()
            second.mkdir()
            write_json(first / "run-result.json", _body())
            write_json(second / "run-result.json", _body())
            write_json(
                first / "review-report.json",
                {"signed": {"name": "Niklas", "at": "2026-11-24T08:00:00Z", "signature": "seal"}},
            )
            write_json(
                first / "remedy-report.json",
                {"signed": {"name": "Urban", "at": "2026-11-24T08:10:00Z", "signature": "seal"}},
            )
            write_json(folder / "run-result_20261122T101800Z.json", _body())
            write_json(
                folder / "review-report_20261122T110000Z.json",
                {"run_result": _body(), "signed": {"name": "Niklas", "at": "t", "signature": "s"}},
            )
            rows = _annotate_rounds(None, folder, _performed_checks(str(folder)), "alpha")
        by_when = {row["when"]: row for row in rows}
        newest = by_when["2026-11-24 09:15:00 UTC"]
        signed = by_when["2026-11-24 07:23:14 UTC"]
        flat = by_when["2026-11-22 10:18:00 UTC"]
        self.assertEqual(newest["review_label"], "Create")
        self.assertIn("result=", newest["review_href"])
        self.assertNotIn("report=", newest["review_href"])
        self.assertEqual(newest["remedy_label"], "—")
        self.assertEqual(signed["review_label"], "Signed")
        self.assertIn("report=", signed["review_href"])
        self.assertNotIn("mode=remediation", signed["review_href"])
        self.assertEqual(signed["remedy_label"], "—")
        self.assertEqual(signed["remedy_report_label"], "Signed")
        self.assertIn("mode=remediation", signed["remedy_report_href"])
        self.assertIn("snapshot=", signed["remedy_report_href"])
        self.assertEqual(flat["review_label"], "Create")
        self.assertNotIn(str(first), flat["review_href"])

    def test_review_items_in_the_check_directory_are_in_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            run = folder / "run-result_20261122T101800Z"
            run.mkdir()
            write_json(run / "run-result.json", _body())
            write_json(run / "review_items.json", {"items": []})
            rows = _annotate_rounds(None, None, _performed_checks(str(folder)), "alpha")
        self.assertEqual(rows[0]["review_label"], "In progress")
        self.assertIn("result=", rows[0]["review_href"])
        self.assertNotIn("review_report_label", rows[0])
        self.assertEqual(rows[0]["remedy_label"], "—")

    def test_saved_work_and_a_signed_report_stay_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            run = folder / "run-result_20261124T072314Z"
            run.mkdir()
            write_json(run / "run-result.json", _body())
            write_json(
                run / "review_items.json",
                {"items": [{"decision": "must_fix", "remediation_history": [{"remediation": "Filled"}]}]},
            )
            write_json(
                run / "review-report_20261124T080000Z.json",
                {"signed": {"name": "Niklas", "at": "2026-11-24T08:00:00Z", "signature": "seal"}},
            )
            write_json(
                run / "remedy-report_20261124T090000Z.json",
                {"signed": {"name": "Urban", "at": "2026-11-24T09:00:00Z", "signature": "seal"}},
            )
            rows = _annotate_rounds(None, None, _performed_checks(str(folder)), "alpha")
        row = rows[0]
        self.assertEqual(row["review_label"], "Signed")
        self.assertIn("report=", row["review_href"])
        self.assertNotIn("mode=remediation", row["review_href"])
        self.assertIn("review-report_20261124T080000Z.json", row["review_href"])
        self.assertEqual(row["remedy_label"], "In progress")
        self.assertIn("mode=remediation", row["remedy_href"])
        self.assertNotIn("snapshot=", row["remedy_href"])
        self.assertEqual(row["remedy_report_label"], "Signed")
        self.assertIn("snapshot=", row["remedy_report_href"])

    def test_a_new_studio_check_is_a_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            first = new_check_run_path(folder)
            second = new_check_run_path(folder)
        self.assertEqual(first.name, "run-result.json")
        self.assertTrue(first.parent.name.startswith("run-result_"))
        self.assertNotEqual(first.parent, second.parent)

    def test_the_review_and_remedy_cells_are_links(self):
        page = check_page(
            None,
            None,
            editor={
                "repo_id": "alpha",
                "runs": [
                    {
                        "when": "2026-11-24 09:15 UTC",
                        "path": "/tmp/runs/run-result_20261124T091500Z/run-result.json",
                        "review_label": "Create",
                        "review_href": "/review?repo=alpha&result=new",
                        "remedy_label": "—",
                        "fail": 3,
                        "pass": 0,
                        "skipped": 0,
                    },
                    {
                        "when": "2026-11-24 07:23 UTC",
                        "path": "/tmp/runs/run-result_20261124T072314Z/run-result.json",
                        "review_label": "In progress",
                        "review_href": "/review?repo=alpha&result=owned",
                        "review_report_label": "Signed",
                        "review_report_href": "/review?repo=alpha&report=owned",
                        "remedy_label": "Remediate",
                        "remedy_href": "/review?repo=alpha&result=owned&mode=remediation",
                        "fail": 4,
                        "pass": 0,
                        "skipped": 0,
                    },
                ],
            },
        ).decode()
        self.assertIn("<th>Remediation</th>", page)
        self.assertIn('href="/review?repo=alpha&amp;result=new">Create</a>', page)
        self.assertIn('href="/review?repo=alpha&amp;result=owned">In progress</a>', page)
        self.assertIn('href="/review?repo=alpha&amp;report=owned">Signed</a>', page)
        self.assertIn('href="/review?repo=alpha&amp;result=owned&amp;mode=remediation">Remediate</a>', page)
        self.assertNotIn("mode=remediation", page.split(">Signed</a>")[0].split("href=")[-1])
