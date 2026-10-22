"""Researcher overview, findings, feedback, checks, and Claim creation over HTTP."""

from __future__ import annotations

import json
import re
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from common.jsonio import read_json
from tests.test_claims_binding_ui import _seed_two_requirements


class DiscoverClaimsUiTest(unittest.TestCase):
    def test_researcher_workflow_from_discover_to_claim(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_two_requirements(root)
            workspace = Workspace(root)
            workspace.discover_complete = lambda _prompt, _settings: (
                '{"score": 0.9, "rank": "High", "why": "Names the risk.", "excerpt": "risk assessment"}'
            )
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(workspace))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://{httpd.server_address[0]}:{httpd.server_address[1]}"
            query = "repo=sample-product&source=cra-xml-vii&timestamp=2026-10-14T080000Z"
            try:
                _post(base + "/discover/repos", {"name": "sample-product", "path": str(root / "product")})
                started = _post(
                    base + "/discover/run",
                    {
                        "repo_id": "sample-product",
                        "source_id": "cra-xml-vii",
                        "timestamp": "2026-10-14T080000Z",
                        "assess_limit": "5",
                    },
                )
                found = re.search(r'data-poll="/discover/jobs/([^"]+)"', started)
                self.assertIsNotNone(found)
                job = _wait_job(base, found.group(1))
                self.assertEqual(job["status"], "done")
                overview = _get(base + "/discover/claims?" + query)
                self.assertIn("REQ-A", overview)
                self.assertIn("REQ-B", overview)
                self.assertNotIn("vii-1a", overview)
                self.assertIn("law passage", _get(base + "/discover/claims/REQ-A?" + query))
                page = _get(base + "/discover/claims/REQ-A?" + query)
                self.assertIn("Evidence Source", page)
                self.assertIn("temperature 0", page)
                self.assertIn("not a decision that the product complies", page)
                self.assertNotIn("Model assessment. Signing", page)
                self.assertNotIn("none yet", page)
                self.assertNotIn("Create claim", page)
                self.assertIn("File is present", page)
                self.assertIn("File has the expected content", page)
                self.assertIn("File must not contain this text", page)
                self.assertIn("File is not a placeholder", page)
                self.assertIn("File is recent enough", page)
                self.assertIn("Written by the claimed author", page)
                self.assertIn("Banned package version", page)
                self.assertIn('value="exist"', page)
                self.assertIn('value="text_forbid"', page)
                self.assertIn('data-for="contents"', page)
                self.assertIn('name="min_bytes"', page)
                self.assertIn('name="pattern"', page)
                self.assertIn('name="package"', page)
                self.assertIn('name="max_age_days"', page)
                self.assertIn('name="require_git_author_email"', page)
                self.assertIn("Names the risk.", page)
                self.assertIn("0.9", page)
                document = _get(base + "/discover/claims/REQ-A/file?" + query + "&path=docs/risk-a.md")
                self.assertIn("risk assessment", document)
                self.assertIn("<mark>", document)
                self.assertIn("found in the file", document)
                missing = _get(base + "/discover/claims/REQ-A/file?" + query + "&path=missing.md")
                self.assertIn("existing file", missing)
                self.assertNotIn("<mark>", missing)
                _post(
                    base + "/discover/feedback/vote",
                    {
                        "repo_id": "sample-product",
                        "source_id": "cra-xml-vii",
                        "timestamp": "2026-10-14T080000Z",
                        "requirement_id": "REQ-A",
                        "path": "docs/risk-a.md",
                        "vote": "useful",
                    },
                )
                voted = _get(base + "/discover/claims/REQ-A?" + query)
                self.assertIn("useful", voted)
                self.assertFalse((root / "product" / "claims").exists())
                rejected = _post(
                    base + "/discover/feedback/checks",
                    {
                        "repo_id": "sample-product",
                        "source_id": "cra-xml-vii",
                        "timestamp": "2026-10-14T080000Z",
                        "requirement_id": "REQ-A",
                        "path": "docs/risk-a.md",
                        "check": "contents",
                        "probe_kind": "pattern",
                        "pattern": "",
                    },
                )
                self.assertIn('class="invalid"', rejected)
                self.assertIn('class="save-check"', rejected)
                self.assertFalse((root / "product" / "claims").exists())
                _post(
                    base + "/discover/feedback/checks",
                    {
                        "repo_id": "sample-product",
                        "source_id": "cra-xml-vii",
                        "timestamp": "2026-10-14T080000Z",
                        "requirement_id": "REQ-A",
                        "path": "docs/risk-a.md",
                        "check": "exist",
                    },
                )
                saved = _get(base + "/discover/claims/REQ-A?" + query)
                self.assertIn("File is present", saved)
                claim_files = list((root / "product" / "claims").glob("*.json"))
                self.assertEqual(len(claim_files), 1)
                claim = read_json(claim_files[0])
                self.assertEqual(claim["requirement_id"], "REQ-A")
                self.assertEqual(claim["source"], "documents")
                self.assertEqual(claim["args"], {"path": "docs/risk-a.md"})
                self.assertEqual(claim["checks"], [{"check": "exist", "args": {"paths": ["docs/risk-a.md"]}}])
                self.assertEqual(claim["description"], "Names the risk.")
                self.assertNotIn("signed", claim)
                before = claim_files[0].read_bytes()
                _post(
                    base + "/discover/feedback/checks",
                    {
                        "repo_id": "sample-product",
                        "source_id": "cra-xml-vii",
                        "timestamp": "2026-10-14T080000Z",
                        "requirement_id": "REQ-A",
                        "path": "docs/risk-a.md",
                        "check": "exist",
                    },
                )
                self.assertEqual(claim_files[0].read_bytes(), before)
                opened = _get(
                    base
                    + "/claims?requirement_id=REQ-A&repo_id=sample-product"
                    + "&source_id=cra-xml-vii&timestamp=2026-10-14T080000Z"
                )
                self.assertIn(claim["id"], opened)
                self.assertIn("Unsigned draft", opened)
                self.assertIn("docs/risk-a.md", opened)
                page = _get(base + "/discover/claims/REQ-A?" + query)
                self.assertIn('class="add-open"', page)
                self.assertIn("Add an evidence source candidate", page)
                self.assertNotIn(">Add a finding<", page)
                _post(
                    base + "/discover/feedback/add",
                    {
                        "repo_id": "sample-product",
                        "source_id": "cra-xml-vii",
                        "timestamp": "2026-10-14T080000Z",
                        "requirement_id": "REQ-A",
                        "path": "docs/risk-b.md",
                    },
                )
                added = _get(base + "/discover/claims/REQ-A?" + query + "&open_checks=docs%2Frisk-b.md")
                self.assertIn("docs/risk-b.md", added)
                self.assertIn("Added by hand.", added)
                self.assertIn('data-reopen="1"', added)
                self.assertEqual(len(list((root / "product" / "claims").glob("*.json"))), 1)
                with self.assertRaises(urllib.error.HTTPError):
                    _get(base + "/discover/claims?repo=sample-product&source=cra-xml-vii&timestamp=not-a-copy")
                with self.assertRaises(urllib.error.HTTPError):
                    _get(base + "/discover/claims/NO-SUCH?" + query)
            finally:
                httpd.shutdown()
                httpd.server_close()


def _wait_job(base: str, job_id: str) -> dict:
    import time

    for _ in range(100):
        job = json.loads(_get(base + "/discover/jobs/" + job_id))
        if job.get("status") != "running":
            return job
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def _get(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def _post(url: str, form: dict) -> str:
    data = urllib.parse.urlencode(form).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(request) as response:
        return response.read().decode("utf-8")


if __name__ == "__main__":
    unittest.main()
