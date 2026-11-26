"""POST /requirements/source goes through the handler."""

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


class SourcePostTest(unittest.TestCase):
    def test_source_post_remembers_a_known_adapter_and_refuses_an_empty_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                with self.assertRaises(AssertionError) as empty:
                    _post(base + "/requirements/source", {"adapter_id": ""})
                self.assertIn("a non-empty adapter id", str(empty.exception))
                self.assertFalse((root / "source_adapter.json").is_file())
                with self.assertRaises(AssertionError) as unknown:
                    _post(base + "/requirements/source", {"adapter_id": "missing-adapter"})
                self.assertIn("a known adapter, not missing-adapter", str(unknown.exception))
                remembered = json.loads((root / "source_adapter.json").read_text())
                self.assertEqual(remembered["adapter_id"], "missing-adapter")
                self.assertEqual(
                    _post(base + "/requirements/source", {"adapter_id": "cra"}),
                    "/requirements/inspect?adapter=cra",
                )
                remembered = json.loads((root / "source_adapter.json").read_text())
                self.assertEqual(remembered["adapter_id"], "cra")
            finally:
                httpd.shutdown()
                httpd.server_close()
