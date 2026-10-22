"""Review opens the existing one-Requirement Discovery without hiding the failed Claim."""

from __future__ import annotations

import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from claims.bind import build_claim
from common.canonical import version_digest
from demo_setup import prepare_demo
from review.compile import compile_report, record_decision, write_report


class ReviewDiscoverAgainTest(unittest.TestCase):
    def test_failed_claim_stays_visible_and_popup_is_one_requirement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepare_demo(root)
            ws = Workspace(root)
            old = build_claim(
                claim_id="claim-old",
                requirement_id="R1",
                source="documents",
                args={"path": "docs/old.md"},
                checks=[
                    {
                        "check": "contents",
                        "args": {
                            "path": "docs/old.md",
                            "probes": [{"kind": "headers", "headers": ["# Missing"]}],
                        },
                    }
                ],
                description="The old note was the evidence.",
            )
            ok = build_claim(
                claim_id="claim-ok",
                requirement_id="R1",
                source="documents",
                args={"path": "docs/ok.md"},
                checks=[{"check": "exist", "args": {"paths": ["docs/ok.md"]}}],
                description="The other note is still present.",
            )
            old_args = old["checks"][0]["args"]
            ok_args = ok["checks"][0]["args"]
            report = compile_report(
                run_result={
                    "tool": "curbcheck",
                    "tool_version": "0.0.1a",
                    "packs": [{"id": "house", "version": "0.1.0", "digest": "abc"}],
                    "claims": [
                        {
                            "id": "claim-old",
                            "digest": version_digest(old),
                            "status": "fail",
                            "checks": [
                                {
                                    "index": 0,
                                    "check": "contents",
                                    "args": old_args,
                                    "status": "fail",
                                    "detail": "missing phrase",
                                }
                            ],
                        },
                        {
                            "id": "claim-ok",
                            "digest": version_digest(ok),
                            "status": "pass",
                            "checks": [
                                {
                                    "index": 0,
                                    "check": "exist",
                                    "args": ok_args,
                                    "status": "pass",
                                }
                            ],
                        },
                    ],
                },
                requirements=[_requirement("R1")],
                claims=[old, ok],
            )
            write_report(
                ws.report_path,
                record_decision(report, "I read this run. I am not saying the product meets CRA."),
            )
            before_bytes = ws.report_path.read_bytes()
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ws))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                page = _get(
                    base
                    + "/review?repo=sample-product&source=cra-xml-vii&timestamp=2026-10-21T120000Z"
                )
            finally:
                httpd.shutdown()
                httpd.server_close()
            self.assertEqual(ws.report_path.read_bytes(), before_bytes)

        before, _sep, rest = page.partition("<dialog ")
        dialog, _end, after = rest.partition("</dialog>")
        self.assertIn('data-claim="claim-old"', before)
        self.assertIn('data-requirement="R1"', before)
        self.assertIn("docs/old.md", before)
        self.assertIn("missing phrase", before)
        self.assertIn('data-check="contents"', before)
        self.assertIn("Discover again", before)
        self.assertIn('data-claim="claim-ok"', before)
        self.assertIn('data-requirement="R1"', dialog)
        self.assertNotIn('data-requirement="R2"', dialog)
        self.assertIn(
            "/discover/claims/R1?repo=sample-product&amp;source=cra-xml-vii&amp;timestamp=2026-10-21T120000Z&amp;from=review",
            dialog,
        )
        self.assertNotIn("/discover/claims/R2", page)
        self.assertIn("Find equivalent evidence", dialog)
        self.assertIn('type="button"', dialog)
        self.assertNotIn("<form", dialog)
        self.assertNotIn("claim-old", after)


def _requirement(requirement_id: str) -> dict:
    return {
        "id": requirement_id,
        "pack_id": "house",
        "source": {
            "framework": "test",
            "instrument": "fixture",
            "identifier": "FIX-1",
            "language": "en",
            "url": "https://example.test/law",
        },
        "references": [{"nr": 1, "locator": "1", "law_text": "The product documents the risk."}],
    }


def _get(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


if __name__ == "__main__":
    unittest.main()
