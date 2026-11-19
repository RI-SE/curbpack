"""Project page gate, empty-repos scan, and select."""

from __future__ import annotations

import tempfile
import threading
import unittest
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.project_selector import ensure_repos_populated
from app.server import Workspace, make_handler
from common.jsonio import read_json, write_json
from discovery.door import created_curbpack, open_repo_id, set_open_repo
from discovery.repos import add_repo, load_repos, save_repos


class ProjectPageTest(unittest.TestCase):
    def test_gate_redirects_to_project_and_select_opens_cover(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            workspace.mkdir()

            demo = workspace / "demo-product"
            demo.mkdir()
            write_json(demo / "curbpack.json", created_curbpack())

            httpd = ThreadingHTTPServer(
                ("127.0.0.1", 0),
                make_handler(Workspace(workspace)),
            )
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"

            try:
                project = _get(base + "/discover")
                self.assertIn("Registered projects", project)
                self.assertIn("demo-product", project)

                repos = load_repos(workspace).get("repos") or []
                self.assertEqual(len(repos), 1)
                self.assertEqual(repos[0]["name"], "demo-product")

                cover = _post(
                    base + "/project",
                    {"action": "select", "repo_id": str(repos[0]["id"])},
                )

                self.assertEqual(open_repo_id(workspace), str(repos[0]["id"]))
                self.assertIn("<h1>Curbpack Studio</h1>", cover)
                self.assertIn("author packs from law text", cover)
                self.assertIn('href="/home">Home</a>', cover)
                self.assertIn("Change Project", cover)
                self.assertLess(cover.index("</header>"), cover.index('class="config-panel"'))
                self.assertLess(cover.index('class="config-panel"'), cover.index("<h1>Curbpack Studio</h1>"))
                self.assertLess(cover.index('class="config-panel"'), cover.index("Review — compile"))
                self.assertIn("Current Project", cover)
                self.assertIn('id="config-all-open">demo-product</button>', cover)
                self.assertNotIn("Show Configuration", cover)
                compact, _, dialog = cover.partition('<dialog id="config-all"')
                for label in (
                    "Current Configuration",
                    "Packs directory",
                    "Claims directory",
                    "Results directory",
                    "Reports directory",
                ):
                    self.assertNotIn(label, compact)
                    self.assertIn(label, dialog)
                self.assertIn("curbpack/packs", cover)
                self.assertIn("curbpack/claims", cover)
                self.assertIn(".curbpack", cover)
                self.assertIn("curbpack/reports", cover)
            finally:
                httpd.shutdown()
                httpd.server_close()

    def test_invalid_curbpack_still_shows_registered_projects(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            workspace.mkdir()
            demo = workspace / "demo-product"
            demo.mkdir()
            config = created_curbpack()
            config["unsigned_requirements"] = "reject"
            write_json(demo / "curbpack.json", config)
            data = load_repos(workspace)
            add_repo(workspace, data, name="demo-product", path=str(demo))
            save_repos(workspace, data)
            set_open_repo(workspace, str(data["repos"][-1]["id"]))

            httpd = ThreadingHTTPServer(
                ("127.0.0.1", 0),
                make_handler(Workspace(workspace)),
            )
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                page = _get(base + "/")
                self.assertIn("Registered projects", page)
                self.assertIn("demo-product", page)
                self.assertIn("unsigned_requirements", page)
                self.assertIn("curbpack/packs", page)
            finally:
                httpd.shutdown()
                httpd.server_close()

    def test_ensure_repos_populated_writes_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "ws"
            workspace.mkdir()

            product = workspace / "alpha"
            product.mkdir()
            write_json(product / "curbpack.json", created_curbpack())

            first = ensure_repos_populated(workspace)
            self.assertEqual(len(first["repos"]), 1)

            second = ensure_repos_populated(workspace)
            self.assertEqual(len(second["repos"]), 1)

            self.assertEqual(
                read_json(workspace / "product_repos.json")["repos"][0]["name"],
                "alpha",)


def _get(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def _post(url: str, fields: dict) -> str:
    data = urllib.parse.urlencode(fields).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(request) as response:
        return response.read().decode("utf-8")


if __name__ == "__main__":
    unittest.main()
