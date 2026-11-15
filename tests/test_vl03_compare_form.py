"""VL-03: a form Compare page reviews one Requirement."""

from __future__ import annotations

import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from common.canonical import version_digest
from common.store import load_requirement, save_requirement
from requirements.editing import apply_edits
from requirements.extract.pipeline import draft_pack, extract_annex_vii_risk
from requirements.workspace import create_extraction_copy


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

    def test_json_names_the_current_and_proposed_notes_and_writes_nothing(self):
        import json

        base_requirement = extract_annex_vii_risk()
        current = apply_edits(base_requirement, {"note": "Current note."})
        proposed = apply_edits(base_requirement, {"note": "Proposed note."})
        same = apply_edits(dict(base_requirement, id="REQ-SAME"), {"note": "Same note."})
        destination = create_extraction_copy(
            self.root, "cra-baseline", draft_pack(), at="2026-10-13T090000Z"
        )
        proposal = create_extraction_copy(
            self.root, "cra-baseline", draft_pack(), at="2026-10-13T143000Z"
        )
        save_requirement(destination, current)
        save_requirement(destination, same)
        save_requirement(proposal, proposed)
        save_requirement(proposal, same)
        before = {
            path: path.read_bytes()
            for path in list(destination.rglob("*.json")) + list(proposal.rglob("*.json"))
        }
        base = self._serve()
        query = "proposal=2026-10-13T143000Z&destination=2026-10-13T090000Z"
        changed = json.loads(
            urllib.request.urlopen(
                base + "/requirements/compare/form.json?requirement=CRA-ANNEX-VII-RISK&" + query
            ).read().decode("utf-8")
        )
        unchanged = json.loads(
            urllib.request.urlopen(
                base + "/requirements/compare/form.json?requirement=REQ-SAME&" + query
            ).read().decode("utf-8")
        )
        self.assertEqual(changed["current"]["note"], "Current note.")
        self.assertEqual(changed["proposed"]["note"], "Proposed note.")
        self.assertEqual(changed["destination_digest"], version_digest(current))
        self.assertEqual(changed["source_digest"], version_digest(proposed))
        self.assertEqual(changed["changed"], ["note"])
        self.assertEqual(unchanged["changed"], [])
        after = {
            path: path.read_bytes()
            for path in list(destination.rglob("*.json")) + list(proposal.rglob("*.json"))
        }
        self.assertEqual(after, before)

    def test_the_list_shows_changes_for_the_extract_and_the_import_pair(self):
        import urllib.error

        from common.jsonio import write_json
        from common.store import save_pack
        from discovery.door import created_curbpack, set_open_repo
        from discovery.repos import add_repo, load_repos, save_repos
        from requirements.workspace import mark_selected
        from studio.pack.pack_exchange import export_pack_zip

        base_requirement = extract_annex_vii_risk()
        current = apply_edits(base_requirement, {"note": "Current note."})
        proposed = apply_edits(base_requirement, {"note": "Proposed note."})
        same = apply_edits(dict(base_requirement, id="REQ-SAME"), {"note": "Same note."})
        create_extraction_copy(self.root, "cra-baseline", draft_pack(), at="2026-10-13T090000Z")
        create_extraction_copy(self.root, "cra-baseline", draft_pack(), at="2026-10-13T143000Z")
        destination = self.root / "cra-baseline" / "2026-10-13T090000Z"
        proposal = self.root / "cra-baseline" / "2026-10-13T143000Z"
        save_requirement(destination, current)
        save_requirement(destination, same)
        save_requirement(proposal, proposed)
        save_requirement(proposal, same)
        base = self._serve()
        listed = urllib.request.urlopen(
            base
            + "/requirements/copy?proposal=2026-10-13T143000Z&destination=2026-10-13T090000Z"
        ).read().decode("utf-8")
        self.assertIn("<th>New</th>", listed)
        self.assertIn(
            'href="/requirements/compare/form?requirement=CRA-ANNEX-VII-RISK'
            '&amp;proposal=2026-10-13T143000Z&amp;destination=2026-10-13T090000Z"',
            listed,
        )
        self.assertIn(">Changes</a>", listed)
        same_row = listed.split("REQ-SAME", 1)[1].split("</tr>", 1)[0]
        self.assertNotIn("Changes", same_row)
        compare = urllib.request.urlopen(base + "/requirements/compare").read().decode("utf-8")
        self.assertIn("<h1>Compare</h1>", compare)

        mark_selected(self.root, "cra-baseline", "2026-10-13T090000Z")
        imported = apply_edits(base_requirement, {"note": "Imported note."})
        imported_pack = dict(draft_pack(), version="1.1.0")
        folder = self.root / "zip-source"
        save_pack(folder, imported_pack)
        save_requirement(folder, imported)
        save_requirement(folder, same)
        payload, _rows = export_pack_zip(folder, {})
        repo = self.root / "product"
        repo.mkdir()
        write_json(repo / "curbpack.json", created_curbpack(namespace_base="RISE", packs=["cra-baseline"]))
        save_repos(self.root, add_repo(self.root, load_repos(self.root), name="Product", path=str(repo)))
        set_open_repo(self.root, "product")
        boundary = "vl03boundarytoken"
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="archive"; filename="pack.zip"\r\n'
            "Content-Type: application/zip\r\n\r\n"
        ).encode("utf-8") + payload + f"\r\n--{boundary}--\r\n".encode("utf-8")

        class _NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        opener = urllib.request.build_opener(_NoRedirect)
        try:
            opener.open(
                urllib.request.Request(
                    base + "/requirements",
                    data=body,
                    method="POST",
                    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                )
            )
            self.fail("import did not redirect")
        except urllib.error.HTTPError as exc:
            location = exc.headers.get("Location") or ""
            exc.close()
        self.assertIn("proposal=", location)
        self.assertIn("destination=2026-10-13T090000Z", location)
        imported_list = urllib.request.urlopen(base + location).read().decode("utf-8")
        self.assertIn("<th>New</th>", imported_list)
        self.assertIn("CRA-ANNEX-VII-RISK", imported_list)
        self.assertIn(">Changes</a>", imported_list)

    def test_import_without_a_selected_copy_has_no_changes_link(self):
        import urllib.error

        from common.jsonio import write_json
        from common.store import save_pack
        from discovery.door import created_curbpack, set_open_repo
        from discovery.repos import add_repo, load_repos, save_repos
        from studio.pack.pack_exchange import export_pack_zip

        folder = self.root / "zip-source"
        save_pack(folder, draft_pack())
        save_requirement(folder, apply_edits(extract_annex_vii_risk(), {"note": "Imported note."}))
        payload, _rows = export_pack_zip(folder, {})
        repo = self.root / "product"
        repo.mkdir()
        write_json(repo / "curbpack.json", created_curbpack(namespace_base="RISE", packs=["cra-baseline"]))
        save_repos(self.root, add_repo(self.root, load_repos(self.root), name="Product", path=str(repo)))
        set_open_repo(self.root, "product")
        boundary = "vl03boundarytoken"
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="archive"; filename="pack.zip"\r\n'
            "Content-Type: application/zip\r\n\r\n"
        ).encode("utf-8") + payload + f"\r\n--{boundary}--\r\n".encode("utf-8")

        class _NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        opener = urllib.request.build_opener(_NoRedirect)
        base = self._serve()
        try:
            opener.open(
                urllib.request.Request(
                    base + "/requirements",
                    data=body,
                    method="POST",
                    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                )
            )
            self.fail("import did not redirect")
        except urllib.error.HTTPError as exc:
            location = exc.headers.get("Location") or ""
            exc.close()
        self.assertEqual(location, "/requirements/copy?imported=1")
        page = urllib.request.urlopen(base + location).read().decode("utf-8")
        self.assertNotIn("<th>New</th>", page)
        self.assertNotIn(">Changes</a>", page)
