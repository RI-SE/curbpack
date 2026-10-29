"""The demo page shows real objects. It is not a substitute for the domain tests."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from demo_setup import prepare_demo


class UiSmokeTest(unittest.TestCase):
    def test_pages_show_the_saved_requirement_and_a_real_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepare_demo(root)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                cover = _get(base + "/")
                self.assertIn("Pack Editor", cover)
                self.assertIn("No review report.", cover)
                self.assertIn("Discover", cover)
                self.assertIn("Developer", cover)
                # Sample Prepare lives under packs/; it is not the active pilot Pack.
                self.assertIn("author packs from law text", cover)
                self.assertNotIn("CRA-ANNEX-VII-RISK", cover)
                requirement = _get(base + "/requirement")
                self.assertIn("cybersecurity risks", requirement)
                self.assertIn("CRA-ANNEX-VII-RISK", requirement)
                discovered = _get(base + "/discover")
                self.assertIn("Add repo", discovered)
                self.assertIn(">Pack</th>", discovered)
                self.assertIn("Section", discovered)
                self.assertIn(">Copy</th>", discovered)
                self.assertIn("curbpack.json", discovered)
                self.assertNotIn("docs/threat-model-draft.md", discovered)
                _post(base + "/scaffold", {"path": "docs/annex-vii/risk_assessment.md"})
                path = "docs/annex-vii/risk_assessment.md"
                _post(
                    base + "/claims",
                    {
                        "id": "claim-risk",
                        "requirement_id": "CRA-ANNEX-VII-RISK",
                        "source": "documents",
                        "severity": "high",
                        "description": "The risk assessment file is the reviewed evidence.",
                        "args": json.dumps({"path": path}),
                        "checks": json.dumps(
                            [
                                {"check": "exist", "args": {"paths": [path]}},
                                {
                                    "check": "contents",
                                    "args": {
                                        "path": path,
                                        "probes": [
                                            {"kind": "size", "bytes": 200, "op": ">="},
                                            {"kind": "headers", "headers": ["# Risk Assessment"]},
                                        ],
                                    },
                                },
                            ]
                        ),
                    },
                )
                check = _post(base + "/check", {"repo_id": "sample-product", "action": "check"})
                self.assertIn("claim-risk", check)
                self.assertIn("fail", check)
                self.assertIn("not a legal conclusion", check)
                review = _get(base + "/review")
                self.assertIn("not saved", review)
                self.assertIn("Compile writes the report", review)
                self.assertIn("no field for a conclusion that the product meets CRA", review)
                self.assertIn("not verification of that commit", review)
                self.assertIn("claim-risk", review)
                reports_dir = root / "product" / "curbpack" / "reports"
                self.assertFalse(reports_dir.exists() and any(reports_dir.glob("review-report_*.json")))
                try:
                    _post(
                        base + "/review",
                        {"decision": "The stub is not an assessment. I am not saying the product meets CRA."},
                    )
                    self.fail("saving a decision must wait until Compile writes the file")
                except urllib.error.HTTPError as exc:
                    self.assertEqual(exc.code, 400)
                self.assertFalse(reports_dir.exists() and any(reports_dir.glob("review-report_*.json")))
                compiled = _post(base + "/review/compile", {"repo_id": "sample-product"})
                reports = sorted(reports_dir.glob("review-report_*.json"))
                self.assertEqual(len(reports), 1)
                self.assertNotIn("Compile writes the report", compiled)
                self.assertNotIn("not saved", compiled)
                self.assertIn("no field for a conclusion that the product meets CRA", compiled)
                self.assertIn("not verification of that commit", compiled)
                self.assertFalse((root / "product" / ".curbpack" / "review-report.json").exists())
                self.assertFalse((root / "product" / "docs" / "reports" / "review-report.json").exists())
                saved = _post(
                    base + "/review",
                    {"decision": "The stub is not an assessment. I am not saying the product meets CRA."},
                )
                self.assertIn("The stub is not an assessment", saved)
                self.assertIn("unsigned", saved.lower())
            finally:
                httpd.shutdown()
                httpd.server_close()


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
