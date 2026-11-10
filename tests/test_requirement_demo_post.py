"""POST /requirement goes through the handler."""

from __future__ import annotations

import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from common.store import load_requirement
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


class DemoRequirementPostTest(unittest.TestCase):
    def test_save_redirects_to_the_demo_requirement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            requirement = root / "packs" / "cra-baseline" / "CRA-ANNEX-VII-RISK.json"
            try:
                self.assertEqual(_post(base + "/requirement", {"note": "A demo note."}), "/project")
                self.assertFalse(requirement.is_file())
                prepare_demo(root)
                self.assertEqual(
                    _post(base + "/requirement", {"note": "A demo note."}),
                    "/requirement?saved=1",
                )
                saved = load_requirement(requirement)
                self.assertEqual(saved["note"], "A demo note.")
            finally:
                httpd.shutdown()
                httpd.server_close()
