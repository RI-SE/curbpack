"""VL-06: a changed Requirement shows the Claims bound to its previous digest."""

from __future__ import annotations

import copy
import html
import inspect
import json
import tempfile
import threading
import unittest
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from claims.bind import build_claim, sign_claim, write_claim
from common.signing import generate_keypair
from claims.impact import claims_affected_by_requirement
from common.canonical import version_digest
from common.jsonio import write_json
from common.store import load_requirement, save_pack, save_requirement
from discovery.door import set_open_repo
from discovery.repos import add_repo, load_repos, save_repos
from requirements.editing import apply_edits
from requirements.extract.pipeline import draft_pack, extract_annex_vii_risk
from requirements.workspace import create_extraction_copy, mark_selected
from studio.pack.pages import editor_page


class AffectedClaimsTest(unittest.TestCase):
    def test_a_changed_requirement_lists_the_claim_bound_to_the_previous_digest(self):
        """VL-06 VL06-01. The Requirement change is reported and the Claim is not modified."""
        requirement = extract_annex_vii_risk()
        claim = build_claim(
            claim_id="claim-bound",
            requirement=requirement,
            source="documents",
            args={"path": "docs/present.md"},
            checks=[{"check": "exist", "args": {"paths": ["docs/present.md"]}}],
            description="The file is the evidence for this Requirement.",
        )
        other = build_claim(
            claim_id="claim-other",
            requirement=apply_edits(requirement, {"note": "An older note."}),
            source="documents",
            args={"path": "docs/other.md"},
            checks=[],
            description="This Claim was bound to an older payload.",
        )
        changed = apply_edits(requirement, {"note": "The note changed."})
        before = copy.deepcopy(claim)
        found = claims_affected_by_requirement([claim, other], requirement, changed)
        self.assertEqual([item["id"] for item in found], ["claim-bound"])
        self.assertEqual(found[0]["recorded"]["namespace"], requirement["namespace"])
        self.assertEqual(found[0]["recorded"]["pack_id"], requirement["pack_id"])
        self.assertEqual(found[0]["recorded"]["requirement_id"], requirement["id"])
        self.assertEqual(found[0]["recorded"]["requirement_digest"], version_digest(requirement))
        self.assertEqual(found[0]["current"]["namespace"], changed["namespace"])
        self.assertEqual(found[0]["current"]["pack_id"], changed["pack_id"])
        self.assertEqual(found[0]["current"]["requirement_id"], changed["id"])
        self.assertEqual(found[0]["current"]["digest"], version_digest(changed))
        self.assertEqual(claim, before)

    def test_an_unchanged_digest_reports_no_newly_stale_claim(self):
        """VL-06 VL06-02. A save that keeps the payload digest adds no stale Claim."""
        requirement = extract_annex_vii_risk()
        claim = build_claim(
            claim_id="claim-bound",
            requirement=requirement,
            source="documents",
            args={"path": "docs/present.md"},
            checks=[],
            description="The file is the evidence for this Requirement.",
        )
        self.assertEqual(claims_affected_by_requirement([claim], requirement, requirement), [])

    def test_a_run_result_and_a_review_report_stay_unchanged(self):
        """VL-06 VL06-07. Listing affected Claims does not rewrite historical records."""
        requirement = extract_annex_vii_risk()
        claim = build_claim(
            claim_id="claim-bound",
            requirement=requirement,
            source="documents",
            args={"path": "docs/present.md"},
            checks=[],
            description="The file is the evidence for this Requirement.",
        )
        changed = apply_edits(requirement, {"note": "The note changed."})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_result = root / "run-result.json"
            report = root / "review-report.json"
            run_result.write_text('{"claims":[]}\n', encoding="utf-8")
            report.write_text('{"decision":"recorded"}\n', encoding="utf-8")
            run_bytes = run_result.read_bytes()
            report_bytes = report.read_bytes()
            claims_affected_by_requirement([claim], requirement, changed)
            self.assertEqual(run_result.read_bytes(), run_bytes)
            self.assertEqual(report.read_bytes(), report_bytes)


class RequirementPageImpactTest(unittest.TestCase):
    def test_the_requirement_page_shows_the_affected_claim_after_save_and_reopen(self):
        """VL-06 VL06-04 and VL06-05. The page shows the Claim and writes nothing but the Requirement."""
        requirement = extract_annex_vii_risk()
        pack = draft_pack()
        requirement["namespace"] = pack["namespace"]
        requirement["pack_id"] = pack["id"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            product = root / "product"
            pack_dir = product / "curbpack" / "packs" / pack["id"] / pack["version"]
            save_pack(pack_dir, pack)
            save_requirement(pack_dir, requirement)
            stored = load_requirement(pack_dir / f"{requirement['id']}.json")
            claim = build_claim(
                claim_id="claim-bound",
                requirement=stored,
                source="documents",
                args={"path": "docs/present.md"},
                checks=[{"check": "exist", "args": {"paths": ["docs/present.md"]}}],
                description="The file is the evidence for this Requirement.",
            )
            write_claim(product / "curbpack" / "claims", claim)
            write_json(
                product / "curbpack.json",
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
            save_repos(root, add_repo(root, load_repos(root), name="alpha", path="product"))
            set_open_repo(root, "alpha")
            claim_path = product / "curbpack" / "claims" / "claim-bound.json"
            claim_bytes = claim_path.read_bytes()
            recorded = claim["requirement_digest"]
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://{httpd.server_address[0]}:{httpd.server_address[1]}"
            try:
                page = _post(
                    base + f"/requirements/requirement/{stored['id']}",
                    {
                        "present": "note",
                        "note": "The note changed.",
                        "expected_digest": version_digest(stored),
                        "repo": "alpha",
                        "pack": pack["id"],
                    },
                )
                current = version_digest(load_requirement(pack_dir / f"{stored['id']}.json"))
                self.assertNotEqual(recorded, current)
                self.assertIn('data-affected-claim="claim-bound"', page)
                self.assertIn(f'data-claim-recorded-digest="{recorded}"', page)
                self.assertIn(f'data-claim-current-digest="{current}"', page)
                self.assertIn('href="/claims?repo=alpha', page)
                self.assertIn("#claim-claim-bound", page)
                self.assertIn(f'href="/discover/claims/{stored["id"]}?repo=alpha&amp;pack={pack["id"]}"', page)
                self.assertIn('data-later="1"', page)
                self.assertNotIn("<form", page[page.index('data-later="1"') : page.index('data-later="1"') + 80])
                reopened = _get(base + f"/requirements/requirement/{stored['id']}?repo=alpha&pack={pack['id']}")
                self.assertIn('data-affected-claim="claim-bound"', reopened)
                self.assertEqual(claim_path.read_bytes(), claim_bytes)
                self.assertFalse(any("queue" in path.name for path in product.rglob("*")))
                editor = _get(base + "/claims?repo=alpha")
                self.assertIn("claim-bound", editor)
                self.assertEqual(claim_path.read_bytes(), claim_bytes)
            finally:
                httpd.shutdown()
                httpd.server_close()
            self.assertNotIn("version_digest", inspect.getsource(editor_page))
            compare_ts = Path("studio/pack/pages/compare_form.ts").read_text(encoding="utf-8")
            self.assertNotIn("claims_affected_by_requirement", compare_ts)
            self.assertNotIn("requirement_digest", compare_ts)


class EditorRebindTest(unittest.TestCase):
    def test_rebind_uses_the_namespace_and_pack_and_keeps_the_checks(self):
        """VL-06 VL06-03. The editor shows both bindings, and rebind selects the named Pack."""
        source = _pack("source-pack", "Source Pack")
        owned = _pack("owned-pack", "Owned Pack")
        source_requirement = extract_annex_vii_risk()
        source_requirement["namespace"] = source["namespace"]
        source_requirement["pack_id"] = source["id"]
        owned_requirement = apply_edits(source_requirement, {"note": "Owned note."})
        owned_requirement["namespace"] = owned["namespace"]
        owned_requirement["pack_id"] = owned["id"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            product = root / "product"
            stored_source = _store(product, source, source_requirement)
            stored_owned = _store(product, owned, owned_requirement)
            claim = build_claim(
                claim_id="claim-move",
                requirement=stored_source,
                source="documents",
                args={"path": "docs/present.md"},
                checks=[{"check": "exist", "args": {"paths": ["docs/present.md"]}}],
                description="The file is the evidence for this Requirement.",
            )
            private, _public = generate_keypair()
            sealed = sign_claim(claim, name="QA", private_key=private, at="2026-11-16T12:00:00Z")
            write_claim(product / "curbpack" / "claims", sealed)
            write_json(
                product / "curbpack.json",
                {
                    "packs": [source["id"], owned["id"]],
                    "packs_dir": "curbpack/packs",
                    "claims_dir": "curbpack/claims",
                    "results_dir": "curbpack/results",
                    "reports_dir": "curbpack/reports",
                    "namespace_base": "RISE",
                    "search_hints": {},
                },
            )
            save_repos(root, add_repo(root, load_repos(root), name="alpha", path="product"))
            set_open_repo(root, "alpha")
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://{httpd.server_address[0]}:{httpd.server_address[1]}"
            query = urllib.parse.urlencode(
                {
                    "repo": "alpha",
                    "namespace": stored_owned["namespace"],
                    "pack_id": stored_owned["pack_id"],
                    "requirement_id": stored_owned["id"],
                }
            )
            try:
                page = _get(base + "/claims?" + query)
                self.assertIn(f'data-recorded-namespace="{stored_source["namespace"]}"', page)
                self.assertIn(f'data-recorded-pack="{stored_source["pack_id"]}"', page)
                self.assertIn(f'data-recorded-digest="{version_digest(stored_source)}"', page)
                self.assertIn(f'data-proposed-namespace="{stored_owned["namespace"]}"', page)
                self.assertIn(f'data-proposed-pack="{stored_owned["pack_id"]}"', page)
                self.assertIn(f'data-proposed-digest="{version_digest(stored_owned)}"', page)
                _post(
                    base + "/claims/claim-move/rebind",
                    {
                        "repo": "alpha",
                        "namespace": stored_owned["namespace"],
                        "pack_id": stored_owned["pack_id"],
                        "requirement_id": stored_owned["id"],
                    },
                )
            finally:
                httpd.shutdown()
                httpd.server_close()
            saved = json.loads((product / "curbpack" / "claims" / "claim-move.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["namespace"], stored_owned["namespace"])
            self.assertEqual(saved["pack_id"], stored_owned["pack_id"])
            self.assertEqual(saved["requirement_digest"], version_digest(stored_owned))
            self.assertNotIn("signed", saved)
            self.assertEqual(saved["checks"], sealed["checks"])


class CompareApplyImpactTest(unittest.TestCase):
    def test_compare_apply_shows_the_claim_only_when_the_digest_changes(self):
        """VL-06 VL06-01. Compare Apply uses the Requirement page list and does not write the Claim."""
        base_requirement = extract_annex_vii_risk()
        current = apply_edits(base_requirement, {"note": "Current note."})
        proposed = apply_edits(base_requirement, {"note": "Proposed note."})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            destination = create_extraction_copy(root, "cra-baseline", draft_pack(), at="2026-10-13T090000Z")
            proposal = create_extraction_copy(root, "cra-baseline", draft_pack(), at="2026-10-13T143000Z")
            save_requirement(destination, current)
            save_requirement(proposal, proposed)
            stored = load_requirement(destination / "CRA-ANNEX-VII-RISK.json")
            claim = build_claim(
                claim_id="claim-bound",
                requirement=stored,
                source="documents",
                args={"path": "docs/present.md"},
                checks=[{"check": "exist", "args": {"paths": ["docs/present.md"]}}],
                description="The file is the evidence for this Requirement.",
            )
            product = root / "product"
            write_claim(product / "curbpack" / "claims", claim)
            write_json(
                product / "curbpack.json",
                {
                    "packs": ["cra-baseline"],
                    "packs_dir": "curbpack/packs",
                    "claims_dir": "curbpack/claims",
                    "results_dir": "curbpack/results",
                    "reports_dir": "curbpack/reports",
                    "namespace_base": "RISE",
                    "search_hints": {},
                },
            )
            save_repos(root, add_repo(root, load_repos(root), name="alpha", path="product"))
            set_open_repo(root, "alpha")
            claim_path = product / "curbpack" / "claims" / "claim-bound.json"
            claim_bytes = claim_path.read_bytes()
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://{httpd.server_address[0]}:{httpd.server_address[1]}"
            form = {
                "requirement": "CRA-ANNEX-VII-RISK",
                "proposal": "2026-10-13T143000Z",
                "destination": "2026-10-13T090000Z",
            }
            try:
                unchanged = _post(
                    base + "/requirements/compare/form/apply",
                    {**form, "choice": json.dumps({"note": "old"})},
                )
                self.assertNotIn('data-affected-claim="claim-bound"', unchanged)
                changed = _post(
                    base + "/requirements/compare/form/apply",
                    {**form, "choice": json.dumps({"note": "new"})},
                )
                current_digest = version_digest(load_requirement(destination / "CRA-ANNEX-VII-RISK.json"))
                self.assertNotEqual(current_digest, claim["requirement_digest"])
                self.assertIn('data-affected-claim="claim-bound"', changed)
                self.assertIn(">claim-bound<", changed)
                self.assertIn(f'data-claim-recorded-digest="{claim["requirement_digest"]}"', changed)
                self.assertIn(f'data-claim-current-digest="{current_digest}"', changed)
                self.assertEqual(claim_path.read_bytes(), claim_bytes)
                review = _get(base + _href(changed, "Review Claim"))
                self.assertIn("claim-bound", review)
                self.assertIn(f"Recorded binding", review)
                self.assertIn(claim["requirement_digest"], review)
                self.assertIn("Proposed binding", review)
                self.assertIn(current_digest, review)
                self.assertEqual(claim_path.read_bytes(), claim_bytes)
                discovery = _get(base + _href(changed, "Discovery"))
                self.assertIn("CRA-ANNEX-VII-RISK", discovery)
                self.assertNotIn("an id in this pack", discovery)
                self.assertEqual(claim_path.read_bytes(), claim_bytes)
                self.assertEqual(
                    list((product / "curbpack" / "claims").glob("*.json")),
                    [claim_path],
                )
                saved_requirement = load_requirement(destination / "CRA-ANNEX-VII-RISK.json")
                identity = (
                    f'{saved_requirement["namespace"]} '
                    f'{saved_requirement["pack_id"]} '
                    f'{saved_requirement["id"]}'
                )
                self.assertIn(f"selected>{identity}<", review)
                stamp = "2026-10-13T090000Z"
                _assert_copy_stamp(_href(discovery, "← Claims"), stamp)
                evidence = product / "docs" / "present.md"
                evidence.parent.mkdir(parents=True)
                evidence.write_text("The present file.\n", encoding="utf-8")
                kept = _post_discovery(
                    base,
                    discovery,
                    "/discover/feedback/add",
                    {"path": "docs/present.md", "rationale": "Names the risk."},
                )
                _assert_copy_stamp(_href(kept, "← Claims"), stamp)
                _assert_copy_stamp(_attr(kept, 'class="file-link" href="'), stamp)
                voted = _post_discovery(
                    base,
                    kept,
                    "/discover/feedback/vote",
                    {"path": "docs/present.md", "vote": "useful"},
                )
                _assert_copy_stamp(_href(voted, "← Claims"), stamp)
                _assert_copy_stamp(_attr(voted, 'class="file-link" href="'), stamp)
                motivated = _post_discovery(
                    base,
                    voted,
                    "/discover/feedback/motivation",
                    {"path": "docs/present.md", "choice": "keep", "why": "Names the risk."},
                )
                _assert_copy_stamp(_href(motivated, "← Claims"), stamp)
                checked = _post_discovery(
                    base,
                    motivated,
                    "/discover/feedback/checks",
                    {"path": "docs/present.md", "check": "exist", "claim_source": "documents"},
                )
                _assert_copy_stamp(_href(checked, "← Claims"), stamp)
                _assert_copy_stamp(_attr(checked, 'class="file-link" href="'), stamp)
                self.assertEqual(claim_path.read_bytes(), claim_bytes)
                _post(
                    base + "/claims/claim-bound/rebind",
                    {
                        "repo": "alpha",
                        "namespace": saved_requirement["namespace"],
                        "pack_id": saved_requirement["pack_id"],
                        "requirement_id": saved_requirement["id"],
                        "timestamp": stamp,
                    },
                )
                rebound = json.loads(claim_path.read_text(encoding="utf-8"))
                self.assertEqual(rebound["namespace"], saved_requirement["namespace"])
                self.assertEqual(rebound["pack_id"], saved_requirement["pack_id"])
                self.assertEqual(rebound["requirement_id"], saved_requirement["id"])
                self.assertEqual(rebound["requirement_digest"], current_digest)
                self.assertEqual(rebound["checks"], claim["checks"])
            finally:
                httpd.shutdown()
                httpd.server_close()
            compare_apply = Path("studio/pack/pack_compare.py").read_text(encoding="utf-8")
            self.assertNotIn("claims.impact", compare_apply)
            self.assertNotIn("claims_affected_by_requirement", compare_apply)


class TakeOwnershipImpactTest(unittest.TestCase):
    def test_take_ownership_keeps_the_source_claim_distinct_and_unchanged(self):
        """VL-06 VL06-06 and VL06-07. The source binding is not stale and no historical file changes."""
        pack = draft_pack()
        pack["name"] = "Imported"
        pack["namespace"] = "OTHER/Imported"
        requirement = extract_annex_vii_risk()
        requirement["namespace"] = pack["namespace"]
        requirement["pack_id"] = pack["id"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stamp = "2026-10-13T090000Z"
            source = create_extraction_copy(root, pack["id"], pack, at=stamp)
            save_requirement(source, requirement)
            stored = load_requirement(source / f"{requirement['id']}.json")
            source_claim = build_claim(
                claim_id="claim-source",
                requirement=stored,
                source="documents",
                args={"path": "docs/present.md"},
                checks=[{"check": "exist", "args": {"paths": ["docs/present.md"]}}],
                description="The file is the evidence for the source Requirement.",
            )
            owned_requirement = dict(stored)
            owned_requirement["namespace"] = "RISE/Imported"
            owned_claim = build_claim(
                claim_id="claim-owned",
                requirement=owned_requirement,
                source="documents",
                args={"path": "docs/owned.md"},
                checks=[{"check": "exist", "args": {"paths": ["docs/owned.md"]}}],
                description="The file is the evidence for the owned Requirement.",
            )
            product = root / "product"
            write_claim(product / "curbpack" / "claims", source_claim)
            write_claim(product / "curbpack" / "claims", owned_claim)
            write_json(
                product / "curbpack.json",
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
            run_result = product / "curbpack" / "results" / "run-result.json"
            report = product / "curbpack" / "reports" / "review-report.json"
            run_result.parent.mkdir(parents=True)
            report.parent.mkdir(parents=True)
            run_result.write_text('{"claims":[]}\n', encoding="utf-8")
            report.write_text('{"decision":"recorded"}\n', encoding="utf-8")
            run_bytes = run_result.read_bytes()
            report_bytes = report.read_bytes()
            save_repos(root, add_repo(root, load_repos(root), name="alpha", path="product"))
            set_open_repo(root, "alpha")
            source_bytes = (product / "curbpack" / "claims" / "claim-source.json").read_bytes()
            owned_bytes = (product / "curbpack" / "claims" / "claim-owned.json").read_bytes()
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://{httpd.server_address[0]}:{httpd.server_address[1]}"
            try:
                page = _post(
                    base + f"/requirements/requirement/{stored['id']}",
                    {
                        "timestamp": stamp,
                        "expected_digest": version_digest(stored),
                        "take_ownership": "1",
                    },
                )
                self.assertIn('data-source-claim="claim-source"', page)
                self.assertIn(">claim-source<", page)
                self.assertIn('data-source-namespace="OTHER/Imported"', page)
                source_at = page.index('data-source-claim="claim-source"')
                self.assertNotIn("stale", page[source_at : source_at + 500])
                self.assertIn('data-owned-claim="claim-owned"', page)
                self.assertNotIn('data-binding="stale"', page)
                review = _get(base + _href(page[source_at:], "Review Claim"))
                self.assertIn("Recorded binding", review)
                self.assertIn("OTHER/Imported", review)
                self.assertIn("Proposed binding", review)
                self.assertIn("RISE/Imported", review)
                self.assertEqual(
                    (product / "curbpack" / "claims" / "claim-source.json").read_bytes(),
                    source_bytes,
                )
            finally:
                httpd.shutdown()
                httpd.server_close()
            self.assertEqual((product / "curbpack" / "claims" / "claim-source.json").read_bytes(), source_bytes)
            self.assertEqual((product / "curbpack" / "claims" / "claim-owned.json").read_bytes(), owned_bytes)
            self.assertEqual(run_result.read_bytes(), run_bytes)
            self.assertEqual(report.read_bytes(), report_bytes)
            self.assertFalse(any("queue" in path.name for path in root.rglob("*")))

    def test_save_posts_the_open_working_copy_not_the_selected_one(self):
        """The save form names the open copy, and its digest is checked against that copy."""
        selected_pack = draft_pack()
        foreign_pack = draft_pack()
        foreign_pack["name"] = "Imported"
        foreign_pack["namespace"] = "OTHER/Imported"
        selected_requirement = extract_annex_vii_risk()
        selected_requirement["namespace"] = selected_pack["namespace"]
        selected_requirement["pack_id"] = selected_pack["id"]
        selected_requirement["note"] = "Selected note."
        foreign_requirement = extract_annex_vii_risk()
        foreign_requirement["namespace"] = foreign_pack["namespace"]
        foreign_requirement["pack_id"] = foreign_pack["id"]
        foreign_requirement["note"] = "Foreign note."
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            selected_stamp = "2026-10-13T090000Z"
            foreign_stamp = "2026-10-13T080000Z"
            selected = create_extraction_copy(root, selected_pack["id"], selected_pack, at=selected_stamp)
            foreign = create_extraction_copy(root, foreign_pack["id"], foreign_pack, at=foreign_stamp)
            save_requirement(selected, selected_requirement)
            save_requirement(foreign, foreign_requirement)
            mark_selected(root, selected_pack["id"], selected_stamp)
            stored = load_requirement(foreign / f"{foreign_requirement['id']}.json")
            claim = build_claim(
                claim_id="claim-source",
                requirement=stored,
                source="documents",
                args={"path": "docs/source.md"},
                checks=[{"check": "exist", "args": {"paths": ["docs/source.md"]}}],
                description="The file is the evidence for the source Requirement.",
            )
            product = root / "product"
            write_claim(product / "curbpack" / "claims", claim)
            write_json(
                product / "curbpack.json",
                {
                    "packs": [foreign_pack["id"]],
                    "packs_dir": "curbpack/packs",
                    "claims_dir": "curbpack/claims",
                    "results_dir": "curbpack/results",
                    "reports_dir": "curbpack/reports",
                    "namespace_base": "RISE",
                    "search_hints": {},
                },
            )
            save_repos(root, add_repo(root, load_repos(root), name="alpha", path="product"))
            set_open_repo(root, "alpha")
            selected_bytes = _file_bytes(selected)
            foreign_bytes = _file_bytes(foreign)
            claim_bytes = (product / "curbpack" / "claims" / "claim-source.json").read_bytes()
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(root)))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://{httpd.server_address[0]}:{httpd.server_address[1]}"
            try:
                page = _get(
                    base
                    + f"/requirements/requirement/{stored['id']}?timestamp={foreign_stamp}"
                )
                form = _save_form(page)
                self.assertEqual(_input(form, "timestamp"), foreign_stamp)
                self.assertEqual(_input(form, "expected_digest"), version_digest(stored))
                asked = _post(
                    base + f"/requirements/requirement/{stored['id']}",
                    {
                        "present": "note",
                        "note": "Ownership note.",
                        "timestamp": _input(form, "timestamp"),
                        "expected_digest": _input(form, "expected_digest"),
                    },
                )
                self.assertIn("Take ownership of this Pack?", asked)
                self.assertIn(f'timestamp={foreign_stamp}', html.unescape(_href(asked, "Cancel")))
                confirmation = _save_form(asked)
                self.assertEqual(_input(confirmation, "timestamp"), foreign_stamp)
                self.assertEqual(_input(confirmation, "expected_digest"), version_digest(stored))
                self.assertEqual(_input(confirmation, "take_ownership"), "1")
                rejected = _post(
                    base + f"/requirements/requirement/{stored['id']}",
                    {
                        "present": "note",
                        "note": "Ownership note.",
                        "timestamp": foreign_stamp,
                        "expected_digest": "0" * 64,
                        "take_ownership": "1",
                    },
                )
                self.assertIn("Field Version: expected the digest read before this save", rejected)
                self.assertIn("Namespace <code>OTHER/Imported</code>", rejected)
                self.assertEqual(_input(_save_form(rejected), "timestamp"), foreign_stamp)
            finally:
                httpd.shutdown()
                httpd.server_close()
            self.assertEqual(_file_bytes(selected), selected_bytes)
            self.assertEqual(_file_bytes(foreign), foreign_bytes)
            self.assertEqual(
                (product / "curbpack" / "claims" / "claim-source.json").read_bytes(),
                claim_bytes,
            )


def _file_bytes(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def _save_form(page: str) -> str:
    start = page.index('<form method="post" action="/requirements/requirement/')
    return page[start : page.index("</form>", start)]


def _pack(pack_id: str, name: str) -> dict:
    pack = draft_pack()
    pack["id"] = pack_id
    pack["name"] = name
    pack["namespace"] = f"RISE/{name}"
    return pack


def _store(product: Path, pack: dict, requirement: dict) -> dict:
    directory = product / "curbpack" / "packs" / pack["id"] / pack["version"]
    save_pack(directory, pack)
    save_requirement(directory, requirement)
    return load_requirement(directory / f"{requirement['id']}.json")


def _post(url: str, form: dict) -> str:
    data = urllib.parse.urlencode(form).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(request) as response:
        return response.read().decode("utf-8")


def _get(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def _href(page: str, label: str) -> str:
    marker = f">{label}</a>"
    end = page.index(marker)
    start = page.rindex('href="', 0, end)
    return html.unescape(page[start + 6 : page.index('"', start + 6)])


def _attr(page: str, marker: str) -> str:
    start = page.index(marker) + len(marker)
    return html.unescape(page[start : page.index('"', start)])


def _input(page: str, name: str) -> str:
    marker = f'name="{name}" value="'
    start = page.index(marker) + len(marker)
    return html.unescape(page[start : page.index('"', start)])


def _assert_copy_stamp(href: str, stamp: str) -> None:
    plain = urllib.parse.unquote(href)
    if f"timestamp={stamp}" not in plain or "pack=cra-baseline" not in plain:
        raise AssertionError(href)


def _post_discovery(base: str, page: str, path: str, fields: dict) -> str:
    form = {
        "repo_id": _input(page, "repo_id"),
        "source_id": _input(page, "source_id"),
        "timestamp": _input(page, "timestamp"),
        "pack": _input(page, "pack"),
        "requirement_id": _input(page, "requirement_id"),
    }
    form.update(fields)
    return _post(base + path, form)
