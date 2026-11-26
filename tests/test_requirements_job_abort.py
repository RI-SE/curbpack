"""POST /requirements/jobs/{id}/abort goes through the handler."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler


def _post(url: str, form: dict) -> str:
    data = urllib.parse.urlencode(form).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(request) as response:
            return response.geturl()
    except urllib.error.HTTPError as exc:
        if exc.code in {301, 302, 303, 307, 308}:
            location = exc.headers.get("Location") or ""
            exc.close()
            return location
        body = exc.read().decode("utf-8")
        exc.close()
        raise AssertionError(f"{exc.code} {body}") from exc


class RequirementsJobAbortPostTest(unittest.TestCase):
    def test_abort_redirects_to_the_job_and_refuses_a_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                with self.assertRaises(AssertionError) as missing:
                    _post(base + "/requirements/jobs/missing/abort", {})
                self.assertIn("an existing job file", str(missing.exception))
                self.assertFalse((root / "jobs" / "missing.json").is_file())
                jobs = root / "jobs"
                jobs.mkdir()
                (jobs / "job-1.json").write_text(
                    json.dumps({"status": "running", "log_tail": []}),
                    encoding="utf-8",
                )
                self.assertEqual(
                    _post(base + "/requirements/jobs/job-1/abort", {"document": "doc-1"}),
                    "/requirements?document=doc-1&job=job-1",
                )
                saved = json.loads((jobs / "job-1.json").read_text(encoding="utf-8"))
                self.assertEqual(saved["status"], "aborted")
                (jobs / "job-2.json").write_text(
                    json.dumps({"status": "running", "log_tail": []}),
                    encoding="utf-8",
                )
                self.assertEqual(
                    _post(base + "/requirements/jobs/job-2/abort", {}),
                    "/requirements?job=job-2",
                )
            finally:
                httpd.shutdown()
                httpd.server_close()
