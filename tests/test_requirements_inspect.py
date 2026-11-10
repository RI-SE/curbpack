"""GET /requirements/inspect goes through the handler."""

from __future__ import annotations

import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler


def _get(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


class InspectPageTest(unittest.TestCase):
    def test_inspect_shows_the_named_adapter_without_an_open_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(Path(tmp))))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                page = _get(base + "/requirements/inspect?adapter=cra")
                self.assertIn("<h1>Source details</h1>", page)
                self.assertIn("<code>cra</code>", page)
                self.assertIn("<code>VII</code>", page)
                self.assertNotIn("Registered projects", page)
                with self.assertRaises(urllib.error.HTTPError) as missing:
                    _get(base + "/requirements/inspect")
                self.assertEqual(missing.exception.code, 400)
                self.assertIn(
                    "source: field adapter: expected an adapter id",
                    missing.exception.read().decode("utf-8"),
                )
            finally:
                httpd.shutdown()
                httpd.server_close()
