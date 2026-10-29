"""The Check page shows the open repo's curbpack.json paths and can save them."""

from __future__ import annotations

import tempfile
import threading
import unittest
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from common.jsonio import read_json, write_json
from common.store import save_pack
from discovery.door import created_curbpack
from discovery.repos import add_repo, load_repos, save_repos
from requirements.extract.pipeline import draft_pack


def _get(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode()


def _post(url: str, form: dict) -> str:
    data = urllib.parse.urlencode(form, doseq=True).encode()
    request = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(request) as response:
        return response.read().decode()


class CheckEditorTest(unittest.TestCase):
    def test_check_shows_named_packs_and_saves_directory_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "ws"
            root.mkdir()
            repo = Path(tmp) / "widget"
            repo.mkdir()
            write_json(
                repo / "curbpack.json",
                created_curbpack(packs=["cra-baseline"], reports_dir="signed/reports"),
            )
            save_pack(
                repo / "curbpack" / "packs" / "cra-baseline" / draft_pack()["version"],
                draft_pack(),
            )
            save_repos(
                root,
                add_repo(root, load_repos(root), name="Widget", path=str(repo)),
            )
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                page = _get(base + "/check?repo=widget")
                self.assertNotIn("Read it and tick the packs it names?", page)
                self.assertNotIn("Start empty", page)
                self.assertIn("cra-baseline", page)
                self.assertIn("present", page)
                self.assertIn('name="packs_dir"', page)
                self.assertIn('name="reports_dir"', page)
                saved = _post(
                    base + "/check",
                    {
                        "action": "save",
                        "repo_id": "widget",
                        "packs_dir": "curbpack/packs",
                        "claims_dir": "curbpack/claims",
                        "results_dir": ".curbpack",
                        "reports_dir": "kept/reports",
                    },
                )
                self.assertEqual(read_json(repo / "curbpack.json")["reports_dir"], "kept/reports")
                self.assertEqual(read_json(repo / "curbpack.json")["packs"], ["cra-baseline"])
                self.assertIn("kept/reports", saved)
            finally:
                httpd.shutdown()
                httpd.server_close()


if __name__ == "__main__":
    unittest.main()
