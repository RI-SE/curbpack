"""Review queue rendering: attention rows, check pills, and secondary details."""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from common.jsonio import write_json
from claims.bind import write_claim
from studio.review.review_page import review_page

from tests.test_rev03_review import (
    _details,
    _exist_claim,
    _matching_run,
    _open_run,
    _pack,
    _serve,
    _workspace,
)


class ReviewRenderStructureTest(unittest.TestCase):
    def test_open_requirement_uses_poc_card_hierarchy(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace, repo = _workspace("Alpha", Path(tmp) / "alpha")
            _pack(repo, "REQ-FAIL")
            _pack(repo, "REQ-PASS")
            failed = _exist_claim("failed-note", "REQ-FAIL", "bad.md")
            passed = _exist_claim("passed-note", "REQ-PASS", "ok.md")
            write_claim(repo / "kept" / "claims", failed)
            write_claim(repo / "kept" / "claims", passed)
            run = _matching_run(repo, [failed, passed])
            run["claims"][0]["status"] = "fail"
            run["claims"][0]["checks"][0]["status"] = "fail"
            run["claims"][0]["checks"][0]["detail"] = "broke here"
            path = next((repo / "runs" / "out").glob("run-result_*.json"))
            write_json(path, run)
            with _serve(workspace) as base:
                page = _open_run(base, "alpha", path)

            self.assertIn("review-board", page)
            self.assertIn("<h1>Review</h1>", page)
            self.assertIn("<th>Requirement</th>", page)
            self.assertIn("<th>File</th>", page)
            self.assertIn("<th>Checks</th>", page)
            self.assertIn(
                '<th class="tips" title="Wrench: suggestion from the Check. '
                'Scroll: suggestion from the Requirement.">Remedy suggestions</th>',
                page,
            )
            self.assertNotIn("<th>Remedy</th>", page)
            self.assertIn("<th>Decisions</th>", page)
            self.assertNotIn("<th>Verdict</th>", page)
            self.assertIn('<details class="passed-frame" data-approved="1">', page)
            self.assertNotIn('<details class="passed-frame" data-approved="1" open', page)
            open_list, passed_frame = page.split('<details class="passed-frame"', 1)
            self.assertIn("<h2>Deviations</h2>", open_list)
            self.assertLess(
                open_list.index("<h2>Deviations</h2>"),
                open_list.index("1 claim · 1 deviation"),
            )
            self.assertNotIn("<h2>Deviations</h2>", passed_frame)
            self.assertIn("1 claim · 1 deviation", open_list)
            self.assertIn('data-claim="failed-note"', open_list)
            self.assertNotIn('data-claim="passed-note"', open_list)
            self.assertIn('data-claim="passed-note"', passed_frame)

            failed_group = _details(page, "REQ-FAIL")
            self.assertIn("broke here", failed_group)
            self.assertIn('class="check fail"', failed_group)
            self.assertIn("bad.md", failed_group)
            self.assertNotIn("Technical details", failed_group)
            self.assertNotIn("&quot;paths&quot;", failed_group)
            self.assertIn("Technical details", page)
            self.assertIn("&quot;paths&quot;", page.split('<section data-secondary>', 1)[1])

            passed_group = _details(page, "REQ-PASS")
            self.assertIn('data-claim="passed-note"', passed_group)
            self.assertIn(
                '<option value="must_fix" selected>Must be fixed</option>',
                failed_group,
            )
            self.assertIn('<option value="" selected>Passed</option>', passed_group)
            self.assertIn(">Passed</option>", passed_group)
            self.assertIn(">Must be fixed</option>", passed_group)
            self.assertNotIn(">Retire</option>", passed_group)

    def test_check_pills_cover_pass_fail_and_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace, repo = _workspace("Alpha", Path(tmp) / "alpha")
            _pack(repo, "REQ-MIX")
            claim = _exist_claim("mix-note", "REQ-MIX", "mix.md")
            write_claim(repo / "kept" / "claims", claim)
            run = _matching_run(repo, [claim])
            run["claims"][0]["checks"] = [
                {
                    "index": 0,
                    "check": "exist",
                    "args": {"paths": ["mix.md"]},
                    "status": "pass",
                },
                {
                    "index": 1,
                    "check": "contents",
                    "args": {"path": "mix.md"},
                    "status": "fail",
                    "detail": "short",
                },
                {
                    "index": 2,
                    "check": "exist",
                    "args": {"paths": ["later.md"]},
                    "status": "skipped",
                    "detail": "later",
                },
            ]
            run["claims"][0]["status"] = "fail"
            path = next((repo / "runs" / "out").glob("run-result_*.json"))
            write_json(path, run)
            with _serve(workspace) as base:
                page = _open_run(base, "alpha", path)
            group = _details(page, "REQ-MIX")
            self.assertIn('class="check fail"', group)
            self.assertIn('class="check skipped"', group)
            self.assertNotIn('class="check pass"', group)
            self.assertIn('class="check pass"', page.split('data-approved="1"', 1)[1])
            self.assertNotIn("pill-ok", group)

    def test_check_pills_use_short_labels_and_caption_tooltips(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace, repo = _workspace("Alpha", Path(tmp) / "alpha")
            _pack(repo, "REQ-LABELS")
            claim = _exist_claim("label-note", "REQ-LABELS", "note.md")
            write_claim(repo / "kept" / "claims", claim)
            run = _matching_run(repo, [claim])
            run["claims"][0]["checks"] = [
                {"index": 0, "check": "exist", "args": {"paths": ["note.md"]}, "status": "pass"},
                {
                    "index": 1,
                    "check": "contents",
                    "args": {"path": "note.md"},
                    "status": "fail",
                    "detail": "too short",
                    "remediation_hint": "Add a paragraph.",
                },
                {
                    "index": 2,
                    "check": "contents",
                    "args": {"probes": [{"kind": "pattern", "pattern": "TODO"}]},
                    "status": "fail",
                    "detail": "found TODO",
                },
                {
                    "index": 3,
                    "check": "contents",
                    "args": {"probes": [{"kind": "placeholder"}]},
                    "status": "skipped",
                    "detail": "not checked",
                },
                {"index": 4, "check": "fresh", "args": {"max_age_days": 30}, "status": "pass"},
                {"index": 5, "check": "owned", "args": {"email": "a@b.c"}, "status": "pass"},
                {"index": 6, "check": "dep_ban", "args": {"package": "axios"}, "status": "fail", "detail": "banned"},
                {"index": 7, "check": "custom_probe", "args": {}, "status": "fail", "detail": "custom broke"},
            ]
            run["claims"][0]["status"] = "fail"
            path = next((repo / "runs" / "out").glob("run-result_*.json"))
            write_json(path, run)
            with _serve(workspace) as base:
                page = _open_run(base, "alpha", path)
            group = _details(page, "REQ-LABELS")
            passed = page.split('data-approved="1"', 1)[1]
            self.assertIn('class="check pass" title="File is present"><svg class="mark"', passed)
            self.assertIn('aria-label="pass"', passed)
            self.assertIn('d="M20 6 9 17l-5-5"', passed)
            self.assertIn("</svg>Exists</span>", passed)
            self.assertIn(
                'class="check fail" title="File has the expected content"><svg class="mark"',
                group,
            )
            self.assertIn('aria-label="fail"', group)
            self.assertIn('d="M18 6 6 18"', group)
            self.assertIn("</svg>Contents</span>", group)
            self.assertIn(
                'class="check fail" title="File must not contain this text"><svg class="mark"',
                group,
            )
            self.assertIn("</svg>Forbidden text</span>", group)
            self.assertIn(
                'class="check skipped" title="File is not a placeholder">Anti-placeholder · skipped<',
                group,
            )
            self.assertIn(
                'class="check pass" title="File is recent enough"><svg class="mark"',
                passed,
            )
            self.assertIn("</svg>Fresh</span>", passed)
            self.assertIn(
                'class="check pass" title="Written by the claimed author"><svg class="mark"',
                passed,
            )
            self.assertIn("</svg>Owned</span>", passed)
            self.assertIn('class="check fail" title="Banned package version"><svg class="mark"', group)
            self.assertIn("</svg>Banned</span>", group)
            self.assertIn('class="check fail" title="custom_probe"><svg class="mark"', group)
            self.assertIn("</svg>custom_probe</span>", group)
            self.assertNotIn(" · pass<", group)
            self.assertNotIn(" · fail<", group)
            for row in group.split("<tr>"):
                self.assertFalse("</svg>Exists" in row and "</svg>Contents" in row)
                self.assertFalse("</svg>Contents" in row and "</svg>Forbidden text" in row)
                self.assertFalse("</svg>Forbidden text" in row and "</svg>Banned" in row)
            self.assertIn("too short", group)
            self.assertIn("Add a paragraph.", group)
            self.assertIn("found TODO", group)
            self.assertNotIn('title="too short"', group)
            self.assertNotIn('title="Add a paragraph."', group)
            self.assertNotIn(">File is present ·", group)

    def test_remediation_lists_only_unaccepted_red_checks(self):
        green = {
            "id": "claim-green",
            "checks": [{"index": 0, "check": "exist", "status": "pass", "args": {"path": "ok.md"}}],
        }
        accepted = {
            "id": "claim-accepted",
            "digest": "digest-accepted",
            "checks": [
                {"index": 0, "check": "exist", "status": "pass", "args": {"path": "a.md"}},
                {"index": 1, "check": "contents", "status": "fail", "args": {"path": "a.md"}},
            ],
        }
        stale = {
            "id": "claim-stale",
            "binding": "stale",
            "namespace": "house",
            "pack_id": "house-policy",
            "recorded_requirement_id": "REQ-A",
            "checks": [{"index": 0, "check": "exist", "status": "pass", "args": {"path": "c.md"}}],
        }
        open_fail = {
            "id": "claim-open",
            "digest": "digest-open",
            "checks": [
                {"index": 0, "check": "exist", "status": "pass", "args": {"path": "b.md"}},
                {"index": 1, "check": "contents", "status": "fail", "args": {"path": "b.md"}},
                {"index": 2, "check": "fresh", "status": "skipped", "args": {}},
            ],
        }
        report = {
            "run_result": {"claims": []},
            "claims": [],
            "assessments": [
                {
                    "kind": "check",
                    "claim_id": "claim-accepted",
                    "claim_digest": "digest-accepted",
                    "index": 1,
                    "disposition": "accept",
                    "text": "Known gap.",
                }
            ],
        }
        door = {
            "repo_id": "alpha",
            "selected_result": "/tmp/run-result.json",
            "review_mode": "remediation",
            "presentation": {
                "groups": [{"id": "REQ-A", "claims": [green, accepted, stale, open_fail]}]
            },
        }
        page = review_page(report, None, door=door).decode()
        self.assertNotIn('<section class="deviations-frame" data-resolved="1">', page)
        self.assertNotIn("claim-green", page)
        self.assertIn('data-claim="claim-accepted"', page)
        self.assertNotIn('class="check pass"', page)
        self.assertNotIn('class="check skipped"', page)
        self.assertIn('data-claim="claim-open"', page)
        self.assertIn('data-claim="claim-stale"', page)
        self.assertIn('data-binding="stale"', page)
        self.assertIn('class="check fail"', page)

    def test_a_recheck_that_passes_is_shown_read_only(self):
        from studio.review.impl.items import check_digest

        digest = check_digest("contents", {"path": "b.md"})
        claim = {
            "id": "claim-fixed",
            "checks": [
                {"index": 0, "check": "contents", "status": "fail", "args": {"path": "b.md"}},
            ],
        }
        door = {
            "repo_id": "alpha",
            "selected_result": "/tmp/run-result.json",
            "review_mode": "remediation",
            "review_items": [
                {
                    "key": {"claim_id": "claim-fixed", "check_digest": digest},
                    "decision": "pass",
                    "remediation_history": [
                        {"date": "2026-11-24T00:00:00Z", "remediation": "Re-check", "transition": "must_fix -> pass"}
                    ],
                }
            ],
            "presentation": {"groups": [{"id": "REQ-A", "claims": [claim]}]},
        }
        page = review_page({"run_result": {"claims": []}, "claims": []}, None, door=door).decode()
        open_list, resolved = page.split('<section class="deviations-frame" data-resolved="1">', 1)
        self.assertEqual(open_list.count("No claims need attention"), 1)
        self.assertNotIn("claim-fixed", open_list)
        self.assertLess(open_list.index('class="round-notes"'), open_list.index('data-deviations="1"'))
        self.assertIn('name="notes" form="remedy-sign"', open_list)
        self.assertIn('data-claim="claim-fixed"', resolved)
        self.assertIn('data-status="pass"', resolved)
        self.assertIn('class="check pass"', resolved)
        self.assertNotIn("Re-check", resolved)
        self.assertIn("must_fix -&gt; pass", resolved)
        self.assertNotIn(">Re-check</button>", resolved)
        signed_door = dict(door)
        signed_door["remedy_signed"] = True
        signed_door["remedy_signer"] = "Ada"
        signed_door["remedy_signed_at"] = "2026-11-25T11:00:00Z"
        signed_door["remedy_notes"] = "Y and P still fail outside this round."
        signed_door["remedy_md"] = "remedy-report_20261125T110000Z.md"
        signed = review_page({"run_result": {"claims": []}, "claims": []}, None, door=signed_door).decode()
        self.assertLess(signed.index('class="round-notes"'), signed.index('data-deviations="1"'))
        self.assertIn("Y and P still fail outside this round.", signed)
        self.assertNotIn('name="notes"', signed)
        self.assertIn("Signed off by Ada at 2026-11-25T11:00:00Z.", signed)
        self.assertIn("This signed remediation is read-only.", signed)
        self.assertIn("Revoke signature", signed)
        self.assertNotIn("Sign Off", signed)
        self.assertIn("Remediation report", signed)
        self.assertNotIn("Remediation report (PDF)", signed)
        self.assertIn("/review/remedy-report?", signed)
        revoked_door = dict(door)
        revoked_door["remedy_revocation"] = {
            "report": "remedy-report_20261125T110500Z.json",
            "name": "Ada",
            "at": "2026-11-25T12:00:00Z",
        }
        reopened = review_page({"run_result": {"claims": []}, "claims": []}, None, door=revoked_door).decode()
        self.assertIn("data-remedy-revoked", reopened)
        self.assertIn("remedy-report_20261125T110500Z.json", reopened)
        self.assertIn("Sign Off", reopened)
        self.assertNotIn("Revoke signature", reopened)

    def test_a_retired_check_is_struck_and_leaves_the_queue(self):
        from app.pages import CSS
        from studio.review.impl.items import check_digest, record_retire

        digest = check_digest("text_forbid", {"path": "SECURITY.md", "text": "secret"})
        claim = {
            "id": "claim-retired",
            "checks": [
                {
                    "index": 0,
                    "check": "text_forbid",
                    "status": "fail",
                    "args": {"path": "SECURITY.md", "text": "secret"},
                }
            ],
        }
        door = {
            "repo_id": "alpha",
            "selected_result": "/tmp/run-result.json",
            "review_mode": "remediation",
            "review_items": [
                record_retire(
                    {"key": {"claim_id": "claim-retired", "check_digest": digest}, "decision": "must_fix"},
                    remediation="Retired.",
                )
            ],
            "presentation": {"groups": [{"id": "REQ-A", "claims": [claim]}]},
        }
        page = review_page({"run_result": {"claims": []}, "claims": []}, None, door=door).decode()
        open_list, resolved = page.split('<section class="deviations-frame" data-resolved="1">', 1)
        self.assertIn("No claims need attention.", open_list)
        self.assertNotIn("claim-retired", open_list)
        row = next(part for part in re.findall(r"<tr>(.*?)</tr>", resolved, re.S) if "claim-retired" in part)
        self.assertIn('class="check retired"', row)
        self.assertIn("<s>Forbidden text</s>", row)
        self.assertIn(">Retired</span>", row)
        self.assertIn("Retired.", row)
        self.assertNotIn("must_fix -&gt; pass", row)
        self.assertNotIn('data-action="retire"', row)
        self.assertNotIn(">Re-check</button>", row)
        self.assertNotIn("Remove the forbidden text.", row)
        self.assertIn("text-decoration:line-through", CSS)
        self.assertIn(".check.retired", CSS)

    def test_a_retired_check_stays_yellow_beside_an_open_failure(self):
        from studio.review.impl.items import check_digest, record_retire

        retired_digest = check_digest("text_forbid", {"path": "SECURITY.md", "text": "secret"})
        claim = {
            "id": "claim-mixed",
            "checks": [
                {
                    "index": 0,
                    "check": "text_forbid",
                    "status": "fail",
                    "args": {"path": "SECURITY.md", "text": "secret"},
                },
                {
                    "index": 1,
                    "check": "exist",
                    "status": "fail",
                    "args": {"paths": ["SECURITY.md"]},
                    "detail": "SECURITY.md is absent",
                },
            ],
        }
        door = {
            "repo_id": "alpha",
            "selected_result": "/tmp/run-result.json",
            "review_mode": "remediation",
            "review_items": [
                record_retire(
                    {
                        "key": {"claim_id": "claim-mixed", "check_digest": retired_digest},
                        "decision": "must_fix",
                    },
                    remediation="Retired.",
                )
            ],
            "presentation": {"groups": [{"id": "REQ-A", "claims": [claim]}]},
        }
        page = review_page({"run_result": {"claims": []}, "claims": []}, None, door=door).decode()
        self.assertIn('data-claim="claim-mixed"', page)
        self.assertNotIn('data-resolved="1"', page)
        rows = re.findall(r"<tr>(.*?)</tr>", page, re.S)
        retired = next(row for row in rows if 'data-status="retired"' in row)
        failing = next(row for row in rows if 'data-status="fail"' in row and 'data-check="exist"' in row)
        self.assertIn('class="check retired"', retired)
        self.assertIn("<s>Forbidden text</s>", retired)
        self.assertNotIn('data-action=', retired)
        self.assertNotIn("Remove the forbidden text.", retired)
        self.assertIn('class="check fail"', failing)
        self.assertIn('class="actions-menu"', failing)
        self.assertIn(">Re-check</button>", failing)

    def test_a_signed_rebind_leaves_the_remediation_list(self):
        stale = {
            "id": "claim-stale",
            "binding": "stale",
            "namespace": "house",
            "pack_id": "house-policy",
            "recorded_requirement_id": "REQ-A",
            "checks": [{"index": 0, "check": "exist", "status": "pass", "args": {"path": "c.md"}}],
        }
        door = {
            "repo_id": "alpha",
            "selected_result": "/tmp/run-result.json",
            "review_mode": "remediation",
            "review_items": [
                {
                    "key": {"claim_id": "claim-stale", "check_digest": "binding"},
                    "remediation_history": [
                        {"date": "2026-11-24T00:00:00Z", "remediation": "Rebound the Claim.", "action": "rebind"}
                    ],
                }
            ],
            "presentation": {"groups": [{"id": "REQ-A", "claims": [stale]}]},
        }
        page = review_page({"run_result": {"claims": []}, "claims": []}, None, door=door).decode()
        open_list, resolved = page.split('<section class="deviations-frame" data-resolved="1">', 1)
        self.assertIn("No claims need attention.", open_list)
        self.assertNotIn('data-claim="claim-stale"', open_list)
        self.assertIn('data-claim="claim-stale"', resolved)
        self.assertIn('class="check pass"', resolved)
        self.assertIn("Rebound the Claim.", resolved)
        self.assertNotIn('class="check fail"', resolved)
        self.assertNotIn(">Rebind and Sign</button>", resolved)

    def test_a_failed_recheck_keeps_a_rebound_claim_open(self):
        from studio.review.impl.items import binding_digest

        stale = {
            "id": "claim-stale",
            "binding": "stale",
            "namespace": "house",
            "pack_id": "house-policy",
            "recorded_requirement_id": "REQ-A",
            "checks": [{"index": 0, "check": "exist", "status": "pass", "args": {"path": "c.md"}}],
        }
        door = {
            "repo_id": "alpha",
            "selected_result": "/tmp/run-result.json",
            "review_mode": "remediation",
            "review_items": [
                {
                    "key": {"claim_id": "claim-stale", "check_digest": binding_digest()},
                    "decision": "must_fix",
                    "remediation_history": [
                        {"date": "2026-11-24T00:00:00Z", "remediation": "Rebound the Claim.", "action": "rebind"},
                        {"date": "2026-11-24T00:00:01Z", "remediation": "Check", "transition": "pass -> fail"},
                    ],
                }
            ],
            "presentation": {"groups": [{"id": "REQ-A", "claims": [stale]}]},
        }
        page = review_page({"run_result": {"claims": []}, "claims": []}, None, door=door).decode()
        self.assertIn('data-claim="claim-stale"', page)
        self.assertNotIn('data-resolved="1"', page)
        self.assertIn('class="check fail"', page)

    def test_a_green_claim_hides_the_requirement_remedy(self):
        from studio.review.impl.items import check_digest

        digest = check_digest("contents", {"path": "b.md"})
        hint = "Replace TODO / lorem ipsum / [insert ...] with real contact and process details."
        green = {
            "id": "claim-green",
            "requirement_hint": hint,
            "requirement_hint_from": "current",
            "checks": [
                {"index": 0, "check": "contents", "status": "fail", "args": {"path": "b.md"}},
            ],
        }
        door = {
            "repo_id": "alpha",
            "selected_result": "/tmp/run-result.json",
            "review_mode": "remediation",
            "review_items": [
                {"key": {"claim_id": "claim-green", "check_digest": digest}, "decision": "pass"},
            ],
            "presentation": {"groups": [{"id": "REQ-A", "claims": [green]}]},
        }
        page = review_page({"run_result": {"claims": []}, "claims": []}, None, door=door).decode()
        _open_list, resolved = page.split('<section class="deviations-frame" data-resolved="1">', 1)
        self.assertNotIn("data-requirement-remediation", resolved)
        self.assertNotIn("lorem ipsum", resolved)
        still_open = dict(door)
        still_open["review_items"] = []
        open_page = review_page({"run_result": {"claims": []}, "claims": []}, None, door=still_open).decode()
        self.assertIn("data-requirement-remediation", open_page)
        self.assertIn("lorem ipsum", open_page)

    def test_a_changed_claim_shows_its_current_file(self):
        from studio.review.impl.present import present_raw_run

        run = {
            "tool": "curbcheck",
            "tool_version": "0",
            "packs": [],
            "claims": [
                {
                    "id": "claim-a",
                    "digest": "old",
                    "status": "fail",
                    "requirement_id": "REQ-A",
                    "checks": [
                        {
                            "index": 0,
                            "check": "contents",
                            "status": "fail",
                            "args": {"paths": ["SECURITY.md", ".well-known/security.txt"]},
                        }
                    ],
                }
            ],
        }
        current = {
            "id": "claim-a",
            "requirement_id": "REQ-A",
            "checks": [
                {
                    "check": "contents",
                    "args": {"paths": ["docs/SECURITY.md", ".well-known/security.txt"]},
                }
            ],
        }
        shown = present_raw_run(
            run_result=run,
            claims_by_id={"claim-a": current},
            requirements_by_id={"REQ-A": {"id": "REQ-A"}},
            claim_readings={},
            requirement_readings={},
            expanded=None,
        )
        check = shown["groups"][0]["claims"][0]["checks"][0]
        self.assertEqual(
            [row["path"] for row in check["paths"]],
            ["docs/SECURITY.md", ".well-known/security.txt"],
        )
        self.assertEqual(check["args"]["paths"][0], "SECURITY.md")
        self.assertEqual(check["edit"], "unsafe")

    def test_a_requirement_stays_open_until_every_check_is_green(self):
        from studio.review.impl.items import check_digest

        digest = check_digest("contents", {"path": "b.md"})
        passed = {
            "id": "claim-passed",
            "checks": [
                {"index": 0, "check": "contents", "status": "fail", "args": {"path": "b.md"}},
            ],
        }
        waiting = {
            "id": "claim-waiting",
            "binding": "stale",
            "namespace": "house",
            "pack_id": "house-policy",
            "recorded_requirement_id": "REQ-A",
            "checks": [{"index": 0, "check": "exist", "status": "pass", "args": {"path": "c.md"}}],
        }
        door = {
            "repo_id": "alpha",
            "selected_result": "/tmp/run-result.json",
            "review_mode": "remediation",
            "review_items": [
                {
                    "key": {"claim_id": "claim-passed", "check_digest": digest},
                    "decision": "pass",
                    "remediation_history": [
                        {"date": "2026-11-24T00:00:00Z", "remediation": "Re-check", "transition": "must_fix -> pass"}
                    ],
                }
            ],
            "presentation": {"groups": [{"id": "REQ-A", "claims": [passed, waiting]}]},
        }
        page = review_page({"run_result": {"claims": []}, "claims": []}, None, door=door).decode()
        self.assertNotIn('<section class="deviations-frame" data-resolved="1">', page)
        self.assertIn('data-claim="claim-passed"', page)
        self.assertIn('data-status="pass"', page)
        self.assertIn("must_fix -&gt; pass", page)
        self.assertNotIn('formaction="/review/recheck"', page)
        self.assertIn('data-claim="claim-waiting"', page)
        self.assertIn('class="check fail"', page)
        self.assertIn(">Rebind and Sign</button>", page)

    def test_binding_stale_opens_a_sign_dialog_instead_of_rebind(self):
        claim = {
            "id": "claim-a",
            "binding": "stale",
            "namespace": "house",
            "pack_id": "house-policy",
            "recorded_requirement_id": "REQ-A",
            "checks": [
                {"index": 0, "check": "exist", "status": "pass", "args": {"path": "a.md"}},
                {"index": 1, "check": "contents", "status": "fail", "args": {"path": "a.md"}},
            ],
        }
        page = review_page(
            {"run_result": {"claims": []}, "claims": []},
            None,
            door={
                "repo_id": "alpha",
                "selected_result": "/tmp/run-result_20261120T120000Z.json",
                "presentation": {"groups": [{"id": "REQ-A", "claims": [claim]}]},
            },
        ).decode()
        self.assertNotIn(">Rebind</a>", page)
        self.assertNotIn('data-binding-dialog="binding-claim-a"', page)
        self.assertIn('data-binding="stale"', page)
        remediated = review_page(
            {"run_result": {"claims": []}, "claims": []},
            None,
            door={
                "repo_id": "alpha",
                "selected_result": "/tmp/run-result_20261120T120000Z.json",
                "review_mode": "remediation",
                "presentation": {"groups": [{"id": "REQ-A", "claims": [claim]}]},
            },
        ).decode()
        page = remediated
        self.assertIn("<h1>Remediation</h1>", page)
        self.assertIn("<title>Remediation</title>", page)
        self.assertNotIn("<h1>Review</h1>", page)
        self.assertNotIn('class="check pass"', page)
        self.assertIn('data-binding-dialog="binding-claim-a"', page)
        self.assertIn('aria-label="Binding stale"', page)
        self.assertIn("Requirement Binding</button>", page)
        self.assertNotIn(">Binding stale<", page)
        button = page.split('data-binding-dialog="binding-claim-a"', 1)[1].split("</button>", 1)[0]
        self.assertIn('d="M18 6 6 18"', button)
        self.assertNotIn('d="M20 6 9 17l-5-5"', button)
        self.assertIn("The Requirement has changed since this Claim was bound to it.", page)
        self.assertNotIn("Click the check to rebind this Claim.", page)
        self.assertIn("Have you checked the Requirement and confirmed this Claim still applies?", page)
        self.assertIn(">Rebind and Sign</button>", page)
        self.assertIn('name="name"', page)
        self.assertIn('data-rebind="1"', page)
        self.assertIn(">Cancel</button>", page)
        self.assertIn('action="/claims/claim-a/rebind"', page)
        self.assertIn('name="return_to" value="/review?repo=alpha', page)

    def test_a_missing_file_is_a_tip_on_exist_and_not_repeated(self):
        missing = {"path": "SECURITY.md", "state": "missing"}
        claim = {
            "id": "claim-a",
            "status": "fail",
            "checks": [
                {
                    "index": 0,
                    "check": "exist",
                    "status": "fail",
                    "detail": "SECURITY.md is absent",
                    "args": {"paths": ["SECURITY.md"]},
                    "paths": [missing],
                },
                {
                    "index": 1,
                    "check": "contents",
                    "status": "fail",
                    "detail": "SECURITY.md is absent",
                    "args": {
                        "path": "SECURITY.md",
                        "probes": [{"kind": "pattern", "pattern": "TODO"}],
                    },
                    "paths": [missing],
                },
                {
                    "index": 2,
                    "check": "contents",
                    "status": "fail",
                    "detail": "SECURITY.md matches forbidden pattern 'TODO'",
                    "args": {
                        "path": "SECURITY.md",
                        "probes": [{"kind": "pattern", "pattern": "TODO"}],
                    },
                    "paths": [missing],
                },
                {
                    "index": 3,
                    "check": "contents",
                    "status": "fail",
                    "detail": "SECURITY.md contains placeholder text 'TODO'",
                    "args": {
                        "path": "SECURITY.md",
                        "probes": [{"kind": "placeholder"}],
                    },
                    "paths": [{"path": "SECURITY.md", "state": "present"}],
                },
            ],
        }
        page = review_page(
            {"run_result": {"claims": []}, "claims": []},
            None,
            door={
                "repo_id": "alpha",
                "selected_result": "/tmp/run-result_20261120T120000Z.json",
                "presentation": {"groups": [{"id": "REQ-A", "claims": [claim]}]},
            },
        ).decode()
        rows = re.findall(r"<tr>(.*?)</tr>", page, re.S)
        exist = next(
            row for row in rows if 'data-check="exist"' in row and 'data-status="fail"' in row
        )
        cells = re.findall(r"<td\b.*?</td>", exist, re.S)
        file_cell = next(cell for cell in cells if "data-claim=" in cell)
        self.assertIn("(missing)", file_cell)
        self.assertNotIn("discover-again", page)
        self.assertNotIn(">Re-Discover</a>", page)
        self.assertNotIn(">Re-Discover</button>", page)
        remediated = review_page(
            {"run_result": {"claims": []}, "claims": []},
            None,
            door={
                "repo_id": "alpha",
                "selected_result": "/tmp/run-result_20261120T120000Z.json",
                "review_mode": "remediation",
                "presentation": {"groups": [{"id": "REQ-A", "claims": [claim]}]},
            },
        ).decode()
        self.assertIn(">Re-Discover</button>", remediated)
        self.assertIn('class="discover-again" hidden', remediated)
        self.assertIn(">Find</button>", remediated)
        self.assertLess(remediated.index("<th>Actions</th>"), remediated.index("<th>Comment</th>"))
        self.assertLess(
            remediated.index("<th>Comment</th>"),
            remediated.index("<th>Remediation history</th>"),
        )
        self.assertIn(
            "Find the file first. Re-discover the Claim if that does not work.",
            cells[3],
        )
        self.assertIn('aria-label="Check remediation"', cells[3])
        self.assertNotIn("is absent", page)
        forbidden = [row for row in rows if "Forbidden text</" in row]
        self.assertEqual(len(forbidden), 2)
        absent = next(row for row in forbidden if "matches forbidden pattern" not in row)
        matched = next(row for row in forbidden if "matches forbidden pattern" in row)
        self.assertIn("Find the file first.", absent)
        self.assertIn("Remove the forbidden text.", matched)
        self.assertNotIn("Find the file first.", matched)
        placeholder = next(row for row in rows if "Anti-placeholder</" in row)
        self.assertIn("Replace the placeholder text.", placeholder)
        self.assertIn("contains placeholder text", placeholder)

    def test_an_open_remediation_check_uses_an_actions_menu(self):
        from studio.review.impl.items import check_digest

        missing = {
            "index": 0,
            "check": "exist",
            "status": "fail",
            "edit": "ok",
            "detail": "docs/a.md is absent",
            "args": {"path": "docs/a.md"},
            "paths": [{"path": "docs/a.md", "state": "missing"}],
        }
        present = {
            "index": 1,
            "check": "contents",
            "status": "fail",
            "edit": "none",
            "detail": "placeholder text",
            "args": {"path": "SECURITY.md"},
            "paths": [{"path": "SECURITY.md", "state": "present"}],
        }
        claim = {
            "id": "claim-open",
            "pack_id": "house-policy",
            "recorded_requirement_id": "REQ-A",
            "checks": [missing, present],
        }
        binding = {"id": "claim-stale", "binding": "stale", "checks": []}
        door = {
            "repo_id": "alpha",
            "selected_result": "/tmp/run-result.json",
            "review_mode": "remediation",
            "presentation": {"groups": [{"id": "REQ-A", "claims": [claim, binding]}]},
        }
        page = review_page({"run_result": {"claims": []}, "claims": []}, None, door=door).decode()
        rows = re.findall(r"<tr>(.*?)</tr>", page, re.S)
        exist = next(row for row in rows if 'data-check="exist"' in row)
        contents = next(row for row in rows if 'data-check="contents"' in row)
        bound = next(row for row in rows if 'data-binding="stale"' in row)

        self.assertIn('class="actions-menu"', exist)
        self.assertIn('class="actions-label">Actions</span>', exist)
        self.assertIn('class="actions-panel"', exist)
        labels = ["Find", "Edit check", "Add comment", "Re-check", "Retire"]
        places = [exist.index(f">{label}</button>") for label in labels]
        self.assertEqual(places, sorted(places))
        self.assertIn('data-find-open="find-claim-open-0"', exist)
        self.assertIn("No file named <code>a.md</code>", page)
        self.assertNotIn("does not change the Claim", page)
        self.assertNotIn("data-find-result=", page)
        self.assertIn('data-check-dialog="check-update-claim-open"', exist)
        self.assertIn('data-remedy-comment-open="remedy-comment-claim-open-0"', exist)
        self.assertIn('id="recheck-claim-open-0"', exist)
        self.assertIn('action="/review/recheck"', exist)
        self.assertIn('form="recheck-claim-open-0"', exist)
        self.assertIn('id="retire-claim-open-0"', exist)
        self.assertIn('action="/review/remediate"', exist)
        self.assertIn('name="action" value="retire"', exist)
        self.assertIn('form="retire-claim-open-0"', exist)
        self.assertIn('data-action="retire"', exist)
        panel = re.search(r'<div class="actions-panel".*?</div>', exist, re.S)
        self.assertIsNotNone(panel)
        self.assertIn(">Find</button>", panel.group(0))
        self.assertNotIn('<dialog id="remedy-comment-claim-open-0"', panel.group(0))
        self.assertNotIn('action="/review/recheck"', panel.group(0))
        self.assertNotIn('action="/review/remediate"', panel.group(0))
        self.assertIn('<dialog id="remedy-comment-claim-open-0"', exist)

        self.assertIn('class="actions-menu"', contents)
        self.assertNotIn("data-find-open", contents)
        self.assertNotIn("Edit check", contents)
        self.assertIn(">Add comment</button>", contents)
        self.assertIn(">Re-check</button>", contents)
        self.assertIn('data-action="retire"', contents)
        self.assertNotIn("actions-menu", bound)

        digest = check_digest("exist", {"path": "docs/a.md"})
        mixed = review_page(
            {"run_result": {"claims": []}, "claims": []},
            None,
            door={
                **door,
                "review_items": [
                    {
                        "key": {"claim_id": "claim-open", "check_digest": digest},
                        "decision": "pass",
                    }
                ],
            },
        ).decode()
        mixed_rows = re.findall(r"<tr>(.*?)</tr>", mixed, re.S)
        passed_exist = next(row for row in mixed_rows if 'data-check="exist"' in row)
        still_open = next(row for row in mixed_rows if 'data-check="contents"' in row)
        self.assertNotIn("actions-menu", passed_exist)
        self.assertIn('class="actions-menu"', still_open)
        finished = {
            "id": "claim-fixed",
            "pack_id": "house-policy",
            "recorded_requirement_id": "REQ-A",
            "checks": [missing],
        }
        resolved_page = review_page(
            {"run_result": {"claims": []}, "claims": []},
            None,
            door={
                "repo_id": "alpha",
                "selected_result": "/tmp/run-result.json",
                "review_mode": "remediation",
                "review_items": [
                    {
                        "key": {"claim_id": "claim-fixed", "check_digest": digest},
                        "decision": "pass",
                    }
                ],
                "presentation": {"groups": [{"id": "REQ-A", "claims": [finished]}]},
            },
        ).decode()
        open_list, resolved = resolved_page.split(
            '<section class="deviations-frame" data-resolved="1">', 1
        )
        self.assertIn("No claims need attention.", open_list)
        self.assertNotIn("actions-menu", resolved)
        self.assertNotIn(">Re-check</button>", resolved)

        review = review_page(
            {"run_result": {"claims": []}, "claims": []},
            None,
            door={**door, "review_mode": ""},
        ).decode()
        self.assertNotIn('class="actions-menu"', review)
        signed = review_page(
            {"run_result": {"claims": []}, "claims": []},
            None,
            door={**door, "remedy_signed": True},
        ).decode()
        self.assertNotIn('class="actions-menu"', signed)
        accepted = review_page(
            {
                "run_result": {"claims": []},
                "claims": [],
                "assessments": [
                    {
                        "kind": "check",
                        "claim_id": "claim-open",
                        "claim_digest": "digest-1",
                        "index": 1,
                        "disposition": "accept",
                        "text": "Kept.",
                    }
                ],
            },
            None,
            door={
                **door,
                "review_mode": "",
                "presentation": {
                    "groups": [
                        {
                            "id": "REQ-A",
                            "claims": [{**claim, "digest": "digest-1"}],
                        }
                    ]
                },
            },
        ).decode()
        contents = next(
            row
            for row in re.findall(r"<tr>(.*?)</tr>", accepted, re.S)
            if 'data-check="contents"' in row
        )
        self.assertIn('<option value="accept" selected>Accept</option>', contents)
        self.assertNotIn('<option value="must_fix" selected>', contents)
        self.assertIn("<th>Decisions</th>", page)
        self.assertIn('data-disposition="must_fix">Must be fixed</span>', page)


if __name__ == "__main__":
    unittest.main()
