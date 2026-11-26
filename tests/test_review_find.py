"""Find lists every same-named path. OK writes that path, signs the Claim, and re-checks it."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from claims.bind import build_claim, write_claim
from common.jsonio import read_json
from common.store import load_claim
from common.validate import validate_requirement
from studio.review.impl.items import check_digest, load_items, write_items
from studio.review.review_page import _find_dialog, review_page
from tests.test_rev03_review import _get, _pack, _post, _post_redirect, _requirement, _serve, _workspace


def _claim(path: str) -> dict:
    return build_claim(
        claim_id="claim-moved",
        requirement=validate_requirement(_requirement("REQ-A")),
        source="documents",
        args={"path": path},
        checks=[
            {"check": "exist", "args": {"paths": [path]}},
            {
                "check": "contents",
                "args": {"path": path, "probes": [{"kind": "size", "bytes": 1, "op": ">="}]},
            },
        ],
        description="The security file is the evidence.",
    )


class FindDialogTest(unittest.TestCase):
    def test_the_dialog_offers_each_path_and_ok_submits_it(self):
        dialog = _find_dialog(
            "find-1",
            "SECURITY.md",
            [("docs/SECURITY.md", "# Security\n"), ("notes/SECURITY.md", "plain")],
            '<input type="hidden" name="claim_id" value="claim-moved">',
        )
        self.assertIn('action="/review/find"', dialog)
        self.assertIn('type="radio" name="path" value="docs/SECURITY.md"', dialog)
        self.assertIn('type="radio" name="path" value="notes/SECURITY.md"', dialog)
        self.assertIn('data-find-preview="find-1-preview-0"', dialog)
        self.assertIn("# Security", dialog)
        self.assertIn('name="name"', dialog)
        self.assertIn(">OK</button>", dialog)
        self.assertIn('data-find-name="SECURITY.md"', dialog)
        self.assertNotIn("does not change the Claim", dialog)

        empty = _find_dialog("find-2", "SECURITY.md", [], "")
        self.assertIn("No file named <code>SECURITY.md</code>", empty)
        self.assertIn('action="/review/find"', empty)
        self.assertIn("data-find-submit hidden", empty)

    def test_a_passed_retarget_moves_the_requirement_and_shows_both_paths(self):
        old = check_digest("exist", {"paths": ["SECURITY.md"]})
        new = check_digest("exist", {"paths": ["docs/SECURITY.md"]})
        claim = {
            "id": "claim-moved",
            "recorded_requirement_id": "REQ-A",
            "checks": [
                {
                    "index": 0,
                    "check": "exist",
                    "status": "fail",
                    "detail": "SECURITY.md is absent",
                    "args": {"paths": ["SECURITY.md"]},
                    "paths": [{"path": "SECURITY.md", "state": "missing"}],
                }
            ],
        }
        door = {
            "repo_id": "alpha",
            "selected_result": "/tmp/run-result.json",
            "review_mode": "remediation",
            "review_items": [
                {
                    "key": {"claim_id": "claim-moved", "check_digest": new},
                    "decision": "pass",
                    "remediation_history": [
                        {
                            "date": "2026-11-24T15:00:00Z",
                            "remediation": "SECURITY.md -> docs/SECURITY.md",
                            "action": "retarget",
                            "name": "Ada",
                            "old_check_digest": old,
                        }
                    ],
                }
            ],
            "presentation": {"groups": [{"id": "REQ-A", "claims": [claim]}]},
        }
        page = review_page({"run_result": {"claims": []}, "claims": []}, None, door=door).decode()
        open_section, resolved = page.split('data-resolved="1"', 1)
        self.assertNotIn("claim-moved", open_section.split('data-deviations="1"', 1)[1])
        self.assertIn("Ada SECURITY.md -&gt; docs/SECURITY.md", resolved)
        self.assertNotIn('class="actions-menu"', resolved.split("</section>", 1)[0])

    def test_a_retargeted_pass_wins_over_the_old_check_and_drops_the_stale_remedy(self):
        from studio.review.impl.items import check_digest

        old = check_digest("contents", {"path": "SECURITY.md"})
        new = check_digest("contents", {"path": "docs/SECURITY.md"})
        claim = {
            "id": "claim-moved",
            "recorded_requirement_id": "REQ-A",
            "checks": [
                {
                    "index": 0,
                    "check": "contents",
                    "status": "fail",
                    "detail": "SECURITY.md is absent",
                    "args": {"path": "SECURITY.md"},
                    "paths": [{"path": "SECURITY.md", "state": "missing"}],
                }
            ],
        }
        door = {
            "repo_id": "alpha",
            "selected_result": "/tmp/run-result.json",
            "review_mode": "remediation",
            "review_items": [
                {
                    "key": {"claim_id": "claim-moved", "check_digest": old},
                    "decision": "not_assessed",
                },
                {
                    "key": {"claim_id": "claim-moved", "check_digest": new},
                    "decision": "pass",
                    "remediation_history": [
                        {
                            "date": "2026-11-24T15:00:00Z",
                            "remediation": "SECURITY.md -> docs/SECURITY.md",
                            "action": "retarget",
                            "old_check_digest": old,
                        }
                    ],
                },
            ],
            "presentation": {"groups": [{"id": "REQ-A", "claims": [claim]}]},
        }
        page = review_page({"run_result": {"claims": []}, "claims": []}, None, door=door).decode()
        _open, resolved = page.split('data-resolved="1"', 1)
        self.assertIn('data-status="pass"', resolved)
        self.assertNotIn("Find the file first", resolved)


class FindFilesNowTest(unittest.TestCase):
    def test_opening_find_reads_a_file_created_after_the_page(self):
        import json

        with tempfile.TemporaryDirectory() as tmp:
            workspace, repo = _workspace("Alpha", Path(tmp) / "alpha")
            with _serve(workspace) as base:
                (repo / "SECURITY.md").write_text("now\n", encoding="utf-8")
                body = _get(base + "/review/find-files?repo_id=alpha&name=SECURITY.md")
            payload = json.loads(body)
            self.assertEqual([row["path"] for row in payload["paths"]], ["SECURITY.md"])
            self.assertEqual(payload["paths"][0]["text"], "now\n")


class FindAdoptTest(unittest.TestCase):
    def test_ok_signs_the_new_path_rechecks_it_and_records_both_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace, repo = _workspace("Alpha", Path(tmp) / "alpha")
            _pack(repo, "REQ-A")
            claim = _claim("SECURITY.md")
            write_claim(repo / "kept" / "claims", claim)
            (repo / "docs").mkdir()
            (repo / "docs" / "SECURITY.md").write_text("# Security\n\nA real note.\n", encoding="utf-8")
            (repo / "notes").mkdir()
            (repo / "notes" / "SECURITY.md").write_text("# Other\n", encoding="utf-8")
            run_dir = repo / "runs" / "out" / "run-result_20261124T150000Z"
            source = run_dir / "run-result.json"
            source.parent.mkdir(parents=True)
            from common.jsonio import write_json

            write_json(
                source,
                {
                    "tool": "curbcheck",
                    "tool_version": "0",
                    "packs": [{"id": "house", "version": "0.1.0", "digest": "abc"}],
                    "claims": [
                        {
                            "id": "claim-moved",
                            "digest": "digest",
                            "status": "fail",
                            "checks": [
                                {
                                    "index": 0,
                                    "check": "exist",
                                    "args": claim["checks"][0]["args"],
                                    "status": "fail",
                                    "detail": "SECURITY.md is absent",
                                },
                                {
                                    "index": 1,
                                    "check": "contents",
                                    "args": claim["checks"][1]["args"],
                                    "status": "fail",
                                    "detail": "SECURITY.md is absent",
                                },
                            ],
                        }
                    ],
                },
            )
            exist = check_digest("exist", claim["checks"][0]["args"])
            contents = check_digest("contents", claim["checks"][1]["args"])
            write_items(
                run_dir / "review_items.json",
                [
                    {"key": {"claim_id": "claim-moved", "check_digest": exist}, "decision": "must_fix"},
                    {"key": {"claim_id": "claim-moved", "check_digest": contents}, "decision": "must_fix"},
                ],
                marker={"review_locked": True},
            )
            fields = {
                "repo_id": "alpha",
                "source": str(source),
                "claim_id": "claim-moved",
                "check_digest": exist,
                "path": "docs/SECURITY.md",
                "name": "Ada",
            }
            with _serve(workspace) as base:
                refused = _post(base + "/review/find", {**fields, "name": ""})
                self.assertIn("signer name", refused)
                rejected = _post(base + "/review/find", {**fields, "path": "README.md"})
                self.assertIn("a file this search found", rejected)
                location = _post_redirect(base + "/review/find", fields)
            self.assertIn("mode=remediation", location)
            stored = load_claim(repo / "kept" / "claims" / "claim-moved.json")
            self.assertEqual(stored["args"]["path"], "docs/SECURITY.md")
            self.assertEqual(stored["checks"][0]["args"]["paths"], ["docs/SECURITY.md"])
            self.assertEqual(stored["checks"][1]["args"]["path"], "docs/SECURITY.md")
            self.assertEqual(stored["signed"]["name"], "Ada")
            items = load_items(run_dir / "review_items.json")
            self.assertEqual([item["decision"] for item in items], ["pass", "pass"])
            notes = [
                entry.get("remediation")
                for item in items
                for entry in item.get("remediation_history") or []
            ]
            self.assertEqual(notes.count("SECURITY.md -> docs/SECURITY.md"), 2)
            self.assertTrue(
                all(
                    entry.get("name") == "Ada"
                    for item in items
                    for entry in item.get("remediation_history") or []
                    if entry.get("action") == "retarget"
                )
            )
            self.assertEqual(
                {item["remediation_history"][0]["old_check_digest"] for item in items},
                {exist, contents},
            )
            self.assertEqual(read_json(repo / "kept" / "claims" / "claim-moved.json")["signed"]["name"], "Ada")
