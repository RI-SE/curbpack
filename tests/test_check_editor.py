"""The Check page edits a repo's curbpack.json and can run that selection."""

from __future__ import annotations

import tempfile
import threading
import unittest
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from claims.bind import build_claim, write_claim
from common.jsonio import read_json, write_json
from common.store import save_requirement
from discovery.repos import save_repos
from requirements.workspace import create_extraction_copy


def _get(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode()


def _post(url: str, form: dict) -> str:
    data = urllib.parse.urlencode(form, doseq=True).encode()
    request = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(request) as response:
        return response.read().decode()


class CheckEditorTest(unittest.TestCase):
    def test_reading_a_repo_file_ticks_its_packs_and_save_writes_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "ws"
            root.mkdir()
            cra = create_extraction_copy(
                root,
                "cra-xml-baseline",
                {"id": "cra-xml-baseline", "name": "CRA", "version": "0.1.0"},
                at="2026-10-27T065647Z",
            )
            save_requirement(
                cra,
                {
                    "id": "REQ-PURPOSE",
                    "pack_id": "cra-xml-baseline",
                    "source": {
                        "framework": "EU",
                        "instrument": "CRA",
                        "identifier": "CELEX:32024R2847",
                        "language": "en",
                        "url": "https://example.invalid/cra",
                    },
                    "references": [
                        {"nr": 1, "locator": "VII.1(a)", "law_text": "its intended purpose"}
                    ],
                },
            )
            create_extraction_copy(
                root,
                "nis2-baseline",
                {"id": "nis2-baseline", "name": "NIS2", "version": "0.2.0"},
                at="2026-10-27T065647Z",
            )
            repo = Path(tmp) / "widget"
            repo.mkdir()
            write_json(
                repo / "curbpack.json",
                {"packs": ["cra-xml-baseline"], "search_hints": {"exclude_path_globs": ["*.png"]}},
            )
            write_claim(
                repo / "claims",
                build_claim(
                    claim_id="claim-readme",
                    requirement_id="REQ-PURPOSE",
                    source="documents",
                    args={"path": "README.md"},
                    checks=[
                        {"check": "exist", "args": {"paths": ["README.md"]}},
                        {
                            "check": "contents",
                            "args": {
                                "path": "README.md",
                                "probes": [{"kind": "size", "bytes": 20, "op": ">="}],
                            },
                        },
                    ],
                    description="The readme names the product purpose.",
                ),
            )
            save_repos(
                root,
                {"repos": [{"id": "widget", "name": "widget", "path": str(repo)}]},
            )
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                asked = _get(base + "/check?repo=widget")
                self.assertIn("Read it and tick the packs it names?", asked)
                self.assertIn(">Include</th>", asked)
                self.assertNotIn('value="cra-xml-baseline" checked', asked)
                loaded = _get(base + "/check?repo=widget&read=yes")
                self.assertIn('value="cra-xml-baseline" checked', loaded)
                self.assertNotIn('value="nis2-baseline" checked', loaded)
                self.assertIn("Working copy · 2026-10-27T065647Z", loaded)
                self.assertIn("is not signed", loaded)
                self.assertIn("># Claims</th>", loaded)
                self.assertIn("<h2>Claims in this repo</h2>", loaded)
                self.assertIn("claim-readme", loaded)
                self.assertIn("README.md", loaded)
                self.assertIn(
                    "<td><code>cra-xml-baseline</code></td>"
                    "<td>Working copy · 2026-10-27T065647Z</td>"
                    "<td><code>0.1.0</code></td>"
                    '<td class="num">1</td>',
                    loaded,
                )
                saved = _post(
                    base + "/check",
                    {"action": "save", "repo_id": "widget", "pack": ["nis2-baseline"]},
                )
                self.assertIn('value="nis2-baseline" checked', saved)
                document = read_json(repo / "curbpack.json")
                self.assertEqual(document["packs"], ["nis2-baseline"])
                self.assertEqual(document["search_hints"]["exclude_path_globs"], ["*.png"])
                self.assertIn('id="export-curbpack"', saved)
            finally:
                httpd.shutdown()
                httpd.server_close()
