"""Publish/sign ModelErrors return to the Requirement editor with field marks."""

from __future__ import annotations

import tempfile
import threading
import unittest
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, _requirement_editor_for_error, make_handler
from common.errors import ModelError
from common.store import load_requirement, save_requirement
from requirements.extract.adapter import ADAPTERS, load_adapter
from requirements.workspace import extract_section, mark_selected, mark_source_adapter


class RequirementEditorErrorRedirectTest(unittest.TestCase):
    def test_maps_source_edition_error_to_editor_query(self):
        href = _requirement_editor_for_error(
            ModelError(
                "requirement CRA-ANNEX-VII-DESIGN-DEVELOPMENT-ARCHITECTURE.source",
                "edition",
                "non-empty string",
            )
        )
        self.assertTrue(
            href.startswith(
                "/requirements/requirement/CRA-ANNEX-VII-DESIGN-DEVELOPMENT-ARCHITECTURE?"
            )
        )
        self.assertIn("invalid=edition", href)
        self.assertIn("Field%20Edition", href)
        self.assertIn("non%20empty%20string", href)
        self.assertNotIn("CRA-ANNEX-VII-DESIGN-DEVELOPMENT-ARCHITECTURE.source", href)

    def test_publish_missing_edition_opens_editor_with_red_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adapter = load_adapter(ADAPTERS / "cra-xml" / "adapter.json")
            proposals = [
                {
                    "locus": "3",
                    "id": "CRA-ANNEX-VII-RISK",
                    "locator": "VII.3",
                    "discovery_hints": {
                        "concepts": ["risk assessment"],
                        "path_hints": ["*risk*"],
                        "sources": [{"source": "documents"}],
                    },
                }
            ]
            created = extract_section(
                root,
                ADAPTERS / "cra-xml",
                adapter,
                "VII",
                proposals,
                {"id": "cra-xml-baseline", "name": "CRA XML", "version": "0.1.0"},
                at="2026-10-13T090000Z",
            )
            mark_source_adapter(root, "cra-xml")
            mark_selected(root, "cra-xml-baseline", created["copy"].name)
            path = created["copy"] / "CRA-ANNEX-VII-RISK.json"
            requirement = load_requirement(path)
            source = dict(requirement.get("source") or {})
            source.pop("edition", None)
            requirement["source"] = source
            save_requirement(created["copy"], requirement)

            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://{httpd.server_address[0]}:{httpd.server_address[1]}"
            try:
                body = urllib.parse.urlencode({"version": "0.1.0"}).encode("utf-8")
                request = urllib.request.Request(
                    base + "/requirements/publish", data=body, method="POST"
                )
                with urllib.request.urlopen(request) as response:
                    page = response.read().decode("utf-8")
                self.assertIn("CRA-ANNEX-VII-RISK", page)
                self.assertIn('name="edition"', page)
                self.assertIn('class="invalid"', page)
                self.assertIn("Field Edition: expected non empty string", page)
                self.assertNotIn(".source: field edition", page)
            finally:
                httpd.shutdown()
                httpd.server_close()


if __name__ == "__main__":
    unittest.main()
