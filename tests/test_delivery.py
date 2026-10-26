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

from package import host_label  # noqa: E402
from verify import verify_directory  # noqa: E402

import common.paths as paths  # noqa: E402


class HostPackageTest(unittest.TestCase):
    def test_labels_the_two_pilot_hosts_and_refuses_to_cross_compile(self):
        self.assertEqual(host_label("Darwin", "arm64"), "macos-arm64")
        self.assertEqual(host_label("Windows", "AMD64"), "windows-x64")
        with self.assertRaises(SystemExit) as caught:
            host_label("Linux", "x86_64")
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


class CiRunnerTest(unittest.TestCase):
    def test_unknown_only_fails_and_lists_the_checks(self):
        env = dict(os.environ)
        env["ONLY"] = "docker"
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "ci" / "run.py")],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("[FAIL] unknown ONLY=docker", completed.stdout)
        self.assertIn("tests", completed.stdout)


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

    def test_a_failing_quiet_check_prints_the_traceback_and_captured_output(self):
        ci = _ci_tests()

        class Sample(unittest.TestCase):
            def test_ok(self):
                self.assertTrue(True)

            def test_bad(self):
                print("marker-from-stdout")
                self.assertEqual(1, 2)

        result = ci._Result()
        unittest.defaultTestLoader.loadTestsFromTestCase(Sample).run(result)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = ci.report(result, quiet=True)
        text = buf.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("[FAIL]", text)
        self.assertIn("FAIL:", text)
        self.assertIn("AssertionError: 1 != 2", text)
        self.assertIn("marker-from-stdout", text)
        self.assertIn("Summary: 1 PASS, 1 FAIL", text)
        self.assertNotIn("test_ok", text.split("FAIL:", 1)[-1])
