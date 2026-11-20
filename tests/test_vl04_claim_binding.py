"""VL-04: a Claim records the Requirement version it was assessed against."""

from __future__ import annotations

import io
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from studio.check.check_page import check_page
from checks.__main__ import main
from checks.run import build_run_result, run_and_write, run_pack_directories
from claims.bind import build_claim, rebind, sign_claim, write_claim
from common.canonical import version_digest
from common.errors import ModelError
from common.jsonio import read_json, write_json
from common.signing import generate_keypair
from common.store import load_requirement, load_run_result, save_pack, save_requirement
from common.validate import validate_claim, validate_run_result
from requirements.extract.pipeline import draft_pack, extract_annex_vii_risk
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
                    "overlap_confirm": "1",
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

    def test_save_keeps_the_binding_and_findings_do_not_offer_rebind(self):
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
            self.assertNotIn('action="/discover/claims/rebind"', page)
            self.assertNotIn(">Rebind</button>", page)
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


class RunResultBindingTest(unittest.TestCase):
    def test_match_stale_and_missing_stay_beside_a_passing_check(self):
        requirement = extract_annex_vii_risk()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            pack = draft_pack()
            pack["id"] = requirement["pack_id"]
            pack["namespace"] = requirement["namespace"]
            pack_dir = repo / "curbpack" / "packs" / pack["id"] / "0.1.0"
            save_pack(pack_dir, pack)
            save_requirement(pack_dir, requirement)
            stored = load_requirement(pack_dir / f"{requirement['id']}.json")
            (repo / "docs").mkdir()
            (repo / "docs" / "present.md").write_text("present\n", encoding="utf-8")
            write_json(
                repo / "curbpack.json",
                {
                    "packs": [pack["id"]],
                    "packs_dir": "curbpack/packs",
                    "claims_dir": "curbpack/claims",
                    "results_dir": "curbpack/results",
                    "reports_dir": "curbpack/reports",
                    "namespace_base": "RISE",
                    "search_hints": {},
                },
            )
            evidence = [{"check": "exist", "args": {"paths": ["docs/present.md"]}}]
            match = _bound_claim("claim-match", stored, evidence)
            stale = _bound_claim("claim-stale", stored, evidence)
            stale["requirement_digest"] = "recorded-other-digest"
            missing = _bound_claim("claim-missing", stored, evidence)
            missing["namespace"] = "OTHER/Pack"
            result = build_run_result(repo, [match, stale, missing], [{"id": pack["id"], "version": "0.1.0", "digest": "pack"}])
            rows = {row["id"]: row for row in result["claims"]}
            self.assertEqual(rows["claim-match"]["binding"], "match")
            self.assertEqual(rows["claim-stale"]["binding"], "stale")
            self.assertEqual(rows["claim-missing"]["binding"], "missing")
            self.assertNotIn("actual_digest", rows["claim-missing"])
            for claim in (match, stale, missing):
                row = rows[claim["id"]]
                self.assertEqual(row["status"], "pass")
                self.assertEqual(row["digest"], version_digest(claim))
                self.assertEqual(row["checks"][0]["status"], "pass")
                self.assertNotIn("binding", row["checks"][0])
                self.assertNotIn("namespace", row["checks"][0])
                self.assertNotIn("requirement_digest", row["checks"][0])
            self.assertEqual(rows["claim-match"]["actual_digest"], version_digest(stored))
            self.assertEqual(rows["claim-stale"]["actual_digest"], version_digest(stored))
            self.assertEqual(rows["claim-match"]["requirement_digest"], version_digest(stored))
            self.assertEqual(rows["claim-missing"]["namespace"], "OTHER/Pack")

    def test_binding_uses_the_pack_directory_this_run_loaded(self):
        """A packs root other than curbpack.json still supplies the Requirement that was checked."""
        requirement = extract_annex_vii_risk()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "product"
            repo.mkdir()
            pack = draft_pack()
            pack["id"] = requirement["pack_id"]
            pack["namespace"] = requirement["namespace"]
            external = root / "packs" / pack["id"] / pack["version"]
            save_pack(external, pack)
            save_requirement(external, requirement)
            stored = load_requirement(external / f"{requirement['id']}.json")
            other = dict(stored)
            other["note"] = "A different copy in the repository packs directory."
            repo_pack = repo / "curbpack" / "packs" / pack["id"] / pack["version"]
            save_pack(repo_pack, pack)
            save_requirement(repo_pack, other)
            (repo / "docs").mkdir()
            (repo / "docs" / "present.md").write_text("present\n", encoding="utf-8")
            write_json(
                repo / "curbpack.json",
                {
                    "packs": [pack["id"]],
                    "packs_dir": "curbpack/packs",
                    "claims_dir": "curbpack/claims",
                    "results_dir": "curbpack/results",
                    "reports_dir": "curbpack/reports",
                    "namespace_base": "RISE",
                    "search_hints": {},
                },
            )
            claim = _bound_claim(
                "claim-loaded",
                stored,
                [{"check": "exist", "args": {"paths": ["docs/present.md"]}}],
            )
            write_claim(repo / "curbpack" / "claims", claim)
            result, code = run_and_write(repo, root / "packs", repo / "out.json")
            self.assertEqual(code, 0)
            self.assertEqual(result["claims"][0]["status"], "pass")
            self.assertEqual(result["claims"][0]["binding"], "match")
            self.assertEqual(result["claims"][0]["actual_digest"], version_digest(stored))
            write_claim(repo / "claims", claim)
            listed, listed_code = run_pack_directories(repo, [external])
            self.assertEqual(listed_code, 0)
            self.assertEqual(listed["claims"][0]["binding"], "match")
            self.assertEqual(listed["claims"][0]["actual_digest"], version_digest(stored))

    def test_stdout_names_a_stale_binding_beside_a_passing_check(self):
        """The text summary shows the binding. The exit code stays the Check result."""
        requirement = extract_annex_vii_risk()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            pack = draft_pack()
            pack["id"] = requirement["pack_id"]
            pack["namespace"] = requirement["namespace"]
            pack_dir = repo / "curbpack" / "packs" / pack["id"] / pack["version"]
            save_pack(pack_dir, pack)
            save_requirement(pack_dir, requirement)
            stored = load_requirement(pack_dir / f"{requirement['id']}.json")
            (repo / "docs").mkdir()
            (repo / "docs" / "present.md").write_text("present\n", encoding="utf-8")
            write_json(
                repo / "curbpack.json",
                {
                    "packs": [pack["id"]],
                    "packs_dir": "curbpack/packs",
                    "claims_dir": "curbpack/claims",
                    "results_dir": "curbpack/results",
                    "reports_dir": "curbpack/reports",
                    "namespace_base": "RISE",
                    "search_hints": {},
                },
            )
            claim = _bound_claim(
                "claim-stale",
                stored,
                [{"check": "exist", "args": {"paths": ["docs/present.md"]}}],
            )
            claim["requirement_digest"] = "recorded-other-digest"
            write_claim(repo / "curbpack" / "claims", claim)
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = main(["--repo", str(repo)])
            text = buf.getvalue()
            self.assertEqual(code, 0)
            self.assertIn("pass    claim-stale binding stale", text)
            self.assertIn(f"requirement recorded-other-digest actual {version_digest(stored)}", text)
            self.assertNotIn("run-result_", text)

    def test_a_historical_run_result_loads_without_being_rewritten(self):
        historical = {
            "tool": "curbcheck",
            "tool_version": "0.0.1a",
            "packs": [{"id": "house", "version": "0.1.0", "digest": "pack"}],
            "claims": [
                {
                    "id": "claim-old",
                    "digest": "claim",
                    "status": "pass",
                    "checks": [
                        {"index": 0, "check": "exist", "args": {"paths": ["a.md"]}, "status": "pass"}
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run-result.json"
            write_json(path, historical)
            before = path.read_bytes()
            loaded = load_run_result(path)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(set(loaded["claims"][0]), {"id", "digest", "status", "checks"})
        leaked = dict(historical)
        leaked["claims"] = [dict(historical["claims"][0])]
        leaked["claims"][0]["checks"] = [dict(historical["claims"][0]["checks"][0], binding="stale")]
        with self.assertRaises(ModelError):
            validate_run_result(leaked)


class CheckPageBindingTest(unittest.TestCase):
    def test_a_passing_check_still_shows_stale_and_missing_bindings(self):
        """The Check page copies the stored binding. It does not replace the Check status."""
        result = {
            "claims": [
                {
                    "id": "claim-stale",
                    "status": "pass",
                    "binding": "stale",
                    "namespace": "RISE/Stale Pack",
                    "pack_id": "stale-pack",
                    "requirement_id": "REQ-STALE",
                    "requirement_digest": "recorded-stale-digest",
                    "actual_digest": "actual-stale-digest",
                    "checks": [
                        {"index": 0, "check": "exist", "args": {"paths": ["a.md"]}, "status": "pass"}
                    ],
                },
                {
                    "id": "claim-missing",
                    "status": "pass",
                    "binding": "missing",
                    "namespace": "RISE/Missing Pack",
                    "pack_id": "missing-pack",
                    "requirement_id": "REQ-MISSING",
                    "requirement_digest": "recorded-missing-digest",
                    "checks": [
                        {"index": 0, "check": "exist", "args": {"paths": ["a.md"]}, "status": "pass"}
                    ],
                },
                {
                    "id": "claim-match",
                    "status": "pass",
                    "binding": "match",
                    "checks": [
                        {"index": 0, "check": "exist", "args": {"paths": ["a.md"]}, "status": "pass"}
                    ],
                },
                {
                    "id": "claim-old",
                    "status": "pass",
                    "checks": [
                        {"index": 0, "check": "exist", "args": {"paths": ["a.md"]}, "status": "pass"}
                    ],
                },
            ]
        }
        page = check_page(result, 0).decode()
        self.assertEqual(page.count("data-binding="), 3)
        stale = page[page.index('data-binding="stale"'):page.index('data-binding="missing"')]
        self.assertLess(
            stale.index("requirement recorded-stale-digest"),
            stale.index("actual actual-stale-digest"),
        )
        self.assertIn("RISE/Stale Pack", stale)
        self.assertIn("stale-pack", stale)
        self.assertIn("REQ-STALE", stale)
        missing = page[page.index('data-binding="missing"'):page.index('data-binding="match"')]
        self.assertIn("requirement recorded-missing-digest", missing)
        self.assertIn("RISE/Missing Pack", missing)
        self.assertIn("missing-pack", missing)
        self.assertIn("REQ-MISSING", missing)
        self.assertNotIn("actual ", missing)
        match = page[page.index('data-binding="match"'):page.index("</td>", page.index('data-binding="match"'))]
        self.assertTrue(match.endswith(">match"))
        self.assertNotIn("requirement", match)
        self.assertNotIn("actual", match)
        self.assertNotIn('data-binding="pass"', page)
        self.assertEqual(page.count('data-check-status="pass"'), 4)


def _bound_claim(claim_id: str, requirement: dict, checks: list) -> dict:
    return build_claim(
        claim_id=claim_id,
        requirement=requirement,
        source="documents",
        args={"path": "docs/present.md"},
        checks=checks,
        description="The file is the evidence for this Requirement.",
    )
