"""POST /seal-pack goes through the handler."""

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
from demo_setup import prepare_demo


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


class DemoSealPostTest(unittest.TestCase):
    def test_seal_redirects_after_a_prepared_pack_and_refuses_a_missing_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            pack = root / "packs" / "cra-baseline" / "pack.json"
            try:
                with self.assertRaises(AssertionError) as missing:
                    _post(base + "/seal-pack", {"name": "Ada"})
                self.assertIn("a prepared sample", str(missing.exception))
                self.assertFalse(pack.is_file())
                stored = json.loads((root / "keys" / "keys.json").read_text(encoding="utf-8"))
                self.assertEqual(stored["keys"][0]["name"], "Ada")
                prepare_demo(root)
                self.assertEqual(
                    _post(base + "/seal-pack", {"name": "Ada"}),
                    "/requirement?sealed=1",
                )
                sealed = json.loads(pack.read_text(encoding="utf-8"))
                self.assertIn("signed", sealed)
            finally:
                httpd.shutdown()
                httpd.server_close()
