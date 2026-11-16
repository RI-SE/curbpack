"""VL-04: a Claim records the Requirement version it was assessed against."""

from __future__ import annotations

import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from common.canonical import version_digest
from common.errors import ModelError
from common.jsonio import read_json
from common.store import load_requirement
from common.validate import validate_claim
from requirements.extract.pipeline import extract_annex_vii_risk
from tests.test_claims_binding_ui import _new_claim, _post, _seed_two_requirements


def _claim(requirement: dict) -> dict:
    return {
        "id": "claim-annex-vii-risk",
        "requirement_id": requirement["id"],
        "source": "documents",
        "args": {"path": "docs/annex-vii/risk_assessment.md"},
        "description": "The reviewed file is the evidence for this Requirement.",
        "checks": [],
    }


class ClaimBindingFieldsTest(unittest.TestCase):
    def test_a_recorded_binding_is_accepted(self):
        requirement = extract_annex_vii_risk()
        bound = _claim(requirement)
        bound["namespace"] = requirement["namespace"]
        bound["pack_id"] = requirement["pack_id"]
        bound["requirement_digest"] = version_digest(requirement)
        accepted = validate_claim(bound)
        self.assertEqual(accepted["namespace"], requirement["namespace"])
        self.assertEqual(accepted["pack_id"], requirement["pack_id"])
        self.assertEqual(accepted["requirement_digest"], version_digest(requirement))

    def test_a_claim_without_the_binding_is_rejected(self):
        requirement = extract_annex_vii_risk()
        with self.assertRaises(ModelError) as caught:
            validate_claim(_claim(requirement))
        self.assertIn("namespace", str(caught.exception))


class ClaimBindingCreateTest(unittest.TestCase):
    def test_discovery_and_the_claims_editor_record_the_requirement_digest(self):
        with _server() as (root, base):
            requirement = load_requirement(next((root / "product").rglob("REQ-A.json")))
            _post(base + "/claims", _new_claim("claim-editor", "REQ-A", "docs/risk-a.md", "Evidence for A."))
            edited = read_json(root / "product" / "curbpack" / "claims" / "claim-editor.json")
            _assert_binding(self, edited, requirement)

            _post(
                base + "/discover/repos",
                {"name": "sample-product", "path": str(root / "product")},
            )
            _post(
                base + "/discover/feedback/add",
                {
                    "repo_id": "sample-product",
                    "source_id": "cra-xml-vii",
                    "timestamp": "2026-10-14T080000Z",
                    "requirement_id": "REQ-A",
                    "path": "docs/risk-a.md",
                    "rationale": "The file names the risk.",
                },
            )
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
            claim_files = list((root / "product" / "curbpack" / "claims").glob("*.json"))
            discovered = read_json(next(path for path in claim_files if path.name != "claim-editor.json"))
            _assert_binding(self, discovered, requirement)


def _assert_binding(test: unittest.TestCase, claim: dict, requirement: dict) -> None:
    test.assertEqual(claim["namespace"], requirement["namespace"])
    test.assertEqual(claim["pack_id"], requirement["pack_id"])
    test.assertEqual(claim["requirement_id"], requirement["id"])
    test.assertEqual(claim["requirement_digest"], version_digest(requirement))


class _server:
    def __enter__(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        _seed_two_requirements(root)
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        self._httpd = httpd
        base = f"http://{httpd.server_address[0]}:{httpd.server_address[1]}"
        return root, base

    def __exit__(self, exc_type, exc, tb):
        self._httpd.shutdown()
        self._httpd.server_close()
        self._tmp.cleanup()
        return False
