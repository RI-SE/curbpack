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
            self.assertIn("<th>Verdict</th>", page)
            self.assertIn("2 claims · 1 deviation", page)

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
            self.assertIn('class="check pass"', group)
            self.assertIn('class="check fail"', group)
            self.assertIn('class="check skipped"', group)
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
            self.assertIn('class="check pass" title="File is present"><svg class="mark"', group)
            self.assertIn('aria-label="pass"', group)
            self.assertIn('d="M20 6 9 17l-5-5"', group)
            self.assertIn("</svg>Exists</span>", group)
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
            self.assertIn('class="check pass" title="File is recent enough"><svg class="mark"', group)
            self.assertIn("</svg>Fresh</span>", group)
            self.assertIn(
                'class="check pass" title="Written by the claimed author"><svg class="mark"',
                group,
            )
            self.assertIn("</svg>Owned</span>", group)
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
        self.assertNotIn('<section data-resolved="1">', page)
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
        open_list, resolved = page.split('<section data-resolved="1">', 1)
        self.assertIn("No claims need attention.", open_list)
        self.assertNotIn("claim-fixed", open_list)
        self.assertIn('data-claim="claim-fixed"', resolved)
        self.assertIn('data-status="pass"', resolved)
        self.assertIn('class="check pass"', resolved)
        self.assertNotIn("Re-check", resolved)
        self.assertIn("must_fix -&gt; pass", resolved)
        self.assertNotIn(">Re-check</button>", resolved)

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
        open_list, resolved = page.split('<section data-resolved="1">', 1)
        self.assertIn("No claims need attention.", open_list)
        self.assertNotIn('data-claim="claim-stale"', open_list)
        self.assertIn('data-claim="claim-stale"', resolved)
        self.assertIn('class="check pass"', resolved)
        self.assertIn("Rebound the Claim.", resolved)
        self.assertNotIn('class="check fail"', resolved)
        self.assertNotIn(">Rebind and Sign</button>", resolved)

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
        self.assertNotIn('<section data-resolved="1">', page)
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


if __name__ == "__main__":
    unittest.main()
