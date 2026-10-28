"""Discover → Claims binding must keep the selected Requirement identity."""

from __future__ import annotations

import json
import re
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from claims.bind import (
    build_claim,
    exist_args_for_path,
    read_claim_seal,
    rebind,
    require_requirement_id,
    sign_claim,
    write_claim,
)
from common.errors import ModelError
from common.jsonio import read_json
from common.signing import generate_keypair
from common.store import load_claim, save_requirement
from requirements.extract.pipeline import draft_pack
from requirements.workspace import create_extraction_copy, mark_selected


class BindHelpersTest(unittest.TestCase):
    def test_require_requirement_id_rejects_missing_and_unknown(self):
        with self.assertRaises(ModelError):
            require_requirement_id("", ["REQ-A"])
        with self.assertRaises(ModelError):
            require_requirement_id("CRA-ANNEX-VII-RISK", ["REQ-A", "REQ-B"])
        self.assertEqual(require_requirement_id("REQ-B", ["REQ-A", "REQ-B"]), "REQ-B")

    def test_exist_args_for_path(self):
        self.assertEqual(
            exist_args_for_path("docs/risk-a.md"),
            {"paths": ["docs/risk-a.md"]},
        )
        with self.assertRaises(ModelError):
            exist_args_for_path("  ")

    def test_rebind_keeps_seal_when_payload_unchanged(self):
        private, public = generate_keypair()
        claim = build_claim(
            claim_id="claim-a",
            requirement_id="REQ-A",
            source="documents",
            args={"path": "docs/a.md"},
            checks=[{"check": "exist", "args": {"paths": ["docs/a.md"]}}],
            description="docs/a.md is the evidence.",
        )
        sealed = sign_claim(claim, name="QA", private_key=private, at="2026-10-14T08:00:00Z")
        same = rebind(
            sealed,
            source="documents",
            args={"path": "docs/a.md"},
            checks=[{"check": "exist", "args": {"paths": ["docs/a.md"]}}],
            severity="",
            description="docs/a.md is the evidence.",
        )
        self.assertIn("signed", same)
        self.assertEqual(same["signed"], sealed["signed"])
        moved = rebind(sealed, args={"path": "docs/b.md"})
        self.assertNotIn("signed", moved)
        reading = read_claim_seal(same, {"QA": public})
        self.assertTrue(reading["verifiable"])


class ClaimsBindingUiTest(unittest.TestCase):
    def test_discover_use_path_binds_correct_requirement_for_two_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_two_requirements(root)
            workspace = Workspace(root)
            workspace.discover_complete = lambda _prompt, _settings: (
                '{"score": 0.5, "rank": "Low", "why": "Fixture.", "excerpt": ""}'
            )
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(workspace))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://{httpd.server_address[0]}:{httpd.server_address[1]}"
            try:
                discover = _get(base + "/discover")
                self.assertIn(">Pack</th>", discover)
                self.assertIn("CRA Annex VII", discover)
                self.assertIn("2026-10-14T080000Z", discover)
                _post(
                    base + "/discover/repos",
                    {"name": "sample-product", "path": str(root / "product")},
                )
                requirement_file = root / "cra-xml-baseline" / "2026-10-14T080000Z" / "REQ-A.json"
                before = requirement_file.read_bytes()
                started = _post(
                    base + "/discover/run",
                    {
                        "repo_id": "sample-product",
                        "source_id": "cra-xml-vii",
                        "timestamp": "2026-10-14T080000Z",
                    },
                )
                self.assertIn('class="progress"', started)
                found = re.search(r'data-poll="/discover/jobs/([^"]+)"', started)
                self.assertIsNotNone(found)
                job = _wait_job(base, found.group(1))
                self.assertEqual(job["status"], "done")
                log = "\n".join(job["log_tail"])
                self.assertIn("=== REQ-A", log)
                self.assertIn("=== REQ-B", log)
                self.assertIn("candidates:", log)
                finished = _get(base + "/discover?job=" + found.group(1))
                self.assertIn(">OK<", finished)
                self.assertNotIn("Open claims", finished)
                self.assertNotIn(">Close<", finished)
                self.assertNotIn("Use path", finished)
                self.assertIn(">Edit<", finished)
                self.assertNotRegex(finished, r'class="edit-review"[^>]*hidden')
                self.assertIn(
                    'href="/discover/claims?repo=sample-product&amp;source=cra-xml-vii&amp;timestamp=2026-10-14T080000Z"',
                    finished,
                )
                self.assertNotIn("CRA-ANNEX-VII-RISK", finished)
                self.assertEqual(requirement_file.read_bytes(), before)
                self.assertFalse((root / "product" / "claims").exists())

                claims_empty = _get(base + "/claims")
                self.assertIn("Claim editor", claims_empty)
                self.assertIn("Discovery &amp; Claims", claims_empty)
                self.assertNotIn("New claim", claims_empty)

                _post(base + "/claims", _new_claim("claim-from-a", "REQ-A", "docs/risk-a.md", "Evidence for A."))
                saved_a = read_json(root / "product" / "claims" / "claim-from-a.json")
                self.assertEqual(saved_a["requirement_id"], "REQ-A")
                self.assertEqual(saved_a["source"], "documents")
                self.assertEqual(saved_a["args"], {"path": "docs/risk-a.md"})
                self.assertEqual(saved_a["checks"], [{"check": "exist", "args": {"paths": ["docs/risk-a.md"]}}])
                self.assertNotIn("signed", saved_a)

                _post(base + "/claims", _new_claim("claim-from-b", "REQ-B", "docs/risk-b.md", "Evidence for B."))
                saved_b = read_json(root / "product" / "claims" / "claim-from-b.json")
                self.assertEqual(saved_b["requirement_id"], "REQ-B")
                self.assertEqual(saved_b["args"], {"path": "docs/risk-b.md"})
                self.assertNotEqual(saved_b["requirement_id"], saved_a["requirement_id"])

                listed = _get(base + "/claims")
                self.assertIn("Unsigned draft", listed)
                self.assertIn("law passage for A", listed)
                self.assertIn("law passage for B", listed)

                with self.assertRaises(urllib.error.HTTPError) as caught:
                    _post(base + "/claims", _new_claim("claim-bad", "CRA-ANNEX-VII-RISK", "docs/risk-a.md", "Nope."))
                self.assertEqual(caught.exception.code, 400)
                self.assertFalse((root / "product" / "claims" / "claim-bad.json").exists())
                self.assertEqual(
                    read_json(root / "product" / "claims" / "claim-from-a.json")["requirement_id"],
                    "REQ-A",
                )
            finally:
                httpd.shutdown()
                httpd.server_close()

    def test_sign_edit_reopen_and_direct_create(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_two_requirements(root)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://{httpd.server_address[0]}:{httpd.server_address[1]}"
            try:
                direct = _get(base + "/claims")
                self.assertIn("Claim editor", direct)
                self.assertIn('href="/discover"', direct)
                self.assertNotIn("New claim", direct)
                _post(
                    base + "/claims",
                    _new_claim("claim-direct", "REQ-A", "docs/direct.md", "direct", severity="medium"),
                )
                draft = read_json(root / "product" / "claims" / "claim-direct.json")
                self.assertEqual(draft["requirement_id"], "REQ-A")
                self.assertNotIn("signed", draft)

                reopened = _get(base + "/claims")
                self.assertIn("Unsigned draft", reopened)
                self.assertIn("claim-direct", reopened)

                _post(base + "/claims/claim-direct/sign", {"name": "Pilot Reviewer"})
                sealed_page = _get(base + "/claims")
                self.assertIn("Signed · verifiable", sealed_page)
                sealed = load_claim(root / "product" / "claims" / "claim-direct.json")
                self.assertIn("signed", sealed)

                same_save = _post(
                    base + "/claims/claim-direct",
                    _edit_claim("docs/direct.md", "direct", severity="medium"),
                )
                self.assertIn("Claim saved", same_save)
                still = load_claim(root / "product" / "claims" / "claim-direct.json")
                self.assertIn("signed", still)

                cleared = _post(
                    base + "/claims/claim-direct",
                    _edit_claim("docs/moved.md", "direct", severity="medium"),
                )
                self.assertIn("Previous seal cleared", cleared)
                self.assertIn("Unsigned draft", cleared)
                after = load_claim(root / "product" / "claims" / "claim-direct.json")
                self.assertNotIn("signed", after)
                self.assertEqual(after["requirement_id"], "REQ-A")
                self.assertEqual(after["args"], {"path": "docs/moved.md"})
                self.assertEqual(after["checks"][0]["args"], {"paths": ["docs/moved.md"]})
            finally:
                httpd.shutdown()
                httpd.server_close()

    def test_unknown_requirement_query_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_two_requirements(root)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://{httpd.server_address[0]}:{httpd.server_address[1]}"
            try:
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    _get(base + "/claims?requirement_id=CRA-ANNEX-VII-RISK&path=docs/x.md")
                self.assertEqual(caught.exception.code, 400)
            finally:
                httpd.shutdown()
                httpd.server_close()


def _new_claim(claim_id: str, requirement_id: str, path: str, description: str, severity: str = "high") -> dict:
    return {
        "id": claim_id,
        "requirement_id": requirement_id,
        "source": "documents",
        "severity": severity,
        "description": description,
        "args": json.dumps({"path": path}),
        "checks": json.dumps([{"check": "exist", "args": {"paths": [path]}}]),
    }


def _edit_claim(path: str, description: str, severity: str = "high") -> dict:
    body = _new_claim("unused", "REQ-A", path, description, severity)
    body.pop("id")
    body.pop("requirement_id")
    return body


def _seed_two_requirements(root: Path) -> None:
    pack_id = "cra-xml-baseline"
    stamp = "2026-10-14T080000Z"
    pack = draft_pack()
    pack["id"] = pack_id
    copy = create_extraction_copy(root, pack_id, pack, at=stamp)
    for requirement_id, locator, law, hint in (
        ("REQ-A", "VII.3", "law passage for A", "*risk-a*"),
        ("REQ-B", "VII.4", "law passage for B", "*risk-b*"),
    ):
        save_requirement(
            copy,
            {
                "id": requirement_id,
                "pack_id": pack_id,
                "source": {
                    "framework": "EU",
                    "instrument": "CRA",
                    "identifier": "CELEX:32024R2847",
                    "language": "en",
                    "url": "https://example.invalid/cra",
                },
                "references": [{"nr": 1, "locator": locator, "law_text": law}],
                "discovery_hints": {
                    "concepts": ["risk"],
                    "path_hints": [hint],
                    "sources": [{"source": "documents"}],
                    "expected_evidence": ["process description"],
                },
            },
            published=False,
        )
    mark_selected(root, pack_id, stamp)
    product = root / "product"
    product.mkdir(parents=True)
    (product / "curbpack.json").write_text(
        json.dumps(
            {
                "packs": [pack_id],
                "search_hints": {
                    "exclude_path_globs": ["**/node_modules/**"],
                    "prefer_path_globs": ["**/docs/**"],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (product / "docs").mkdir()
    (product / "docs" / "risk-a.md").write_text("# Risk A\nrisk assessment\n", encoding="utf-8")
    (product / "docs" / "risk-b.md").write_text("# Risk B\nrisk assessment\n", encoding="utf-8")


def _wait_job(base: str, job_id: str) -> dict:
    for _ in range(100):
        job = json.loads(_get(base + "/discover/jobs/" + job_id))
        if job.get("status") != "running":
            return job
        time.sleep(0.05)
    raise AssertionError(f"job {job_id} did not finish")


def _get(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def _post(url: str, form: dict) -> str:
    data = urllib.parse.urlencode(form).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    # Follow redirect to the claims page.
    with urllib.request.urlopen(request) as response:
        return response.read().decode("utf-8")


if __name__ == "__main__":
    unittest.main()
