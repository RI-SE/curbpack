"""Directory browser for Add-repo path picking."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from common.errors import ModelError
from discovery.browse import list_directories


class BrowseDirsTest(unittest.TestCase):
    def test_lists_child_dirs_and_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "alpha").mkdir()
            (root / "beta").mkdir()
            (root / "file.txt").write_text("x\n", encoding="utf-8")
            data = list_directories(str(root))
            self.assertEqual(data["path"], str(root.resolve()))
            names = [row["name"] for row in data["dirs"]]
            self.assertEqual(names, ["alpha", "beta"])
            self.assertTrue(data["parent"])
            parent = list_directories(data["parent"])
            child_names = [row["name"] for row in parent["dirs"]]
            self.assertIn(root.name, child_names)

    def test_missing_path_is_model_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nope"
            with self.assertRaises(ModelError):
                list_directories(str(missing))


class BrowseHttpTest(unittest.TestCase):
    def test_browse_json_and_add_repo_ui_have_browse_control(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "product").mkdir()
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://{httpd.server_address[0]}:{httpd.server_address[1]}"
            try:
                with urllib.request.urlopen(
                    base + "/discover/browse?dir=" + urllib.parse.quote(str(root))
                ) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                self.assertEqual(payload["path"], str(root.resolve()))
                self.assertEqual([row["name"] for row in payload["dirs"]], ["product"])

                with urllib.request.urlopen(base + "/discover") as response:
                    page = response.read().decode("utf-8")
                self.assertIn('id="discover-browse-path"', page)
                self.assertIn('id="repo-browse"', page)
                self.assertIn("openRepoBrowse", page)
            finally:
                httpd.shutdown()
                httpd.server_close()


if __name__ == "__main__":
    unittest.main()
