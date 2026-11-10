"""POST /prepare goes through the handler."""

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


def _post_redirect(url: str) -> str:
    request = urllib.request.Request(url, data=b"", method="POST")

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


class PreparePostTest(unittest.TestCase):
    def test_prepare_redirects_home_and_refuses_a_second_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                self.assertEqual(_post_redirect(base + "/prepare"), "/?prepared=1")
                page = _get(base + "/?prepared=1")
                self.assertIn("Sample workspace prepared.", page)
                self.assertTrue((root / "product" / "curbpack.json").is_file())
                request = urllib.request.Request(base + "/prepare", data=b"", method="POST")
                with self.assertRaises(urllib.error.HTTPError) as again:
                    urllib.request.urlopen(request)
                self.assertEqual(again.exception.code, 400)
                self.assertIn(
                    "an empty workspace",
                    again.exception.read().decode("utf-8"),
                )
            finally:
                httpd.shutdown()
                httpd.server_close()
