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
from requirements.ui.pages import job_fragment


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
                self.assertNotIn('href="/requirements/copy"', cover)
                self.assertIn("Developer", cover)
                self.assertIn("Discovery &amp; Claims", cover)
                for href in ("/discover", "/claims", "/check", "/review", "/scaffold"):
                    self.assertIn(f'href="{href}"', cover)
                self.assertLess(cover.index("Pack Editor"), cover.index("Developer"))
                self.assertLess(cover.index('href="/discover"'), cover.index("Developer"))
                self.assertGreater(cover.index('href="/claims"'), cover.index("Developer"))
                catalog = _get(base + "/requirements")
                self.assertIn("Packs", catalog)
                self.assertIn("id=\"add-open\"", catalog)
                self.assertIn("Official name", catalog)
                self.assertIn("Content of the technical documentation", catalog)
                self.assertIn('data-adapter="cra-xml"', catalog)
                self.assertIn('data-adapter="nis"', catalog)
                self.assertIn("https://publications.europa.eu/resource/celex/32024R2847", catalog)
                self.assertIn("https://publications.europa.eu/resource/celex/32022L2555", catalog)
                self.assertIn('type="submit">Sections</button>', catalog)
                self.assertNotIn("disabled>Edit", catalog)
                self.assertIn('class="sign-bad" disabled', catalog)
                self.assertIn(">unsigned</button>", catalog)
                self.assertIn('type="submit">Export Pack</button>', catalog)
                self.assertNotIn('type="button">Publish</button>', catalog)
                self.assertNotIn(">Extract</button>", catalog)
                editor = _get(base + "/requirements?document=cra-annex-vii")
                self.assertIn("Pack Editor", editor)
                self.assertIn(">Signed</th>", editor)
                self.assertIn(">Unsigned</th>", editor)
                self.assertNotIn("Working copy", editor)
                self.assertNotIn('value="publish"', editor)
                self.assertIn("Extract", editor)
                self.assertIn("disabled>Edit", editor)
                self.assertNotIn('data-adapter="nis"', editor)
                self.assertNotIn("medtech", catalog)
                self.assertNotIn("Inventory units", catalog)
                self.assertNotIn("Extract selected section", catalog)
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
                self.assertEqual(list(root.rglob("pack.json")), [])
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
