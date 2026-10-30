"""Focused Review rendering structure for REV-03 presentation correction.

Does not rewrite contract or scenario tests. Asserts the PoC-shaped layout:
topline, requirement cards, Path/Checks table, check pills, actions, and
Technical details for raw args / full seal dump.
"""

from __future__ import annotations

import re
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
    _summary,
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

            self.assertIn('class="card topline"', page)
            self.assertIn("review-board", page)
            self.assertIn("need attention", page.lower())

            failed_group = _details(page, "REQ-FAIL")
            self.assertIn(" open", failed_group[: failed_group.index(">") + 1])
            self.assertIn("card", failed_group[: failed_group.index(">") + 1])
            self.assertIn('class="note"', failed_group)
            self.assertIn("broke here", failed_group)
            self.assertIn("<th>Path</th>", failed_group)
            self.assertIn("<th>Checks</th>", failed_group)
            self.assertIn('class="check fail"', failed_group)
            self.assertIn('class="actions"', failed_group)
            self.assertIn("Technical details", failed_group)
            self.assertIn('class="technical"', failed_group)
            # Raw args live under Technical details, not as a primary dump beside the pill.
            tech = failed_group[failed_group.index('class="technical"') :]
            self.assertIn("&quot;paths&quot;", tech)
            primary = failed_group[: failed_group.index('class="technical"')]
            self.assertNotIn("&quot;paths&quot;", primary)
            self.assertNotIn('"paths"', primary)

            passed_group = _details(page, "REQ-PASS")
            self.assertIsNone(
                re.search(r'<details[^>]*data-requirement="REQ-PASS"[^>]*\bopen\b', page)
            )
            self.assertIn("REQ-PASS", _summary(page, "REQ-PASS"))
            self.assertIn("Result pass", _summary(page, "REQ-PASS"))

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


if __name__ == "__main__":
    unittest.main()
