"""The GitHub Action gates on the packaged checker without changing the product."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "ci" / "curbcheck-action.sh"


class CurbcheckActionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.product = self.root / "product"
        self.product.mkdir()
        self.release = self.root / "release"
        self.release.mkdir()
        self.binary = self.release / "curbcheck-linux-x64"
        self.binary.write_bytes((
            '#!/usr/bin/env bash\n'
            'set -eu\n'
            'test "$1" = "--repo"\n'
            'test "$2" = "$GITHUB_WORKSPACE"\n'
            'test "$3" = "--out"\n'
            'printf \'{"claims":[]}\\n\' > "$4"\n'
            'exit "$CHECK_EXIT"\n'
        ).encode("utf-8"))
        self.write_sums()
        commands = self.root / "bin"
        commands.mkdir()
        curl = commands / "curl"
        curl.write_bytes((
            '#!/usr/bin/env bash\n'
            'set -eu\n'
            'url="$2"\n'
            'cp "$RELEASE_FIXTURE/${url##*/}" "$4"\n'
        ).encode("utf-8"))
        curl.chmod(0o755)
        self.output = self.root / "github-output"
        self.output.touch()
        self.env = dict(
            os.environ,
            PATH=str(commands) + os.pathsep + os.environ["PATH"],
            RELEASE_FIXTURE=self.release.as_posix(),
            CURBCHECK_RELEASE="test-release",
            RUNNER_OS="Linux", RUNNER_ARCH="X64",
            RUNNER_TEMP=self.root.as_posix(),
            GITHUB_WORKSPACE=self.product.as_posix(),
            GITHUB_OUTPUT=self.output.as_posix(), CHECK_EXIT="0",
        )

    def write_sums(self):
        digest = hashlib.sha256(self.binary.read_bytes()).hexdigest()
        (self.release / "SHA256SUMS").write_text(
            f"{digest}  curbcheck-linux-x64\n" + "a" * 64 + "  curbpack-studio-linux-x64\n",
            encoding="utf-8",
        )

    def run_action(self):
        return subprocess.run(
            ["bash", SCRIPT.as_posix()], cwd=self.product, env=self.env,
            capture_output=True, text=True,
        )

    def test_checker_exit_and_result_survive_pass_failure_and_usage_error(self):
        for code in (0, 1, 2):
            with self.subTest(code=code):
                self.output.write_text("")
                self.env["CHECK_EXIT"] = str(code)
                completed = self.run_action()
                self.assertEqual(completed.returncode, code, completed.stderr)
                result = Path(self.output.read_text().strip().split("=", 1)[1])
                self.assertTrue(result.is_file())
                self.assertFalse(result.is_relative_to(self.product))
                self.assertEqual(list(self.product.iterdir()), [])

    def test_changed_binary_is_rejected_before_execution(self):
        self.binary.write_text(self.binary.read_text() + "# changed\n")
        completed = self.run_action()
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("FAILED", completed.stdout)
        self.assertFalse(list(self.root.glob("curbcheck.*/run-result.json")))

    def test_checksum_verification_uses_shasum_when_sha256sum_is_absent(self):
        """macOS runners often lack GNU sha256sum; the action must use shasum instead."""
        shasum = shutil.which("shasum")
        self.assertIsNotNone(shasum, "host needs shasum to exercise the fallback")
        only_shasum = self.root / "only-shasum"
        only_shasum.mkdir()
        (only_shasum / "shasum").symlink_to(shasum)
        path = [str(self.root / "bin"), str(only_shasum)]
        for directory in os.environ["PATH"].split(os.pathsep):
            if not directory or (Path(directory) / "sha256sum").exists():
                continue
            path.append(directory)
        self.env["PATH"] = os.pathsep.join(path)
        completed = self.run_action()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("result=", self.output.read_text())

    def test_checksum_must_name_the_checker(self):
        (self.release / "SHA256SUMS").write_text("a" * 64 + "  another-binary\n")
        self.assertNotEqual(self.run_action().returncode, 0)
        self.assertFalse(list(self.root.glob("curbcheck.*/run-result.json")))

    def test_missing_release_binary_fails_without_a_result(self):
        self.binary.unlink()
        self.assertNotEqual(self.run_action().returncode, 0)
        self.assertFalse(list(self.root.glob("curbcheck.*/run-result.json")))

    def test_unsupported_runner_fails_before_downloading(self):
        self.env["RUNNER_ARCH"] = "ARM64"
        self.assertNotEqual(self.run_action().returncode, 0)
        self.assertEqual(self.output.read_text(), "")

    def test_local_action_requires_an_explicit_release(self):
        self.env["CURBCHECK_RELEASE"] = ""
        self.assertNotEqual(self.run_action().returncode, 0)
        self.assertEqual(self.output.read_text(), "")
