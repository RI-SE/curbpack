"""POST /discover/jobs/{id}/abort goes through the handler."""

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
from discovery.door import set_open_repo
from discovery.repos import add_repo, load_repos, save_repos


def _post(url: str, form: dict | None = None) -> str:
    data = urllib.parse.urlencode(form or {}).encode("utf-8")
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


class DiscoverJobAbortPostTest(unittest.TestCase):
    def test_abort_waits_for_an_open_project_then_redirects_to_the_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            jobs = root / "jobs"
            jobs.mkdir()
            (jobs / "job-1.json").write_text(
                json.dumps({"status": "running", "log_tail": []}),
                encoding="utf-8",
            )
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                self.assertEqual(_post(base + "/discover/jobs/job-1/abort"), "/project")
                saved = json.loads((jobs / "job-1.json").read_text(encoding="utf-8"))
                self.assertEqual(saved["status"], "running")
                product = root / "product"
                product.mkdir()
                data = add_repo(root, load_repos(root), name="sample", path=str(product))
                save_repos(root, data)
                set_open_repo(root, str(data["repos"][-1]["id"]))
                with self.assertRaises(AssertionError) as missing:
                    _post(base + "/discover/jobs/missing/abort")
                self.assertIn("an existing job file", str(missing.exception))
                self.assertEqual(
                    _post(base + "/discover/jobs/job-1/abort"),
                    "/discover?job=job-1",
                )
                saved = json.loads((jobs / "job-1.json").read_text(encoding="utf-8"))
                self.assertEqual(saved["status"], "aborted")
            finally:
                httpd.shutdown()
                httpd.server_close()
