"""A Check run leaves a signed Review report where it was."""

from __future__ import annotations

import subprocess
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from checks.run import run_and_write
from common.jsonio import read_json, write_json
from common.keystore import load_or_create_key, trust_store
from common.store import load_requirement
from demo_setup import prepare_demo
from review.compile import compile_report, read_report_signature, record_decision, sign_report

class CheckKeepsSignedReportTest(unittest.TestCase):
    def test_post_check_does_not_delete_a_signed_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepare_demo(root)
            ws = Workspace(root)
            result, _code = run_and_write(ws.repo, ws.packs, ws.run_path)
            report = compile_report(
                run_result=result,
                requirements=[load_requirement(ws.requirement_path())],
                claims=[],
            )
            private, _public = load_or_create_key(ws.keys, "Ada Reviewer")
            sealed = sign_report(
                record_decision(report, "I read this run. I am not saying the product meets CRA."),
                name="Ada Reviewer",
                private_key=private,
                at="2026-10-21T12:00:00Z",
            )
            write_json(ws.report_path, sealed)
            before = ws.report_path.read_bytes()

            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ws))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                _post(base + "/check", {})
                self.assertTrue(ws.report_path.is_file())
                self.assertEqual(ws.report_path.read_bytes(), before)
                reading = read_report_signature(read_json(ws.report_path), trust_store(ws.keys))
                self.assertTrue(reading["verifiable"])
                self.assertEqual(reading["who"], "Ada Reviewer")
                review = _get(base + "/review")
                self.assertIn("I read this run", review)
            finally:
                httpd.shutdown()
                httpd.server_close()


class CompileReplacesOnlyAfterConfirmationTest(unittest.TestCase):
    def test_a_later_run_stays_distinct_until_compile_is_confirmed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepare_demo(root)
            ws = Workspace(root)
            head = _git(ws.repo, "rev-parse", "HEAD")
            run_and_write(ws.repo, ws.packs, ws.run_path)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ws))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                _post(base + "/review/compile", {})
                _post(base + "/review", {"decision": "I read the first run. I am not saying the product meets CRA."})
                _post(base + "/review/sign", {"name": "Ada Reviewer"})
                signed = ws.report_path.read_bytes()
                (ws.repo / "docs" / "notes.md").write_text("uncommitted\n", encoding="utf-8")
                _post(base + "/check", {})
                self.assertEqual(ws.report_path.read_bytes(), signed)
                self.assertEqual(_git(ws.repo, "rev-parse", "HEAD"), head)
                self.assertFalse((ws.repo / ".curbpack" / "review-report.json").exists())
                review = _get(base + "/review")
                self.assertIn('data-same-run="no"', review)
                self.assertIn("older run", review)
                self.assertIn("I read the first run", review)
                self.assertIn("verifiable yes", review.lower())
                try:
                    _post(base + "/review/compile", {})
                    self.fail("replacing a saved report requires confirmation")
                except urllib.error.HTTPError as exc:
                    self.assertEqual(exc.code, 400)
                self.assertEqual(ws.report_path.read_bytes(), signed)
                self.assertEqual(_git(ws.repo, "rev-parse", "HEAD"), head)
                replaced = _post(base + "/review/compile", {"confirm": "yes"})
                self.assertNotIn("I read the first run", replaced)
                self.assertIn('data-same-run="yes"', replaced)
                self.assertIn("unsigned", replaced.lower())
                loaded = read_json(ws.report_path)
                self.assertNotIn("decision", loaded)
                self.assertNotIn("signed", loaded)
                self.assertEqual(_git(ws.repo, "rev-parse", "HEAD"), head)
            finally:
                httpd.shutdown()
                httpd.server_close()


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def _get(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def _post(url: str, form: dict) -> str:
    data = urllib.parse.urlencode(form).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(request) as response:
        return response.read().decode("utf-8")


if __name__ == "__main__":
    unittest.main()
