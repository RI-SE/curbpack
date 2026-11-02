"""Host packaging, checksum verification, and the CI check runner."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "build"))
sys.path.insert(0, str(ROOT / "scripts" / "release"))

from package_common import host_label  # noqa: E402
from verify import verify_directory  # noqa: E402

import common.paths as paths  # noqa: E402


class HostPackageTest(unittest.TestCase):
    def test_labels_supported_build_hosts_and_refuses_to_cross_compile(self):
        self.assertEqual(host_label("Darwin", "arm64"), "macos-arm64")
        self.assertEqual(host_label("Windows", "AMD64"), "windows-x64")
        self.assertEqual(host_label("Linux", "x86_64"), "linux-x64")
        with self.assertRaises(SystemExit) as caught:
            host_label("Linux", "aarch64")
        self.assertIn("is not", str(caught.exception))
        with self.assertRaises(SystemExit):
            host_label("Darwin", "x86_64")


class VerifyReleaseTest(unittest.TestCase):
    def test_matching_sha256_passes_and_a_changed_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            binary = directory / "curbpack-studio-macos-arm64"
            binary.write_bytes(b"pilot-bytes")
            digest = hashlib.sha256(b"pilot-bytes").hexdigest()
            (directory / "SHA256SUMS").write_text(f"{digest}  {binary.name}\n", encoding="utf-8")
            self.assertEqual(verify_directory(directory), 0)
            binary.write_bytes(b"rebuilt-bytes")
            self.assertEqual(verify_directory(directory), 1)


class FrozenWorkspaceTest(unittest.TestCase):
    def test_frozen_workspace_stays_outside_the_bundle(self):
        with patch.object(paths.sys, "frozen", True, create=True), patch.object(
            paths.sys, "_MEIPASS", "/tmp/curbpack-bundle", create=True
        ):
            self.assertEqual(paths.install_root(), Path("/tmp/curbpack-bundle"))
            workspace = paths.default_workspace()
            self.assertFalse(str(workspace).startswith("/tmp/curbpack-bundle"))
            self.assertEqual(workspace, Path.home() / "curbpack-studio" / "workspace")


class CicdTargetTest(unittest.TestCase):
    commands = [
        "scripts/ci/checks/tests.py",
        "-m unittest tests.test_installers",
        "scripts/build/package_installers.py",
        "scripts/build/package_studio.py",
        "scripts/build/package_curbcheck.py",
    ]

    def run_cicd(self, fail_command=""):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            log = directory / "commands.log"
            python = directory / "python"
            python.write_text(
                "#!/bin/sh\n"
                'printf "%s\\n" "$*" >> "$CICD_COMMAND_LOG"\n'
                'if [ "$*" = "$CICD_FAIL_COMMAND" ]; then exit 1; fi\n',
                encoding="utf-8",
            )
            python.chmod(0o755)
            completed = subprocess.run(
                ["make", "--no-print-directory", "cicd", f"PYTHON={python}"],
                cwd=ROOT,
                env=dict(os.environ, CICD_COMMAND_LOG=str(log),
                         CICD_FAIL_COMMAND=fail_command, ONLY="tests"),
                capture_output=True, text=True,
            )
            commands = log.read_text().splitlines() if log.exists() else []
            return completed, commands

    def test_cicd_runs_all_pr_operations_even_with_only_in_environment(self):
        completed, commands = self.run_cicd()
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(commands, self.commands)

    def test_cicd_fails_when_any_pr_operation_fails(self):
        for index, command in enumerate(self.commands):
            with self.subTest(command=command):
                completed, commands = self.run_cicd(fail_command=command)
                self.assertNotEqual(completed.returncode, 0)
                self.assertEqual(commands, self.commands[:index + 1])


def _ci_tests():
    path = ROOT / "scripts" / "ci" / "checks" / "tests.py"
    spec = importlib.util.spec_from_file_location("ci_check_tests", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class QuietCiReportTest(unittest.TestCase):
    def test_a_passing_quiet_check_stays_one_line(self):
        ci = _ci_tests()

        class Sample(unittest.TestCase):
            def test_ok(self):
                self.assertTrue(True)

        result = ci._Result()
        unittest.defaultTestLoader.loadTestsFromTestCase(Sample).run(result)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = ci.report(result, quiet=True)
        text = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertEqual(text.count("\n"), 1)
        self.assertIn("[PASS]", text)
        self.assertNotIn("Traceback", text)

    def test_a_failing_check_prints_the_traceback_and_captured_output_in_both_modes(self):
        ci = _ci_tests()

        class Sample(unittest.TestCase):
            def test_ok(self):
                self.assertTrue(True)

            def test_bad(self):
                print("marker-from-stdout")
                print("marker-from-stderr", file=sys.stderr)
                self.assertEqual(1, 2)

        result = ci._Result()
        unittest.defaultTestLoader.loadTestsFromTestCase(Sample).run(result)
        for quiet in (True, False):
            with self.subTest(quiet=quiet):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    code = ci.report(result, quiet=quiet)
                text = buf.getvalue()
                self.assertEqual(code, 1)
                self.assertIn("[FAIL]", text)
                self.assertIn("FAIL:", text)
                self.assertIn("Traceback (most recent call last):", text)
                self.assertRegex(text, r'File "[^"]*test_delivery\.py", line \d+, in test_bad')
                self.assertIn("AssertionError: 1 != 2", text)
                self.assertIn("marker-from-stdout", text)
                self.assertIn("marker-from-stderr", text)
                self.assertIn("Summary: 1 PASS, 1 FAIL", text)
                self.assertNotIn("test_ok", text.split("FAIL:", 1)[-1])

    def test_a_large_difference_is_printed_in_full(self):
        ci = _ci_tests()
        expected = [f"expected-{index}" for index in range(100)]
        actual = [f"actual-{index}" for index in range(100)]

        class Sample(unittest.TestCase):
            def test_bad(self):
                self.assertEqual(actual, expected)

        result = ci._Result()
        unittest.defaultTestLoader.loadTestsFromTestCase(Sample).run(result)
        for quiet in (True, False):
            with self.subTest(quiet=quiet):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    code = ci.report(result, quiet=quiet)
                text = buf.getvalue()
                self.assertEqual(code, 1)
                self.assertIn("actual-99", text)
                self.assertIn("expected-99", text)
                self.assertNotIn("Set self.maxDiff to None", text)

    def test_an_unexpected_exception_preserves_its_cause_and_output(self):
        ci = _ci_tests()
        body = "response-body-start\n" + "x" * 1000 + "\nresponse-body-end"

        class Sample(unittest.TestCase):
            def test_error(self):
                print("server-log", file=sys.stderr)
                try:
                    raise ValueError(body)
                except ValueError as exc:
                    raise RuntimeError("request failed") from exc

        result = ci._Result()
        unittest.defaultTestLoader.loadTestsFromTestCase(Sample).run(result)
        for quiet in (True, False):
            with self.subTest(quiet=quiet):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    code = ci.report(result, quiet=quiet)
                text = buf.getvalue()
                self.assertEqual(code, 1)
                self.assertIn("ERROR:", text)
                self.assertIn(body, text)
                self.assertIn("RuntimeError: request failed", text)
                self.assertIn("server-log", text)
                self.assertRegex(text, r'File "[^"]*test_delivery\.py", line \d+, in test_error')
