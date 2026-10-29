"""Cover and Requirements catalog: empty workspace, an existing catalog, and legacy /requirement."""

from __future__ import annotations

import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from common.jsonio import write_json
from common.store import save_pack
from discovery.door import created_curbpack, set_open_repo
from discovery.repos import add_repo, load_repos, save_repos
from requirements.extract.pipeline import draft_pack
from requirements.ui.pages import job_fragment
from requirements.workspace import create_extraction_copy, mark_selected


class CoverNavigationTest(unittest.TestCase):
    def test_empty_workspace_requirement_link_is_explained(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                cover = _get(base + "/")
                self.assertIn("Curbpack Studio", cover)
                self.assertIn('href="/requirements"', cover)
                self.assertNotIn('href="/studio"', cover)
                self.assertNotIn('href="/requirements/copy"', cover)
                self.assertIn("Developer", cover)
                self.assertIn("Discovery &amp; Claims", cover)
                for href in ("/discover", "/claims", "/check", "/review", "/scaffold"):
                    self.assertIn(f'href="{href}"', cover)
                self.assertLess(cover.index("Pack Editor"), cover.index("Developer"))
                self.assertLess(cover.index('href="/discover"'), cover.index("Developer"))
                self.assertGreater(cover.index('href="/claims"'), cover.index("Developer"))
                catalog = _get(base + "/requirements")
                self.assertIn("Pack Sources", catalog)
                self.assertIn("Choose a repo", catalog)
                self.assertNotIn("id=\"add-open\"", catalog)
                self.assertNotIn("cra-xml", catalog)
                self.assertNotIn("Content of the technical documentation", catalog)
                self.assertNotIn("Inventory units", catalog)
                self.assertNotIn("Extract selected section", catalog)
                editor = _get(base + "/requirements?document=cra-annex-vii")
                self.assertIn("Pack Editor", editor)
                self.assertIn("Choose a repo", editor)
                self.assertNotIn("Working copy", editor)
                for path in (
                    "/claims",
                    "/scaffold",
                    "/check",
                    "/review",
                    "/requirements/compare",
                    "/requirements/consolidate",
                ):
                    self.assertIn("<h1>", _get(base + path))

                status, body = _get_status(base + "/requirement")
                self.assertEqual(status, 400)
                self.assertIn("Prepare sample workspace", body)
                self.assertIn("Requirements catalog", body)
                self.assertIn("demo pack", body)
                self.assertNotIn("Traceback", body)
                self.assertNotIn("FileNotFoundError", body)
            finally:
                httpd.shutdown()
                httpd.server_close()

    def test_opening_an_existing_catalog_shows_the_pack_and_does_not_change_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog_path = root / "registered_sources.json"
            catalog_path.write_text(
                '{"documents":[{"id":"house","name":"House Rules",'
                '"official_name":"House","url":"https://example.test/house",'
                '"adapter_id":"cra-xml"}],"sources":[]}\n',
                encoding="utf-8",
            )
            before = catalog_path.read_bytes()
            repo = root / "product"
            repo.mkdir()
            write_json(repo / "curbpack.json", created_curbpack(packs=["house"]))
            pack_dir = repo / "curbpack" / "packs" / "house" / draft_pack()["version"]
            save_pack(
                pack_dir,
                {
                    "id": "house",
                    "name": "House Rules",
                    "version": draft_pack()["version"],
                    "source": {"instrument": "House", "url": "https://example.test/house"},
                },
            )
            save_repos(root, add_repo(root, load_repos(root), name="Product", path=str(repo)))
            set_open_repo(root, "product")
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                cover = _get(base + "/")
                self.assertIn("Pack Editor", cover)
                self.assertIn('href="/requirements">Pack Editor</a>', cover)
                for href in ("/discover", "/check", "/review"):
                    self.assertIn(f'href="{href}"', cover)
                listed = _get(base + "/requirements")
                self.assertIn("<h1>Pack Sources</h1>", listed)
                self.assertIn("House Rules", listed)
                self.assertEqual(catalog_path.read_bytes(), before)
                self.assertFalse((root / "selection.json").exists())
                self.assertEqual(
                    list(root.rglob("pack.json")),
                    [pack_dir / "pack.json"],
                )
            finally:
                httpd.shutdown()
                httpd.server_close()

    def test_requirements_list_links_to_the_current_pack_source_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "registered_sources.json").write_text(
                '{"documents":[{"id":"cra-annex-vii","name":"CRA Annex VII",'
                '"official_name":"Content of the technical documentation",'
                '"url":"https://example.test/cra","adapter_id":"cra-xml"}],'
                '"sources":[]}\n',
                encoding="utf-8",
            )
            copy = create_extraction_copy(
                root,
                "cra-xml-baseline",
                {"id": "cra-xml-baseline", "name": "CRA XML", "version": "0.1.0"},
                at="2026-10-27T065647Z",
            )
            mark_selected(root, "cra-xml-baseline", copy.name)
            repo = root / "product"
            repo.mkdir()
            write_json(repo / "curbpack.json", created_curbpack(packs=[]))
            save_repos(root, add_repo(root, load_repos(root), name="Product", path=str(repo)))
            set_open_repo(root, "product")
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                page = _get(base + "/requirements/copy")
                link = '<a href="/requirements?document=cra-annex-vii">CRA Annex VII</a>'
                self.assertIn(link, page)
                self.assertLess(page.index(">Pack Sources</a>"), page.index(link))
                self.assertLess(page.index(link), page.index("<h1>Requirements</h1>"))
                sections = _get(base + "/requirements?document=cra-annex-vii")
                self.assertIn("Sections of <strong>CRA Annex VII</strong>", sections)
            finally:
                httpd.shutdown()
                httpd.server_close()

    def test_running_extract_dialog_keeps_the_pack(self):
        page = job_fragment(
            {"job_id": "extract-1", "status": "running", "log_tail": ["start VII"]},
            document_id="cra-annex-vii",
        ).decode("utf-8")
        self.assertIn('id="job-abort"', page)
        self.assertIn('name="document" value="cra-annex-vii"', page)
        self.assertIn('href="/requirements?document=cra-annex-vii"', page)


def _get(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def _get_status(url: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


if __name__ == "__main__":
    unittest.main()
