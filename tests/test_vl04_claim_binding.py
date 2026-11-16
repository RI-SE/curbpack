"""VL-04: a Claim records the Requirement version it was assessed against."""

from __future__ import annotations

import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from claims.bind import build_claim, rebind, sign_claim
from common.canonical import version_digest
from common.errors import ModelError
from common.jsonio import read_json
from common.signing import generate_keypair
from common.store import load_requirement, save_requirement
from common.validate import validate_claim
from requirements.extract.pipeline import extract_annex_vii_risk
from tests.test_claims_binding_ui import _edit_claim, _get, _new_claim, _post, _seed_two_requirements


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


class ClaimRebindTest(unittest.TestCase):
    def test_an_ordinary_edit_keeps_the_binding(self):
        requirement = extract_annex_vii_risk()
        sealed = _sealed(requirement)
        same = rebind(sealed, description=sealed["description"])
        self.assertEqual(same["signed"], sealed["signed"])
        edited = rebind(sealed, description="A changed rationale.")
        self.assertNotIn("signed", edited)
        for claim in (same, edited):
            self.assertEqual(claim["namespace"], sealed["namespace"])
            self.assertEqual(claim["pack_id"], sealed["pack_id"])
            self.assertEqual(claim["requirement_id"], sealed["requirement_id"])
            self.assertEqual(claim["requirement_digest"], sealed["requirement_digest"])

    def test_explicit_rebind_updates_the_digest_and_clears_the_seal(self):
        from claims.bind import rebind_requirement

        requirement = extract_annex_vii_risk()
        sealed = _sealed(requirement)
        changed = dict(requirement)
        changed["note"] = "The Requirement text changed."
        rebound = rebind_requirement(sealed, changed)
        self.assertEqual(rebound["requirement_digest"], version_digest(changed))
        self.assertNotIn("signed", rebound)
        self.assertEqual(rebound["namespace"], changed["namespace"])
        self.assertEqual(rebound["pack_id"], changed["pack_id"])
        self.assertEqual(rebound["requirement_id"], changed["id"])

    def test_save_does_not_rebind_and_both_pages_call_rebind(self):
        with _server() as (root, base):
            _post(base + "/claims", _new_claim("claim-keep", "REQ-A", "docs/risk-a.md", "Evidence for A."))
            _post(base + "/claims/claim-keep/sign", {"name": "Pilot Reviewer"})
            form = _edit_claim("docs/risk-a.md", "Evidence for A.", "high")
            form["requirement_id"] = "REQ-B"
            _post(base + "/claims/claim-keep", form)
            kept = read_json(root / "product" / "curbpack" / "claims" / "claim-keep.json")
            self.assertEqual(kept["requirement_id"], "REQ-A")
            self.assertIn("signed", kept)
            editor = _get(base + "/claims")
            self.assertIn('action="/claims/claim-keep/rebind"', editor)

            _post(base + "/claims/claim-keep/rebind", {"requirement_id": "REQ-B"})
            stored = read_json(root / "product" / "curbpack" / "claims" / "claim-keep.json")
            requirement_b = load_requirement(next((root / "product").rglob("REQ-B.json")))
            _assert_binding(self, stored, requirement_b)
            self.assertNotIn("signed", stored)

            _post(base + "/discover/repos", {"name": "sample-product", "path": str(root / "product")})
            page = _get(
                base
                + "/discover/claims/REQ-B?repo=sample-product&source=cra-xml-vii"
                + "&timestamp=2026-10-14T080000Z"
            )
            self.assertIn('action="/discover/claims/rebind"', page)
            product_b = next((root / "product").rglob("REQ-B.json"))
            changed = load_requirement(product_b)
            changed["note"] = "Assessed again."
            save_requirement(product_b.parent, changed)
            _post(
                base + "/discover/claims/rebind",
                {
                    "repo_id": "sample-product",
                    "source_id": "cra-xml-vii",
                    "timestamp": "2026-10-14T080000Z",
                    "requirement_id": "REQ-B",
                    "claim_id": "claim-keep",
                },
            )
            final = read_json(root / "product" / "curbpack" / "claims" / "claim-keep.json")
            _assert_binding(self, final, load_requirement(product_b))


def _sealed(requirement: dict) -> dict:
    claim = build_claim(
        claim_id="claim-annex",
        requirement=requirement,
        source="documents",
        args={"path": "docs/annex-vii/risk_assessment.md"},
        checks=[],
        description="The reviewed file is the evidence for this Requirement.",
    )
    private, _public = generate_keypair()
    return sign_claim(claim, name="QA", private_key=private, at="2026-11-16T10:00:00Z")


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
