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
from checks.run import reports_dir, results_dir, run_and_write
from common.jsonio import read_json, write_json
from common.keystore import load_or_create_key, trust_store
from common.store import load_requirement
from common.validate import validate_curbpack_config
from demo_setup import prepare_demo
from review.compile import compile_report, read_report_signature, record_decision, sign_report

class CheckKeepsSignedReportTest(unittest.TestCase):
    def test_post_check_does_not_delete_a_signed_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepare_demo(root)
            ws = Workspace(root)
            config = validate_curbpack_config(read_json(ws.repo / "curbpack.json"))
            run_path = results_dir(ws.repo, config) / "run-result_20261021T120000Z.json"
            result, _code = run_and_write(ws.repo, None, run_path)
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
            report_path = reports_dir(ws.repo, config) / "review-report_20261021T120000Z.json"
            write_json(report_path, sealed)
            before = report_path.read_bytes()

            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ws))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                _post(base + "/check", {"repo_id": "sample-product", "action": "check"})
                self.assertTrue(report_path.is_file())
                self.assertEqual(report_path.read_bytes(), before)
                reading = read_report_signature(read_json(report_path), trust_store(ws.keys))
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
            config = validate_curbpack_config(read_json(ws.repo / "curbpack.json"))
            head = _git(ws.repo, "rev-parse", "HEAD")
            run_and_write(ws.repo, None, results_dir(ws.repo, config) / "run-result_20261021T120000Z.json")
            reports = reports_dir(ws.repo, config)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ws))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                _post(base + "/review/compile", {"repo_id": "sample-product"})
                _post(base + "/review", {"decision": "I read the first run. I am not saying the product meets CRA."})
                _post(base + "/review/sign", {"name": "Ada Reviewer"})
                first = sorted(reports.glob("review-report_*.json"))[0]
                signed = first.read_bytes()
                (ws.repo / "docs" / "notes.md").write_text("uncommitted\n", encoding="utf-8")
                _post(base + "/check", {"repo_id": "sample-product", "action": "check"})
                self.assertEqual(first.read_bytes(), signed)
                self.assertEqual(_git(ws.repo, "rev-parse", "HEAD"), head)
                self.assertFalse((ws.repo / ".curbpack" / "review-report.json").exists())
                review = _get(base + "/review?report=" + str(first.resolve()))
                self.assertIn('data-same-run="no"', review)
                self.assertIn("older run", review)
                self.assertIn("I read the first run", review)
                self.assertIn("verifiable yes", review.lower())
                replaced = _post(base + "/review/compile", {"repo_id": "sample-product"})
                later = sorted(reports.glob("review-report_*.json"))
                self.assertEqual(len(later), 2)
                self.assertEqual(later[0].read_bytes(), signed)
                self.assertNotIn("I read the first run", replaced)
                self.assertIn('data-same-run="yes"', replaced)
                self.assertIn("unsigned", replaced.lower())
                loaded = read_json(later[-1])
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
