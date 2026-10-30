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
    def test_overview_names_the_section_and_the_seal(self):
        from claims.ui.researcher import overview_page

        overview = overview_page(
            {
                "repo_name": "sample-product",
                "repo_id": "sample-product",
                "section_name": "CRA Annex VII",
                "source_id": "cra-xml-vii",
                "timestamp": "2026-10-14T080000Z",
                "rows": [
                    {
                        "id": "REQ-A",
                        "locator": "VII.3",
                        "findings": 1,
                        "high": 1,
                        "useful": 0,
                        "poor": 0,
                        "claims": 2,
                        "signing": "unsigned draft",
                    }
                ],
            }
        ).decode()
        self.assertIn("<h1>CRA Annex VII</h1>", overview)
        self.assertIn("Requirements in this section", overview)
        self.assertIn("It is not a Claim.", overview)
        self.assertIn(">Source reference</th>", overview)
        self.assertNotIn(">Section</th>", overview)
        self.assertIn("># Claims</th>", overview)
        self.assertIn(">Signature</th>", overview)
        header = overview[overview.index("<thead>"):overview.index("</thead>")]
        self.assertLess(header.index(">Findings</th>"), header.index("># Claims</th>"))
        self.assertLess(header.index("># Claims</th>"), header.index(">Useful</th>"))
        self.assertLess(header.index(">Useful</th>"), header.index(">Poor</th>"))
        self.assertTrue(header.endswith(">Poor</th></tr>"))
        self.assertIn("<td>1</td><td>2</td>", overview)
        self.assertIn("seal-open", overview)
        self.assertIn(">unsigned</span>", overview)
        self.assertNotIn("unsigned draft", overview)
        self.assertIn("VII.3", overview)

    def test_an_empty_list_offers_discover_and_says_why_it_may_stay_empty(self):
        from claims.ui.researcher import requirement_page

        page = requirement_page(
            {
                "repo_id": "sample-product",
                "source_id": "cra-xml-vii",
                "timestamp": "2026-10-14T080000Z",
                "requirement": {
                    "id": "REQ-A",
                    "references": [{"locator": "VII.3"}],
                    "source": {},
                },
                "candidates": [],
                "marks": {},
                "claims": [],
            }
        ).decode()
        self.assertIn('action="/discover/run"', page)
        self.assertIn('name="repo_id" value="sample-product"', page)
        self.assertIn('name="source_id" value="cra-xml-vii"', page)
        self.assertIn('name="timestamp" value="2026-10-14T080000Z"', page)
        self.assertIn(">Discover</button>", page)
        self.assertIn("search hints", page)
        self.assertIn("no evidence to claim", page)
        self.assertNotIn("Run Discover, or add one with +.", page)

    def test_a_different_why_is_green_and_the_saved_motivation_is_struck(self):
        from claims.ui.researcher import requirement_page

        page = requirement_page(
            {
                "repo_id": "sample-product",
                "source_id": "cra-xml-vii",
                "timestamp": "2026-10-14T080000Z",
                "requirement": {
                    "id": "REQ-A",
                    "references": [{"locator": "VII.3"}],
                    "source": {"instrument": "CRA", "identifier": "CELEX:32024R2847"},
                },
                "candidates": [
                    {
                        "path": "docs/risk-a.md",
                        "why": "Names the risk.",
                        "assessment_state": "assessed",
                        "rank": "High",
                        "score": 0.9,
                    },
                    {
                        "path": "docs/other.md",
                        "why": "Only a candidate.",
                        "assessment_state": "assessed",
                        "rank": "Low",
                        "score": 0.2,
                    },
                    {
                        "path": "docs/plain.md",
                        "why": "Kept aside.",
                        "assessment_state": "assessed",
                        "rank": "Low",
                        "score": 0.1,
                    },
                ],
                "marks": {"docs/plain.md": {"dismissed_why": "Kept aside."}},
                "claims": [
                    {
                        "id": "REQ-A-docs__risk-a.md",
                        "requirement_id": "REQ-A",
                        "source": "documents",
                        "args": {"path": "docs/risk-a.md"},
                        "description": "The reviewed file documents the product risks.",
                        "checks": [{"check": "exist", "args": {"paths": ["docs/risk-a.md"]}}],
                    },
                    {
                        "id": "REQ-A-docs__kept.md",
                        "requirement_id": "REQ-A",
                        "source": "documents",
                        "args": {"path": "docs/kept.md"},
                        "description": "This claim stays when discovery misses the file.",
                        "checks": [{"check": "exist", "args": {"paths": ["docs/kept.md"]}}],
                    },
                    {
                        "id": "REQ-A-docs__plain.md",
                        "requirement_id": "REQ-A",
                        "source": "documents",
                        "args": {"path": "docs/plain.md"},
                        "description": "A saved line.",
                        "checks": [{"check": "exist", "args": {"paths": ["docs/plain.md"]}}],
                    },
                ],
            }
        ).decode()
        self.assertIn("<h1>Claims Editor</h1>", page)
        self.assertIn(">Instrument</span><strong>CRA</strong>", page)
        self.assertIn(">Identifier</span><strong>CELEX:32024R2847</strong>", page)
        self.assertIn(">Locator</span><strong>VII.3</strong>", page)
        self.assertIn("Law text", page)
        self.assertIn('class="ref-law law-flow"', page)
        self.assertIn('href="/requirements/requirement/REQ-A">Details</a>', page)
        self.assertNotIn("<h2>Requirement text</h2>", page)
        self.assertIn('id="show-suggestions" checked', page)
        self.assertIn("Show discovered claim candidates", page)
        self.assertIn('class="hits-table show-suggestions"', page)
        self.assertIn('class="motivation-current has-suggestion"', page)
        self.assertIn("suggestion-row", page)
        self.assertIn(">Motivation ", page)
        self.assertEqual(page.count('class="motivation-old"'), 1)
        self.assertEqual(page.count('class="motivation-new"'), 1)
        self.assertIn('name="choice" value="keep"', page)
        self.assertIn('name="choice" value="take"', page)
        self.assertIn("The reviewed file documents the product risks.", page)
        self.assertIn("Names the risk.", page)
        self.assertIn("Only a candidate.", page)
        self.assertNotIn('class="motivation-new">Only a candidate.', page)
        self.assertIn("docs/kept.md", page)
        self.assertIn("This claim stays when discovery misses the file.", page)
        self.assertIn("score-help", page)

    def test_clicking_keeps_the_claim_or_copies_the_sentence(self):
        import tempfile

        from claims.bind import build_claim, sign_claim, write_claim
        from common.signing import generate_keypair
        from discovery.feedback import load_feedback

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_two_requirements(root)
            claim = build_claim(
                claim_id="REQ-A-docs__risk-a.md",
                requirement_id="REQ-A",
                source="documents",
                args={"path": "docs/risk-a.md"},
                checks=[{"check": "exist", "args": {"paths": ["docs/risk-a.md"]}}],
                description="Old motivation.",
            )
            write_claim(root / "product" / "curbpack" / "claims", claim)
            workspace = Workspace(root)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(workspace))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://{httpd.server_address[0]}:{httpd.server_address[1]}"
            form = {
                "repo_id": "sample-product",
                "source_id": "cra-xml-vii",
                "timestamp": "2026-10-14T080000Z",
                "requirement_id": "REQ-A",
                "path": "docs/risk-a.md",
                "why": "New sentence.",
            }
            try:
                _post(base + "/discover/repos", {"name": "sample-product", "path": str(root / "product")})
                _post(base + "/discover/feedback/motivation", {**form, "choice": "keep"})
                kept = read_json(root / "product" / "curbpack" / "claims" / "REQ-A-docs__risk-a.md.json")
                self.assertEqual(kept["description"], "Old motivation.")
                self.assertNotIn("signed", kept)
                feedback = load_feedback(root, "sample-product", "cra-xml-vii", "2026-10-14T080000Z")
                self.assertEqual(
                    feedback["requirements"]["REQ-A"]["docs/risk-a.md"]["dismissed_why"],
                    "New sentence.",
                )
                _post(base + "/discover/feedback/motivation", {**form, "choice": "take"})
                taken = read_json(root / "product" / "curbpack" / "claims" / "REQ-A-docs__risk-a.md.json")
                self.assertEqual(taken["description"], "New sentence.")
                self.assertEqual(taken["checks"], claim["checks"])
                private, _public = generate_keypair()
                sealed = sign_claim(taken, name="QA", private_key=private, at="2026-10-14T08:00:00Z")
                write_claim(root / "product" / "curbpack" / "claims", sealed)
                _post(
                    base + "/discover/feedback/motivation",
                    {**form, "choice": "take", "why": "Newer sentence."},
                )
                still = read_json(root / "product" / "curbpack" / "claims" / "REQ-A-docs__risk-a.md.json")
                self.assertEqual(still["description"], "New sentence.")
                self.assertIn("signed", still)
                _post(
                    base + "/discover/feedback/motivation",
                    {**form, "choice": "take", "why": "Newer sentence.", "unsign": "1"},
                )
                unsigned = read_json(root / "product" / "curbpack" / "claims" / "REQ-A-docs__risk-a.md.json")
                self.assertEqual(unsigned["description"], "Newer sentence.")
                self.assertNotIn("signed", unsigned)
            finally:
                httpd.shutdown()
                httpd.server_close()

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
                self.assertFalse((root / "product" / "curbpack" / "claims").exists())
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
                self.assertFalse((root / "product" / "curbpack" / "claims").exists())
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
                claim_files = list((root / "product" / "curbpack" / "claims").glob("*.json"))
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
                self.assertEqual(len(list((root / "product" / "curbpack" / "claims").glob("*.json"))), 1)
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
