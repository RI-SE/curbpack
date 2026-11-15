"""VL-03: a form Compare page reviews one Requirement."""

from __future__ import annotations

import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler


class CompareFormPageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def _serve(self) -> str:
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(self.root)))
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(httpd.shutdown)
        self.addCleanup(httpd.server_close)
        return f"http://127.0.0.1:{httpd.server_address[1]}"

    def test_the_committed_script_is_served_and_compare_stays(self):
        base = self._serve()
        compare = urllib.request.urlopen(base + "/requirements/compare").read().decode("utf-8")
        self.assertIn("<h1>Compare</h1>", compare)
        request = urllib.request.Request(base + "/requirements/compare/form.js")
        with urllib.request.urlopen(request) as response:
            body = response.read().decode("utf-8")
            content_type = response.headers.get("Content-Type") or ""
        self.assertIn("javascript", content_type)
        self.assertIn("renderCompareForm", body)
        self.assertNotIn("npm install", body)
