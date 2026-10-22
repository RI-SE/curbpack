"""The Review popup greys a passed candidate and still shows it."""

from __future__ import annotations

import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from checks.run import build_run_result
from claims.bind import build_claim, write_claim
from common.jsonio import write_json
from common.store import save_run_result
from discovery.repos import add_repo, load_repos, save_repos
from tests.test_claims_binding_ui import _seed_two_requirements

QUERY = "repo=sample-product&source=cra-xml-vii&timestamp=2026-10-14T080000Z"


class ReviewCoverageUiTest(unittest.TestCase):
    def test_review_popup_greys_passed_path_and_leaves_it_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_two_requirements(root)
            product = root / "product"
            passed = build_claim(
                claim_id="claim-a",
                requirement_id="REQ-A",
                source="documents",
                args={"path": "docs/risk-a.md"},
                checks=[{"check": "exist", "args": {"paths": ["docs/risk-a.md"]}}],
                description="The risk note is present.",
            )
            failed = build_claim(
                claim_id="claim-b",
                requirement_id="REQ-A",
                source="documents",
                args={"path": "docs/risk-b.md"},
                checks=[
                    {
                        "check": "contents",
                        "args": {
                            "path": "docs/risk-b.md",
                            "probes": [{"kind": "size", "bytes": 200, "op": ">="}],
                        },
                    }
                ],
                description="The other note was supposed to contain a phrase.",
            )
            write_claim(product / "claims", passed)
            write_claim(product / "claims", failed)
            save_run_result(
                product / ".curbpack" / "run-result.json",
                build_run_result(
                    product,
                    [passed, failed],
                    [{"id": "cra-xml-baseline", "version": "0.1.0", "digest": "abc"}],
                ),
            )
            write_json(
                root / "jobs" / "discover-fixture.json",
                {
                    "repo_id": "sample-product",
                    "source_id": "cra-xml-vii",
                    "timestamp": "2026-10-14T080000Z",
                    "results": [
                        {
                            "requirement_id": "REQ-A",
                            "candidates": [
                                {"path": "docs/risk-a.md", "excerpt": "risk", "assessment_state": "not_assessed"},
                                {"path": "docs/risk-b.md", "excerpt": "other", "assessment_state": "not_assessed"},
                            ],
                        }
                    ],
                },
            )
            save_repos(root, add_repo(root, load_repos(root), name="sample-product", path=str(product)))
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                plain = _get(base + "/discover/claims/REQ-A?" + QUERY)
                launched = _get(base + "/discover/claims/REQ-A?" + QUERY + "&from=review")
            finally:
                httpd.shutdown()
                httpd.server_close()

        self.assertIn("docs/risk-a.md", plain)
        self.assertIn("docs/risk-b.md", plain)
        self.assertNotIn("Already covered", plain)
        self.assertIn("docs/risk-a.md", launched)
        self.assertIn("docs/risk-b.md", launched)
        passed_row = _hit(launched, "docs/risk-a.md")
        failed_row = _hit(launched, "docs/risk-b.md")
        self.assertIn("covered", passed_row)
        self.assertIn("Already covered — passed in the selected Check run", passed_row)
        self.assertNotIn("hidden", passed_row.split(">", 1)[0])
        self.assertNotIn("covered", failed_row.split('class="', 1)[1].split('"', 1)[0])
        self.assertNotIn("Already covered", failed_row)


def _hit(page: str, path: str) -> str:
    needle = f'data-path="{path}"'
    start = page.index(needle)
    start = page.rfind("<tr", 0, start)
    end = page.index("</tr>", start)
    return page[start:end]


def _get(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


if __name__ == "__main__":
    unittest.main()
