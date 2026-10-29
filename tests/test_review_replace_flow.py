"""Add a replacement Claim, retire the old one, then check and sign."""

from __future__ import annotations

import tempfile
import threading
import unittest
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from checks.run import reports_dir
from claims.bind import build_claim, read_claim, write_claim
from claims.ui.coverage import REPLACEMENT_UNCHECKED
from common.jsonio import read_json
from common.keystore import trust_store
from common.validate import validate_curbpack_config
from discovery.door import set_open_repo
from discovery.repos import add_repo, load_repos, save_repos
from review.compile import read_report_signature
from tests.test_claims_binding_ui import _seed_two_requirements

CONTEXT = {
    "repo_id": "sample-product",
    "source_id": "cra-xml-vii",
    "timestamp": "2026-10-14T080000Z",
}


class ReplaceThenReviewTest(unittest.TestCase):
    def test_add_delete_check_and_sign_keeps_each_action_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_two_requirements(root)
            product = root / "product"
            claims_dir = product / "curbpack" / "claims"
            old = build_claim(
                claim_id="claim-old",
                requirement_id="REQ-A",
                source="documents",
                args={"path": "docs/risk-a.md"},
                checks=[
                    {
                        "check": "contents",
                        "args": {
                            "path": "docs/risk-a.md",
                            "probes": [{"kind": "size", "bytes": 200, "op": ">="}],
                        },
                    }
                ],
                description="The first note was the evidence.",
            )
            write_claim(claims_dir, old)
            save_repos(root, add_repo(root, load_repos(root), name="sample-product", path=str(product)))
            set_open_repo(root, "sample-product")
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            try:
                _post(base + "/claims/claim-old/sign", {**CONTEXT, "name": "Ada Reviewer"})
                old_bytes = (claims_dir / "claim-old.json").read_bytes()
                _post(
                    base + "/discover/feedback/add",
                    {**CONTEXT, "requirement_id": "REQ-A", "path": "docs/risk-b.md", "rationale": "A replacement note."},
                )
                _post(
                    base + "/discover/feedback/checks",
                    {**CONTEXT, "requirement_id": "REQ-A", "path": "docs/risk-b.md", "check": "exist"},
                )
                self.assertEqual((claims_dir / "claim-old.json").read_bytes(), old_bytes)
                created = [path.name for path in claims_dir.glob("*.json")]
                self.assertEqual(len(created), 2)
                editor = _get(base + "/claims?" + urllib.parse.urlencode(CONTEXT))
                self.assertIn("claim-old", editor)
                self.assertIn(REPLACEMENT_UNCHECKED, editor)
                _post(base + "/claims/claim-old/retire", CONTEXT)
                self.assertFalse((claims_dir / "claim-old.json").is_file())
                self.assertEqual(len(list(claims_dir.glob("*.json"))), 1)
                checked = _post(base + "/check", {"repo_id": "sample-product", "action": "check"})
                self.assertIn("pass", checked)
                self.assertNotIn("claim-old", checked)
                replacement = next(claims_dir.glob("*.json"))
                signed = _post(
                    base + f"/claims/{replacement.stem}/sign",
                    {**CONTEXT, "name": "Ada Reviewer"},
                )
                self.assertIn("Signed", signed)
                _post(base + "/review/compile", {"repo_id": "sample-product"})
                decided = _post(
                    base + "/review",
                    {"decision": "I read the replacement run. I am not saying the product meets CRA."},
                )
                self.assertIn("I read the replacement run", decided)
                sealed = _post(base + "/review/sign", {"name": "Ada Reviewer"})
                self.assertIn("verifiable yes", sealed.lower())
            finally:
                httpd.shutdown()
                httpd.server_close()
            claim = read_claim(replacement)
            self.assertEqual(claim["signed"]["name"], "Ada Reviewer")
            config = validate_curbpack_config(read_json(product / "curbpack.json"))
            reports = sorted(reports_dir(product, config).glob("review-report_*.json"))
            self.assertEqual(len(reports), 1)
            report = read_json(reports[0])
            self.assertFalse((product / ".curbpack" / "review-report.json").exists())
            self.assertFalse((product / "docs" / "reports" / "review-report.json").exists())
            reading = read_report_signature(report, trust_store(root / "keys"))
            self.assertTrue(reading["verifiable"])
            self.assertEqual(reading["who"], "Ada Reviewer")
            self.assertNotIn("claim-old", [row.get("id") for row in report["run_result"]["claims"]])


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
