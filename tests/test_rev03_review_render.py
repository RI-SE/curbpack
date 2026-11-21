"""Review queue rendering: attention rows, check pills, and secondary details."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from common.jsonio import write_json
from claims.bind import write_claim

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
            self.assertIn("<th>Verdict</th>", page)
            self.assertIn("1 claim · 1 deviation", page)

            failed_group = _details(page, "REQ-FAIL")
            self.assertIn("broke here", failed_group)
            self.assertIn('class="check fail"', failed_group)
            self.assertIn("bad.md", failed_group)
            self.assertNotIn("Technical details", failed_group)
            self.assertNotIn("&quot;paths&quot;", failed_group)
            self.assertIn("Technical details", page)
            self.assertIn("&quot;paths&quot;", page.split('<section data-secondary>', 1)[1])

            self.assertNotIn('data-requirement="REQ-PASS"', page)
            self.assertNotIn("passed-note", page.split('<section data-secondary>', 1)[0])

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
            self.assertIn('class="check pass" title="File is present">Exists · pass<', group)
            self.assertIn(
                'class="check fail" title="File has the expected content">Contents · fail<',
                group,
            )
            self.assertIn(
                'class="check fail" title="File must not contain this text">Forbidden text · fail<',
                group,
            )
            self.assertIn(
                'class="check skipped" title="File is not a placeholder">Anti-placeholder · skipped<',
                group,
            )
            self.assertIn('class="check pass" title="File is recent enough">Fresh · pass<', group)
            self.assertIn('class="check pass" title="Written by the claimed author">Owned · pass<', group)
            self.assertIn('class="check fail" title="Banned package version">Banned · fail<', group)
            self.assertIn('class="check fail" title="custom_probe">custom_probe · fail<', group)
            self.assertIn("too short", group)
            self.assertIn("Add a paragraph.", group)
            self.assertIn("found TODO", group)
            self.assertNotIn('title="too short"', group)
            self.assertNotIn('title="Add a paragraph."', group)
            self.assertNotIn(">File is present ·", group)


if __name__ == "__main__":
    unittest.main()
