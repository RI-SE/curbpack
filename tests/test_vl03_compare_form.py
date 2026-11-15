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
