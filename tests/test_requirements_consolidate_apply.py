"""POST /requirements/consolidate/apply goes through the handler."""

from __future__ import annotations

import copy
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from common.canonical import version_digest
from common.store import save_requirement
from requirements.editing import apply_edits
from requirements.extract.pipeline import draft_pack, extract_annex_vii_risk
from requirements.workspace import create_extraction_copy, mark_selected


def _post(url: str, form: list[tuple[str, str]]) -> str:
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


class ConsolidateApplyPostTest(unittest.TestCase):
    def test_apply_redirects_after_a_merge_and_refuses_a_missing_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = extract_annex_vii_risk()
            copy_dir = create_extraction_copy(
                root, "cra-baseline", draft_pack(), at="2026-10-13T090000Z"
            )
            other = copy.deepcopy(base)
            other.pop("signed", None)
            other["id"] = "FIXTURE-VII-1A"
            other["references"] = [
                {"nr": 1, "locator": "VII.1(a)", "law_text": "a statement of the intended purpose"}
            ]
            left = apply_edits(base, {"note": "Keep the first note."})
            right = apply_edits(other, {"note": "Keep the first note."})
            save_requirement(copy_dir, left)
            save_requirement(copy_dir, right)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{httpd.server_address[1]}"
            form = [
                ("ids", "CRA-ANNEX-VII-RISK"),
                ("ids", "FIXTURE-VII-1A"),
                ("retained_id", "CRA-ANNEX-VII-RISK"),
                ("note", "Keep the first note."),
                ("ref_locator", "VII.3"),
                ("ref_locator", "VII.1(a)"),
                ("ref_law_text", left["references"][0]["law_text"]),
                ("ref_law_text", right["references"][0]["law_text"]),
                ("digest_id", "CRA-ANNEX-VII-RISK"),
                ("digest_id", "FIXTURE-VII-1A"),
                ("digest_value", version_digest(left)),
                ("digest_value", version_digest(right)),
            ]
            try:
                with self.assertRaises(AssertionError) as missing:
                    _post(base_url + "/requirements/consolidate/apply", form)
                self.assertIn("a selected working copy", str(missing.exception))
                self.assertTrue((copy_dir / "FIXTURE-VII-1A.json").is_file())
                mark_selected(root, "cra-baseline", "2026-10-13T090000Z")
                self.assertEqual(
                    _post(base_url + "/requirements/consolidate/apply", form),
                    "/requirements/consolidate?merged=1",
                )
                self.assertFalse((copy_dir / "FIXTURE-VII-1A.json").exists())
            finally:
                httpd.shutdown()
                httpd.server_close()
