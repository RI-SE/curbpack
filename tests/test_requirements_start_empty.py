"""POST /requirements/start-empty goes through the handler."""

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
            return exc.headers.get("Location") or ""
        body = exc.read().decode("utf-8")
        raise AssertionError(f"{exc.code} {body}") from exc


class StartEmptyPostTest(unittest.TestCase):
    def test_start_empty_registers_a_folder_and_refuses_a_blank_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                with self.assertRaises(AssertionError) as blank:
                    _post(base + "/requirements/start-empty", {"folder": "  "})
                self.assertIn("a working folder", str(blank.exception))
                self.assertFalse((root / "empty-product").exists())
                location = _post(base + "/requirements/start-empty", {"folder": "empty-product"})
                self.assertEqual(location, "/requirements?repo=empty-product")
                self.assertTrue((root / "empty-product").is_dir())
                self.assertFalse((root / "empty-product" / "curbpack.json").exists())
                repos = json.loads((root / "product_repos.json").read_text())
                self.assertEqual(repos["repos"][-1]["id"], "empty-product")
                again = _post(base + "/requirements/start-empty", {"folder": "empty-product"})
                self.assertEqual(again, "/requirements?repo=empty-product")
            finally:
                httpd.shutdown()
                httpd.server_close()
