"""POST /requirements/compare/apply goes through the handler."""

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
from common.canonical import version_digest
from common.jsonio import write_json
from common.store import load_requirement, save_requirement
from discovery.door import created_curbpack, set_open_repo
from discovery.repos import add_repo, load_repos, save_repos
from requirements.editing import apply_edits
from requirements.extract.pipeline import draft_pack, extract_annex_vii_risk
from requirements.workspace import create_extraction_copy


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
        raise AssertionError(f"{exc.code} {body}") from exc


class CompareApplyPostTest(unittest.TestCase):
    def test_apply_redirects_to_the_posted_copies_and_refuses_a_published_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "product"
            repo.mkdir()
            write_json(
                repo / "curbpack.json",
                created_curbpack(namespace_base="RISE", packs=["cra-baseline"]),
            )
            save_repos(root, add_repo(root, load_repos(root), name="Product", path=str(repo)))
            set_open_repo(root, "product")
            base = extract_annex_vii_risk()
            source = create_extraction_copy(root, "cra-baseline", draft_pack(), at="2026-10-13T090000Z")
            destination = create_extraction_copy(root, "cra-baseline", draft_pack(), at="2026-10-13T143000Z")
            source_requirement = apply_edits(base, {"remediation_hint": "from the source"})
            destination_requirement = apply_edits(base, {"remediation_hint": "old hint"})
            save_requirement(source, source_requirement)
            save_requirement(destination, destination_requirement)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{httpd.server_address[1]}"
            form = {
                "source": "2026-10-13T090000Z",
                "destination": "2026-10-13T143000Z",
                "field": "remediation_hint",
                "value": "from the source",
                "requirement_id": "CRA-ANNEX-VII-RISK",
                "source_digest": version_digest(source_requirement),
                "destination_digest": version_digest(destination_requirement),
            }
            try:
                refused = dict(form)
                refused["destination"] = "published:0.1.0"
                with self.assertRaises(AssertionError) as published:
                    _post(base_url + "/requirements/compare/apply", refused)
                self.assertIn("a working copy, not a published release", str(published.exception))
                self.assertEqual(
                    load_requirement(destination / "CRA-ANNEX-VII-RISK.json")["remediation_hint"],
                    "old hint",
                )
                self.assertEqual(
                    _post(base_url + "/requirements/compare/apply", form),
                    "/requirements/compare?left=2026-10-13T090000Z&right=2026-10-13T143000Z",
                )
                saved = load_requirement(destination / "CRA-ANNEX-VII-RISK.json")
                self.assertEqual(saved["remediation_hint"], "from the source")
            finally:
                httpd.shutdown()
                httpd.server_close()
