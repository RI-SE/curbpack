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
        self.assertNotIn("view=", newest["review_href"])
        self.assertEqual(newest["remedy_label"], "—")
        self.assertEqual(signed["review_label"], "View")
        self.assertIn("view=review", signed["review_href"])
        self.assertNotIn("mode=remediation", signed["review_href"])
        self.assertEqual(signed["remedy_label"], "Completed")
        self.assertIn("view=report", signed["remedy_href"])
        self.assertNotIn("remedy_report_label", signed)
        self.assertEqual(flat["review_label"], "Create")
        self.assertNotIn(str(first), flat["review_href"])

    def test_a_revoked_seal_does_not_keep_the_round_as_a_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            run = folder / "run-result_20261124T072314Z"
            run.mkdir()
            write_json(run / "run-result.json", _body())
            write_json(
                run / "review-report.json",
                {"signed": {"name": "Niklas", "at": "2026-11-24T08:00:00Z", "signature": "seal"}},
            )
            write_json(
                run / "remedy-report_20261125T100000Z.json",
                {"signed": {"name": "Ada", "at": "2026-11-25T10:00:00Z", "signature": "older"}},
            )
            write_json(
                run / "remedy-report_20261125T110000Z.json",
                {"signed": {"name": "Ada", "at": "2026-11-25T11:00:00Z", "signature": "seal"}},
            )
            write_json(
                run / "review_items.json",
                {
                    "items": [],
                    "remedy": True,
                    "review_locked": True,
                    "remedy_revoked": [
                        {
                            "report": "remedy-report_20261125T110000Z.json",
                            "name": "Ada",
                            "at": "2026-11-25T12:00:00Z",
                        }
                    ],
                },
            )
            rows = _annotate_rounds(None, None, _performed_checks(str(folder)), "alpha")
        self.assertEqual(rows[0]["remedy_label"], "Continue")
        self.assertNotIn("view=report", rows[0]["remedy_href"])

    def test_review_items_in_the_check_directory_are_in_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            run = folder / "run-result_20261122T101800Z"
            run.mkdir()
            write_json(run / "run-result.json", _body())
            write_json(run / "review_items.json", {"items": []})
            rows = _annotate_rounds(None, None, _performed_checks(str(folder)), "alpha")
        self.assertEqual(rows[0]["review_label"], "Continue")
        self.assertIn("result=", rows[0]["review_href"])
        self.assertIn("resume=1", rows[0]["review_href"])
        self.assertNotIn("view=", rows[0]["review_href"])
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
        self.assertEqual(row["review_label"], "View")
        self.assertIn("view=review", row["review_href"])
        self.assertNotIn("mode=remediation", row["review_href"])
        self.assertEqual(row["remedy_label"], "Completed")
        self.assertEqual(row["remedy_pdf_href"], "")
        self.assertIn("mode=remediation", row["remedy_href"])
        self.assertIn("view=report", row["remedy_href"])

    def test_signed_review_moves_from_start_to_continue_to_view_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            run = folder / "run-result_20261123T142000Z"
            run.mkdir()
            write_json(run / "run-result.json", _body())
            write_json(run / "review_items.json", {"items": [], "review_locked": True})
            started = _annotate_rounds(None, None, _performed_checks(str(folder)), "alpha")
            write_json(
                run / "review_items.json",
                {"items": [{"remediation_history": [{"remediation": "Filled"}]}], "review_locked": True, "remedy": True},
            )
            continued = _annotate_rounds(None, None, _performed_checks(str(folder)), "alpha")
            write_json(
                run / "review_items.json",
                {
                    "items": [{"remediation_history": [{"remediation": "Filled"}]}],
                    "review_locked": True,
                    "remedy": True,
                    "remedy_locked": True,
                },
            )
            signed = _annotate_rounds(None, None, _performed_checks(str(folder)), "alpha")
        self.assertEqual(started[0]["review_label"], "View")
        self.assertEqual(started[0]["remedy_label"], "Start")
        self.assertIn("mode=remediation", started[0]["remedy_href"])
        self.assertNotIn("view=report", started[0]["remedy_href"])
        self.assertEqual(continued[0]["review_label"], "View")
        self.assertEqual(continued[0]["remedy_label"], "Continue")
        self.assertEqual(signed[0]["remedy_label"], "Completed")
        self.assertEqual(signed[0]["remedy_pdf_href"], "")
        self.assertIn("view=report", signed[0]["remedy_href"])

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
                        "review_label": "Continue",
                        "review_href": "/review?repo=alpha&result=owned",
                        "remedy_label": "—",
                        "fail": 4,
                        "pass": 0,
                        "skipped": 0,
                    },
                ],
            },
        ).decode()
        self.assertIn("<th>Remedy</th>", page)
        self.assertIn('href="/review?repo=alpha&amp;result=new">Create</a>', page)
        self.assertIn('href="/review?repo=alpha&amp;result=owned">Continue</a>', page)
        self.assertNotIn(">Remediate</a>", page)
        counted = check_page(
            None,
            None,
            editor={
                "repo_id": "alpha",
                "runs": [
                    {
                        "when": "2026-11-24 07:23 UTC",
                        "path": "/tmp/runs/run-result.json",
                        "review_label": "View",
                        "review_href": "/review?repo=alpha",
                        "remedy_label": "Completed",
                        "remedy_href": "/review?repo=alpha&mode=remediation",
                        "remedy_counts": {"fail": 1, "pass": 2, "skipped": 0, "stale": 1},
                        "fail": 4,
                        "pass": 0,
                        "skipped": 0,
                    }
                ],
            },
        ).decode()
        self.assertLess(
            counted.index(">Completed</a>"),
            counted.index("1 fail · 2 pass · 0 skipped · 1 stale"),
        )

    def test_a_remediation_run_is_not_listed_as_performed(self):
        from studio.check.check_model import remediation_results_dir
        from studio.review.impl.items import studio_temp_dir

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "product"
            official = repo / "run_results"
            official.mkdir(parents=True)
            write_json(new_check_run_path(official), _body())
            scratch = repo / "scratch" / "remediation-runs"
            write_json(new_check_run_path(scratch), _body())
            listed = [row["path"] for row in _performed_checks(str(official))]
            self.assertEqual(len(listed), 1)
            self.assertTrue(listed[0].startswith(str(official.resolve())))
            self.assertEqual(
                remediation_results_dir(repo),
                studio_temp_dir(repo) / "remediation-runs",
            )

    def test_the_remove_dialog_names_the_files_and_waits_for_ok(self):
        page = check_page(
            None,
            None,
            editor={
                "repo_id": "alpha",
                "runs": [
                    {
                        "when": "2026-11-25 09:19:22 UTC",
                        "path": "/tmp/runs/run-result_20261125T091922Z/run-result.json",
                        "files": [
                            "run-result_20261125T091922Z/run-result.json",
                            "run-result_20261125T091922Z/review_items.json",
                            "run-result_20261125T091922Z/remedy-report.json",
                        ],
                        "review_label": "Create",
                        "review_href": "/review?repo=alpha",
                        "fail": 0,
                        "pass": 21,
                        "skipped": 0,
                    }
                ],
            },
        ).decode()
        self.assertLess(page.index('<th class="remove">'), page.index("<th>Check Result</th>"))
        self.assertIn('class="trash"', page)
        self.assertIn('aria-label="Remove this check result"', page)
        self.assertIn("<h2>Remove this check result?</h2>", page)
        self.assertIn("run-result_20261125T091922Z/review_items.json", page)
        self.assertIn("run-result_20261125T091922Z/remedy-report.json", page)
        self.assertIn('action="/check/remove"', page)
        dialog = page.split('class="remove-check"', 1)[1].split("</dialog>", 1)[0]
        self.assertIn('class="remove-ok"', dialog)
        self.assertIn('class="secondary"', dialog)
        self.assertNotIn("sign-bad", dialog)
        self.assertIn(">OK</button>", page)
        self.assertIn(">Cancel</button>", page)
        self.assertIn('type="button" class="trash"', page)
        self.assertNotIn('type="submit" class="trash"', page)

    def test_removing_one_check_result_leaves_the_others(self):
        from studio.check.check_model import remove_check_result

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            gone = folder / "run-result_20261125T091922Z"
            kept = folder / "run-result_20261124T142519Z"
            gone.mkdir()
            kept.mkdir()
            write_json(gone / "run-result.json", _body())
            write_json(gone / "review_items.json", {"items": []})
            write_json(gone / "remedy-report.json", {"signed": {"name": "Ada"}})
            outside = folder / "notes.txt"
            outside.write_text("keep", encoding="utf-8")
            target = folder / "kept-target.txt"
            target.write_text("target", encoding="utf-8")
            (gone / "linked.txt").symlink_to(target)
            write_json(kept / "run-result.json", _body())
            removed = remove_check_result(str(folder), str(gone / "run-result.json"))
            self.assertIn("run-result_20261125T091922Z/run-result.json", removed)
            self.assertIn("run-result_20261125T091922Z/review_items.json", removed)
            self.assertIn("run-result_20261125T091922Z/remedy-report.json", removed)
            self.assertIn("run-result_20261125T091922Z/linked.txt", removed)
            self.assertFalse(gone.exists())
            self.assertTrue((kept / "run-result.json").is_file())
            self.assertEqual(outside.read_text(encoding="utf-8"), "keep")
            self.assertEqual(target.read_text(encoding="utf-8"), "target")
            self.assertEqual(remove_check_result(str(folder), str(outside)), [])
            self.assertEqual(remove_check_result(str(folder), str(folder / "missing.json")), [])
