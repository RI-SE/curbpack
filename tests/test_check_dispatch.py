"""curbcheck runs the command named in the registry."""

from __future__ import annotations

import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from checks.dispatch import run_check_tool
from checks.run import run_claim
from claims.bind import build_claim


def _claim(checks: list[dict]) -> dict:
    return build_claim(
        claim_id="claim-dispatch",
        requirement_id="CRA-ANNEX-VII-RISK",
        source="documents",
        args={"path": "docs/a.md"},
        checks=checks,
        description="The reviewed file is the evidence for this Requirement.",
        severity="high",
    )


class DispatchTest(unittest.TestCase):
    def test_a_separate_executable_receives_the_check_id_repo_and_args(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seen = root / "seen.json"
            script = root / "curbcheck-probe"
            script.write_text(
                "#!/bin/sh\n"
                "printf '%s\\n' \"$1\" > \"$CURBCHECK_SEEN\"\n"
                "printf '%s\\n' \"$3\" >> \"$CURBCHECK_SEEN\"\n"
                "printf '%s\\n' \"$5\" >> \"$CURBCHECK_SEEN\"\n"
                "printf '%s\\n' '{\"status\":\"fail\",\"detail\":\"probe says no\"}'\n"
            )
            script.chmod(script.stat().st_mode | stat.S_IXUSR)
            os.environ["CURBCHECK_SEEN"] = str(seen)
            try:
                result = run_check_tool(root, str(script), "demo", {"path": "notes[1].md"})
            finally:
                os.environ.pop("CURBCHECK_SEEN", None)
            self.assertEqual(result, {"status": "fail", "detail": "probe says no"})
            check_id, repo, payload = seen.read_text(encoding="utf-8").splitlines()
            self.assertEqual(check_id, "demo")
            self.assertEqual(repo, str(root))
            self.assertEqual(json.loads(payload), {"path": "notes[1].md"})

    def test_a_tool_that_exits_without_a_result_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "curbcheck-crash"
            script.write_text("#!/bin/sh\nexit 2\n")
            script.chmod(script.stat().st_mode | stat.S_IXUSR)
            result = run_check_tool(root, str(script), "demo", {"path": "a.md"})
            self.assertEqual(result["status"], "fail")
            self.assertIn("failed", result["detail"])

    def test_a_missing_tool_fails_and_the_next_registered_check_still_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "a.md").write_text("hello\n", encoding="utf-8")
            result = run_claim(
                root,
                _claim(
                    [
                        {"check": "fresh", "args": {"path": "docs/a.md", "max_age_days": 2}},
                        {"check": "exist", "args": {"paths": ["docs/a.md"]}},
                    ]
                ),
            )
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["checks"][0]["status"], "fail")
        self.assertIn("curbcheck-fresh", result["checks"][0]["detail"])
        self.assertIn("unavailable", result["checks"][0]["detail"])
        self.assertEqual(result["checks"][1], {"index": 1, "check": "exist", "args": {"paths": ["docs/a.md"]}, "status": "pass"})
        self.assertNotIn("detail", result["checks"][1])

    def test_a_symlink_out_of_the_repo_fails_and_the_next_check_still_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            (repo / "docs").mkdir(parents=True)
            (repo / "docs" / "allowed.md").write_text("inside\n", encoding="utf-8")
            secret = base / "private.md"
            secret.write_text("OUTSIDE_SECRET\n", encoding="utf-8")
            (repo / "docs" / "link.md").symlink_to(secret)
            result = run_claim(
                repo,
                _claim(
                    [
                        {"check": "exist", "args": {"paths": ["docs/link.md"]}},
                        {"check": "exist", "args": {"paths": ["docs/allowed.md"]}},
                    ]
                ),
            )
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["checks"][0]["status"], "fail")
        self.assertNotIn("OUTSIDE_SECRET", result["checks"][0]["detail"])
        self.assertEqual(
            result["checks"][1],
            {"index": 1, "check": "exist", "args": {"paths": ["docs/allowed.md"]}, "status": "pass"},
        )
