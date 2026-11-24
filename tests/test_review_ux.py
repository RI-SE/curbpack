"""Check and Review stay understandable, and a signed report stays unchanged.

A Review opened with no document offers the latest Check run and does not
compile. A signed report is read-only: decision and review-sign are rejected,
including a direct POST, and Compile writes a new file.
"""

from __future__ import annotations

import tempfile
import unittest
import urllib.parse
from pathlib import Path

from common.errors import ModelError
from common.jsonio import read_json, write_json
from common.signing import generate_keypair
from review.compile import (
    compile_report,
    load_report,
    record_decision,
    save_report_decision,
    save_report_signature,
    sign_report,
    write_report,
)
from studio.check.check_model import _performed_checks
from studio.check.check_page import check_page
from studio.review.model import _reports_for_run
from studio.review.review_page import review_page
from studio.claim.claims_page import claims_page
from tests.test_rev03_review import (
    _config,
    _exist_claim,
    _get,
    _matching_run,
    _open_run,
    _pack,
    _post,
    _requirement,
    _run,
    _serve,
    _workspace,
)
from claims.bind import build_claim, write_claim


class ReviewStartTest(unittest.TestCase):
    def test_review_offers_the_latest_run_without_opening_or_compiling_it(self):
        with tempfile_workspace() as (workspace, repo):
            _config(repo, results_dir="runs/out", reports_dir="signed/reports")
            older = repo / "runs" / "out" / "run-result_20260101T000000Z.json"
            latest = repo / "runs" / "out" / "run-result_20260101T000001Z.json"
            older.parent.mkdir(parents=True)
            (repo / "signed" / "reports").mkdir(parents=True)
            _write_run(older, "claim-older")
            _write_run(latest, "claim-latest")
            with _serve(workspace) as base:
                page = _get(base + "/review?repo=alpha")
            self.assertIn("<h1>Review</h1>", page)
            self.assertNotIn('class="review-process"', page)
            self.assertIn("No previous Check result has been chosen.", page)
            self.assertIn('go to the <a href="/check">Check</a> tab', page)
            self.assertIn("review the latest Check result", page)
            self.assertNotIn("Nothing is opened until you choose a Check run.", page)
            self.assertNotIn("Review the latest run", page)
            self.assertNotIn("Save decision and review-sign need a report file.", page)
            self.assertIn(urllib.parse.quote(str(latest.resolve()), safe=""), page)
            self.assertNotIn('action="/review/compile"', page)
            self.assertNotIn("claim-older", page)
            self.assertNotIn("claim-latest", page)
            self.assertIn("run-result_20260101T000001Z.json", page)
            self.assertNotIn("run-result_20260101T000000Z.json", page)
            self.assertNotIn("<h2>Run results</h2>", page)
            self.assertNotIn("<h2>Review reports</h2>", page)

    def test_an_opened_run_shows_the_requirement_the_claim_and_compile(self):
        with tempfile_workspace() as (workspace, repo):
            _pack(repo, "REQ-SHARED")
            claim = _exist_claim("purpose-note", "REQ-SHARED", "purpose.md")
            write_claim(repo / "kept" / "claims", claim)
            _matching_run(repo, [claim])
            path = next((repo / "runs" / "out").glob("run-result_*.json"))
            with _serve(workspace) as base:
                page = _open_run(base, "alpha", path)
            self.assertIn(path.name, page)
            self.assertNotIn('class="review-process"', page)
            self.assertIn("Execution", page)
            self.assertNotIn("This is the Check result under review.", page)
            self.assertIn('id="review-save"', page)
            self.assertIn('id="sign-open"', page)
            self.assertNotIn(">Create New Report</button>", page)
            self.assertNotIn("Compile writes a new unsigned report", page)
            self.assertIn("not saved", page)
            self.assertIn('data-selected="run"', page)
            self.assertNotIn("No claims need attention", page)
            queue = page.split('<table class="review-queue">', 1)[1]
            self.assertIn('data-claim="purpose-note"', queue)
            self.assertIn(">Passed</option>", queue)
            self.assertIn(">Must be fixed</option>", queue)
            self.assertNotIn(">Retire</option>", queue)
            self.assertIn('data-comment-dialog="comment-check-purpose-note--"', queue)
            select = queue.split("<select", 1)[1].split("</select>", 1)[0]
            self.assertNotIn("data-comment-when", select)
            self.assertEqual(page.count("if (!raw) return false;"), 2)
            self.assertIn(
                "This verdict needs a comment. Close without one and the previous verdict returns.",
                page,
            )
            self.assertIn('id="retire-confirm"', page)
            self.assertIn("Remove retired Checks from Claims when signing the report.", page)
            self.assertIn('id="review-compile"', page)
            self.assertNotIn("Reports for this run", page)
            self.assertNotIn("No report for this run yet.", page)
            self.assertNotIn("<h2>Run results</h2>", page)
            self.assertNotIn("no field for meeting CRA", page)

    def test_only_reports_for_the_open_run_show_decision_and_signature(self):
        claim = build_claim(
            claim_id="claim-a",
            requirement=_requirement("REQ-A"),
            source="documents",
            args={"path": "docs/a.md"},
            checks=[{"check": "exist", "args": {"paths": ["docs/a.md"]}}],
            description="The file is the evidence.",
        )
        other = build_claim(
            claim_id="claim-b",
            requirement=_requirement("REQ-B"),
            source="documents",
            args={"path": "docs/b.md"},
            checks=[{"check": "exist", "args": {"paths": ["docs/b.md"]}}],
            description="The other file is the evidence.",
        )
        from common.canonical import version_digest
        from requirements.extract.pipeline import draft_pack

        def run_for(claim: dict) -> dict:
            return {
                "tool": "curbcheck",
                "tool_version": "0.0.1a",
                "packs": [{"id": "example", "version": draft_pack()["version"], "digest": "abc"}],
                "claims": [
                    {
                        "id": claim["id"],
                        "digest": version_digest(claim),
                        "status": "pass",
                        "checks": [
                            {
                                "index": 0,
                                "check": "exist",
                                "args": claim["checks"][0]["args"],
                                "status": "pass",
                            }
                        ],
                    }
                ],
            }

        run_one = run_for(claim)
        this_run = compile_report(
            run_result=run_one,
            requirements=[_requirement("REQ-A")],
            claims=[claim],
        )
        this_run = sign_report(
            record_decision(this_run, "First reading."),
            name="Ada Reviewer",
            private_key=generate_keypair()[0],
            at="2026-10-21T12:00:00Z",
        )
        other_run = record_decision(
            compile_report(
                run_result=run_for(other),
                requirements=[_requirement("REQ-B")],
                claims=[other],
            ),
            "Other run.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_report(folder / "review-report_20260101T000000Z.json", this_run)
            write_report(folder / "review-report_20260102T000000Z.json", other_run)
            rows = _reports_for_run(folder, this_run["run_result"])
        self.assertEqual([row["name"] for row in rows], ["review-report_20260101T000000Z.json"])
        self.assertEqual(rows[0]["decision"], "First reading.")
        self.assertTrue(rows[0]["signed"])
        self.assertEqual(rows[0]["signer"], "Ada Reviewer")
        page = review_page(
            {"run_result": this_run["run_result"], "claims": [], "appendix": []},
            None,
            saved=False,
            door={
                "repo_id": "alpha",
                "selected_result": "/tmp/runs/run-result_20260101T000000Z.json",
                "run_reports": rows,
            },
        ).decode()
        self.assertIn('data-selected="run"', page)
        self.assertNotIn("First reading.", page)
        self.assertNotIn("Signed by Ada Reviewer", page)
        self.assertNotIn("Other run.", page)
        self.assertNotIn("Reports for this run", page)
        self.assertNotIn("<h2>Review reports</h2>", page)
        self.assertNotIn("A review of this Check run is already started.", page)

    def test_an_unsigned_report_asks_before_the_same_run_opens_again(self):
        page = review_page(
            {"run_result": {"claims": []}, "claims": [], "appendix": []},
            None,
            saved=False,
            door={
                "repo_id": "alpha",
                "selected_result": "/tmp/runs/run-result_20260101T000000Z.json",
                "existing_review_items": "/tmp/.curbpack/tmp/run-result_20260101T000000Z/review_items.json",
            },
        ).decode()
        self.assertIn("Continue this review or start over?", page)
        self.assertIn("resume=1", page)
        self.assertIn(">Continue</a>", page)
        self.assertIn(">Start over</a>", page)
        self.assertIn(">Cancel</a>", page)
        self.assertIn("fresh=1", page)
        fresh = review_page(
            {"run_result": {"claims": []}, "claims": [], "appendix": []},
            None,
            saved=False,
            door={
                "repo_id": "alpha",
                "selected_result": "/tmp/runs/run-result_20260101T000000Z.json",
                "review_fresh": True,
                "run_reports": [
                    {
                        "name": "review-report_20260102T000000Z.json",
                        "path": "/tmp/reports/review-report_20260102T000000Z.json",
                        "signed": False,
                    }
                ],
            },
        ).decode()
        self.assertNotIn("Continue this review or start over?", fresh)
        continued = review_page(
            {"run_result": {"claims": []}, "claims": [], "appendix": []},
            None,
            saved=False,
            door={
                "repo_id": "alpha",
                "selected_result": "/tmp/runs/run-result_20260101T000000Z.json",
                "review_resumed": True,
                "reuse_offer": "review-report_20260102T000000Z",
                "run_reports": [
                    {
                        "name": "review-report_20260102T000000Z.json",
                        "path": "/tmp/reports/review-report_20260102T000000Z.json",
                        "signed": False,
                    }
                ],
            },
        ).decode()
        self.assertNotIn("A review of this Check run is already started.", continued)
        self.assertNotIn("Take in the remediation report?", continued)

    def test_history_is_a_column_only_when_an_item_has_history(self):
        from studio.review.impl.items import check_digest

        digest = check_digest("exist", {"paths": ["docs/a.md"]})
        door = {
            "repo_id": "alpha",
            "selected_result": "/tmp/runs/run-result_20260101T000000Z.json",
            "review_mode": "review",
            "review_items": [
                {
                    "key": {"claim_id": "claim-a", "check_digest": digest},
                    "decision": "pass",
                    "remediation_history": [
                        {
                            "date": "2026-11-23T08:15:00Z",
                            "remediation": "Added the missing file.",
                            "transition": "must_fix -> pass",
                        }
                    ],
                }
            ],
        }
        presentation = {
            "groups": [
                {
                    "id": "REQ-A",
                    "open": True,
                    "claims": [
                        {
                            "id": "claim-a",
                            "requirement_id": "REQ-A",
                            "binding": "match",
                            "checks": [
                                {
                                    "index": 0,
                                    "check": "exist",
                                    "args": {"paths": ["docs/a.md"]},
                                    "status": "pass",
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        page = review_page(
            {"run_result": {"claims": []}, "claims": [], "appendix": []},
            None,
            saved=False,
            door={**door, "presentation": presentation},
        ).decode()
        self.assertIn("Remediation history", page)
        self.assertIn("Added the missing file.", page)
        self.assertIn("must_fix -&gt; pass", page)
        self.assertNotIn('data-action="retire"', page)
        bare = review_page(
            {"run_result": {"claims": []}, "claims": [], "appendix": []},
            None,
            saved=False,
            door={"repo_id": "alpha", "review_mode": "review", "review_items": [], "presentation": presentation},
        ).decode()
        self.assertNotIn("Remediation history", bare)

    def test_rediscover_without_discovery_context_links_to_discover(self):
        with tempfile_workspace() as (workspace, repo):
            _pack(repo, "REQ-SHARED")
            claim = _exist_claim("fail-note", "REQ-SHARED", "fail.md")
            write_claim(repo / "kept" / "claims", claim)
            run = _run_for(claim, status="fail", detail="fail.md is absent")
            path = repo / "runs" / "out" / "run-result_20260101T000000Z.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            from common.jsonio import write_json

            write_json(path, run)
            with _serve(workspace) as base:
                page = _open_run(base, "alpha", path)
            self.assertIn(
                "Find the file first. Re-discover the Claim if that does not work.",
                page,
            )
            self.assertIn('aria-label="Check remediation"', page)
            self.assertNotIn(">Re-Discover</a>", page)
            self.assertNotIn(">Re-Discover</button>", page)
            self.assertNotIn('class="review-discover"', page)

    def test_rediscover_with_discovery_context_keeps_the_dialog(self):
        with tempfile_workspace() as (workspace, repo):
            _pack(repo, "REQ-SHARED")
            claim = _exist_claim("fail-note", "REQ-SHARED", "fail.md")
            write_claim(repo / "kept" / "claims", claim)
            run = _run_for(claim, status="fail", detail="fail.md is absent")
            path = repo / "runs" / "out" / "run-result_20260101T000000Z.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            from common.jsonio import write_json

            write_json(path, run)
            query = (
                "/review?repo=alpha&source=cra-xml-vii&timestamp=2026-10-21T120000Z&result="
                + urllib.parse.quote(str(path.resolve()), safe="")
            )
            with _serve(workspace) as base:
                page = _get(base + query)
            self.assertIn(
                "Find the file first. Re-discover the Claim if that does not work.",
                page,
            )
            self.assertNotIn(">Re-Discover</a>", page)
            self.assertNotIn(">Re-Discover</button>", page)


class SignedReportLockTest(unittest.TestCase):
    def test_a_signed_report_rejects_another_decision_or_signature(self):
        private, _public = generate_keypair()
        claim = build_claim(
            claim_id="claim-a",
            requirement=_requirement("REQ-A"),
            source="documents",
            args={"path": "docs/a.md"},
            checks=[{"check": "exist", "args": {"paths": ["docs/a.md"]}}],
            description="The file is the evidence.",
        )
        from common.canonical import version_digest

        report = compile_report(
            run_result={
                "tool": "curbcheck",
                "tool_version": "0.0.1a",
                "packs": [{"id": "example", "version": "0.1.0", "digest": "abc"}],
                "claims": [
                    {
                        "id": "claim-a",
                        "digest": version_digest(claim),
                        "status": "pass",
                        "checks": [
                            {
                                "index": 0,
                                "check": "exist",
                                "args": claim["checks"][0]["args"],
                                "status": "pass",
                            }
                        ],
                    }
                ],
            },
            requirements=[_requirement("REQ-A")],
            claims=[claim],
        )
        decided = record_decision(report, "First reading.")
        sealed = sign_report(
            decided,
            name="Ada Reviewer",
            private_key=private,
            at="2026-10-21T12:00:00Z",
        )
        with self.assertRaises(ModelError):
            record_decision(sealed, "A later reading.")
        with self.assertRaises(ModelError):
            sign_report(
                sealed,
                name="Other Reviewer",
                private_key=private,
                at="2026-10-22T12:00:00Z",
            )
        self.assertEqual(sealed["decision"], "First reading.")

    def test_direct_post_cannot_change_a_signed_report_and_compile_writes_a_new_file(self):
        with tempfile_workspace() as (workspace, repo):
            _pack(repo, "REQ-SHARED")
            claim = _exist_claim("lock-note", "REQ-SHARED", "lock.md")
            write_claim(repo / "kept" / "claims", claim)
            _matching_run(repo, [claim])
            run_path = next((repo / "runs" / "out").glob("run-result_*.json"))
            reports = repo / "signed" / "reports"
            with _serve(workspace) as base:
                sealed_page = _post(
                    base + "/review/compile",
                    {
                        "repo_id": "alpha",
                        "result": str(run_path.resolve()),
                        "decision": "First reading.",
                        "name": "Ada Reviewer",
                    },
                )
                report_path = next(
                    path for path in reports.glob("review-report_*.json") if not path.name.endswith(".items.json")
                )
                snapshot = _get(base + "/review?repo=alpha&report=" + urllib.parse.quote(str(report_path.resolve())))
                signed_bytes = report_path.read_bytes()
                self.assertIn("First reading.", sealed_page)
                self.assertNotIn("Reports for this run", snapshot)
                self.assertIn("First reading.", snapshot)
                self.assertNotIn(">Save decision</button>", snapshot)
                self.assertNotIn('action="/review/sign"', snapshot)
                self.assertNotIn('id="sign-open"', snapshot)
                self.assertNotIn('id="review-save"', snapshot)
                rejected = _post(
                    base + "/review",
                    {
                        "repo_id": "alpha",
                        "report": str(report_path.resolve()),
                        "decision": "A later reading.",
                    },
                )
                self.assertIn("signed report is unchanged", rejected)
                self.assertEqual(report_path.read_bytes(), signed_bytes)
                resigned = _post(
                    base + "/review/sign",
                    {
                        "repo_id": "alpha",
                        "report": str(report_path.resolve()),
                        "name": "Other Reviewer",
                    },
                )
                self.assertIn("signed report is unchanged", resigned)
                self.assertEqual(report_path.read_bytes(), signed_bytes)
                _post(
                    base + "/review/compile",
                    {"repo_id": "alpha", "result": str(run_path.resolve())},
                )
                self.assertEqual(report_path.read_bytes(), signed_bytes)
                _post(
                    base + "/review/compile",
                    {
                        "repo_id": "alpha",
                        "result": str(run_path.resolve()),
                        "name": "Ada Reviewer",
                    },
                )
            written = sorted(
                path for path in reports.glob("review-report_*.json") if not path.name.endswith(".items.json")
            )
            self.assertEqual(len(written), 1)
            self.assertEqual(written[0].read_bytes(), signed_bytes)
            self.assertEqual(read_json(written[0])["decision"], "First reading.")

    def test_an_unsigned_draft_still_saves_a_decision(self):
        with tempfile_workspace() as (workspace, repo):
            _pack(repo, "REQ-SHARED")
            claim = _exist_claim("draft-note", "REQ-SHARED", "draft.md")
            write_claim(repo / "kept" / "claims", claim)
            _matching_run(repo, [claim])
            run_path = next((repo / "runs" / "out").glob("run-result_*.json"))
            with _serve(workspace) as base:
                page = _post(
                    base + "/review/compile",
                    {
                        "repo_id": "alpha",
                        "result": str(run_path.resolve()),
                        "decision": "Still a draft.",
                    },
                )
                self.assertEqual(list((repo / "signed" / "reports").glob("review-report_*.json")), [])
                _post(
                    base + "/review/compile",
                    {
                        "repo_id": "alpha",
                        "result": str(run_path.resolve()),
                        "decision": "Still a draft.",
                        "name": "Ada Reviewer",
                    },
                )
            self.assertIn("Still a draft.", page)
            self.assertNotIn("Reports for this run", page)
            self.assertIn("<label>Notes</label>", page)
            self.assertIn('name="decision" form="review-compile"', page)
            self.assertNotIn(">Save decision</button>", page)
            self.assertIn('id="review-save"', page)
            self.assertIn(">Save</button>", page)
            self.assertIn(">Sign</button>", page)
            self.assertNotIn('action="/review/sign"', page)
            self.assertNotIn(">Create New Report</button>", page)
            written = [
                path
                for path in (repo / "signed" / "reports").glob("review-report_*.json")
                if not path.name.endswith(".items.json")
            ]
            self.assertEqual(len(written), 1)
            saved = read_json(written[0])
            self.assertEqual(saved["decision"], "Still a draft.")
            self.assertIn("signed", saved)


class CheckSummaryTest(unittest.TestCase):
    def test_a_signed_must_fix_round_links_to_remediate(self):
        page = check_page(
            None,
            None,
            editor={
                "repo_id": "alpha",
                "runs": [
                    {
                        "name": "run-result_20260102T153000Z.json",
                        "path": "/tmp/runs/run.json",
                        "when": "2026-01-02 15:30 UTC",
                        "fail": 4,
                        "pass": 0,
                        "skipped": 0,
                        "review_label": "4 Must fix · Signed",
                        "remedy_label": "Remediate",
                        "remedy_href": "/review?repo=alpha&mode=remediation",
                    }
                ],
            },
        ).decode()
        self.assertIn("4 Must fix · Signed", page)
        self.assertIn(">Remediate</a>", page)
        self.assertIn("mode=remediation", page)
    def test_check_page_explains_the_flow_and_lists_performed_checks(self):
        page = check_page(
            None,
            None,
            editor={
                "repo_id": "alpha",
                "packs": [
                    {
                        "id": "cra-baseline",
                        "name": "CRA baseline",
                        "present": True,
                        "pack_dir": "/tmp/packs/cra-baseline",
                        "claims": 4,
                    }
                ],
                "runs": [
                    {
                        "name": "run-result_20260102T153000Z.json",
                        "path": "/tmp/runs/run-result_20260102T153000Z.json",
                        "when": "2026-01-02 15:30 UTC",
                        "fail": 0,
                        "pass": 3,
                        "skipped": 1,
                        "stale": 0,
                        "missing": 0,
                    },
                    {
                        "name": "run-result_20260101T000000Z.json",
                        "path": "/tmp/runs/run-result_20260101T000000Z.json",
                        "when": "2026-01-01 00:00 UTC",
                        "fail": 1,
                        "pass": 0,
                        "skipped": 0,
                        "stale": 1,
                        "missing": 0,
                    },
                ],
            },
        ).decode()
        card_at = page.index('class="card discover-wrap check-run"')
        performed = page.index("Checks performed")
        card = page[card_at:performed]
        self.assertIn("CRA baseline", card)
        self.assertIn('class="num">4<', card)
        self.assertIn('name="action" value="check"', card)
        self.assertNotIn("/tmp/packs/cra-baseline", page)
        self.assertNotIn("<th>Path</th>", page)
        self.assertLess(page.index("<h1>Check</h1>"), page.index("Sign locks them"))
        self.assertIn(
            "Check writes a Result. Review saves decisions on that Result until Sign locks them. "
            "Remediation starts from that signed review. "
            "A Remedy Report records the work and leaves those decisions unchanged.",
            page,
        )
        self.assertIn("<th>Check Result</th>", page)
        self.assertIn("<th>Review</th>", page)
        self.assertIn("<th>Remediation</th>", page)
        self.assertLess(page.index("Checks performed"), page.index("2026-01-02 15:30 UTC"))
        self.assertLess(page.index("2026-01-02 15:30 UTC"), page.index("2026-01-01 00:00 UTC"))
        self.assertIn("1 fail", page)
        self.assertIn("0 pass", page)
        self.assertIn("0 skipped", page)
        self.assertIn("1 stale", page)
        self.assertIn(
            "/review?repo=alpha&amp;result=%2Ftmp%2Fruns%2Frun-result_20260102T153000Z.json",
            page,
        )
        self.assertIn(
            "/review?repo=alpha&amp;result=%2Ftmp%2Fruns%2Frun-result_20260101T000000Z.json",
            page,
        )
        self.assertNotIn("Run result", page)
        self.assertNotIn("/tmp/runs/run-result_20260102T153000Z.json", page)
        self.assertNotIn("<h2>Report</h2>", page)
        self.assertNotIn("review-report_", page)
        self.assertIn('name="action" value="check"', page)
        self.assertNotIn("not a legal conclusion", page)

    def test_performed_checks_lists_each_result_newest_first(self):
        older = _run_result("fail", "stale")
        newer = _run_result("pass", "match")
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_json(folder / "run-result_20260101T000000Z.json", older)
            write_json(folder / "run-result_20260102T153045Z.json", newer)
            write_json(folder / "review-report_20260102T160000Z.json", {"decision": "later"})
            rows = _performed_checks(str(folder))
        self.assertEqual(
            [row["name"] for row in rows],
            ["run-result_20260102T153045Z.json", "run-result_20260101T000000Z.json"],
        )
        self.assertEqual(rows[0]["when"], "2026-01-02 15:30:45 UTC")
        self.assertEqual(rows[0]["pass"], 1)
        self.assertEqual(rows[0]["fail"], 0)
        self.assertEqual(rows[1]["fail"], 1)
        self.assertEqual(rows[1]["stale"], 1)
        self.assertNotIn("review-report_20260102T160000Z.json", [row["name"] for row in rows])


class ReviewReturnTest(unittest.TestCase):
    def test_claims_editor_links_back_to_the_review_that_opened_it(self):
        page = claims_page(
            {"claims": [], "return_to": "/review?repo=alpha&result=%2Ftmp%2Frun.json"}
        ).decode()
        self.assertIn("Back to Review", page)
        self.assertIn("/review?repo=alpha&amp;result=%2Ftmp%2Frun.json", page)
        blocked = claims_page({"claims": [], "return_to": "https://evil.example/review"}).decode()
        self.assertNotIn("evil.example", blocked)
        self.assertNotIn("Back to Review", blocked)


class SignedReportFileTest(unittest.TestCase):
    def test_save_helpers_leave_the_signed_file_bytes_alone(self):
        import tempfile

        private, _public = generate_keypair()
        claim = build_claim(
            claim_id="claim-a",
            requirement=_requirement("REQ-A"),
            source="documents",
            args={"path": "docs/a.md"},
            checks=[{"check": "exist", "args": {"paths": ["docs/a.md"]}}],
            description="The file is the evidence.",
        )
        from common.canonical import version_digest

        report = compile_report(
            run_result={
                "tool": "curbcheck",
                "tool_version": "0.0.1a",
                "packs": [{"id": "example", "version": "0.1.0", "digest": "abc"}],
                "claims": [
                    {
                        "id": "claim-a",
                        "digest": version_digest(claim),
                        "status": "pass",
                        "checks": [
                            {
                                "index": 0,
                                "check": "exist",
                                "args": claim["checks"][0]["args"],
                                "status": "pass",
                            }
                        ],
                    }
                ],
            },
            requirements=[_requirement("REQ-A")],
            claims=[claim],
        )
        sealed = sign_report(
            record_decision(report, "First reading."),
            name="Ada Reviewer",
            private_key=private,
            at="2026-10-21T12:00:00Z",
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review-report_20260101T000000Z.json"
            write_report(path, sealed)
            before = path.read_bytes()
            with self.assertRaises(ModelError):
                save_report_decision(path, "A later reading.")
            with self.assertRaises(ModelError):
                save_report_signature(
                    path,
                    name="Other Reviewer",
                    private_key=private,
                    at="2026-10-22T12:00:00Z",
                )
            self.assertEqual(path.read_bytes(), before)


def _run_result(status: str, binding: str) -> dict:
    row = {
        "id": "claim-a",
        "digest": "abc",
        "status": status,
        "namespace": "RISE/Example",
        "pack_id": "example",
        "requirement_id": "REQ-A",
        "requirement_digest": "recorded",
        "binding": binding,
        "checks": [
            {
                "index": 0,
                "check": "exist",
                "args": {"paths": ["a.md"]},
                "status": status,
                **({} if status == "pass" else {"detail": "missing file"}),
            }
        ],
    }
    if binding != "missing":
        row["actual_digest"] = "actual"
    return {
        "tool": "curbcheck",
        "tool_version": "0.0.1a",
        "packs": [{"id": "example", "version": "0.1.0", "digest": "abc"}],
        "claims": [row],
    }


def _write_run(path: Path, claim_id: str) -> None:
    from common.jsonio import write_json

    write_json(path, _run(claim_id))


def _run_for(claim: dict, *, status: str, detail: str) -> dict:
    from common.canonical import version_digest
    from requirements.extract.pipeline import draft_pack

    return {
        "tool": "curbcheck",
        "tool_version": "0.0.1a",
        "commit": "abc123",
        "worktree": "clean",
        "packs": [{"id": "cra-baseline", "version": draft_pack()["version"], "digest": "abc"}],
        "claims": [
            {
                "id": claim["id"],
                "digest": version_digest(claim),
                "status": status,
                "checks": [
                    {
                        "index": 0,
                        "check": "exist",
                        "args": claim["checks"][0]["args"],
                        "status": status,
                        "detail": detail,
                    }
                ],
            }
        ],
    }


class tempfile_workspace:
    def __enter__(self):
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        return _workspace("Alpha", root / "alpha")

    def __exit__(self, *args):
        self._tmp.cleanup()
