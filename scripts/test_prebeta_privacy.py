#!/usr/bin/env python3
"""Behavioral privacy regression for the generic prepared-example runner."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


class PreparedExamplePrivacy(unittest.TestCase):
    def test_personal_git_settings_do_not_reach_fixture_or_feedback(self):
        with tempfile.TemporaryDirectory(prefix="curbpack-privacy-") as tmp:
            work = Path(tmp)
            hook_dir = work / "hooks"
            hook_dir.mkdir()
            marker = work / "hook-executed"
            hook = hook_dir / "pre-commit"
            hook.write_text("#!/bin/sh\ntouch " + shlex.quote(str(marker)) + "\n")
            hook.chmod(0o755)
            config = work / "gitconfig"
            config.write_text(
                '[core]\n hooksPath = "' + str(hook_dir) + '"\n'
                '[user]\n name = PRIVACY_SENTINEL_PERSON\n'
                ' email = privacy-sentinel@example.invalid\n'
            )
            env = dict(os.environ)
            env.update(
                GIT_CONFIG_GLOBAL=str(config),
                GIT_AUTHOR_NAME="PRIVACY_SENTINEL_PERSON",
                GIT_AUTHOR_EMAIL="privacy-sentinel@example.invalid",
                GIT_COMMITTER_NAME="PRIVACY_SENTINEL_PERSON",
                GIT_COMMITTER_EMAIL="privacy-sentinel@example.invalid",
                GIT_DIR=str(work / "unrelated-repository"),
                CURBPACK_TEST_RUNS_DIR=str(work / "runs"),
            )
            result = subprocess.run(
                ["bash", str(ROOT / "scripts/test-prebeta.sh")],
                cwd=Path.home(), env=env, capture_output=True, text=True, timeout=300,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(marker.exists(), "personal Git hook executed")
            runs = list((work / "runs").glob("run.*"))
            self.assertEqual(len(runs), 1)
            run = runs[0]
            self.assertEqual(run.stat().st_mode & 0o077, 0)
            authors = subprocess.check_output(
                ["git", "log", "--format=%an <%ae> %cn <%ce>"],
                cwd=run / "example", text=True,
            )
            self.assertNotIn("PRIVACY_SENTINEL_PERSON", authors)
            self.assertNotIn("privacy-sentinel@example.invalid", authors)
            for name in ["feedback.txt", "START-HERE.txt"]:
                path = run / name
                text = path.read_text()
                for forbidden in [str(Path.home()), str(ROOT), str(work),
                                  "PRIVACY_SENTINEL_PERSON", "privacy-sentinel@example.invalid"]:
                    self.assertNotIn(forbidden, text, name)
                self.assertEqual(path.stat().st_mode & 0o077, 0, name)
            for path in (run / "recipient/review-pack").rglob("*"):
                if path.is_file():
                    self.assertNotIn(b"PRIVACY_SENTINEL_PERSON", path.read_bytes(), path.name)
            audit = json.loads((run / "06-review.json").read_text())["pack_audit"]
            self.assertEqual(audit["integrity"]["status"], "verified")
            self.assertEqual(audit["completeness"]["status"], "verified")


if __name__ == "__main__":
    unittest.main()
