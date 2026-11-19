"""VL-03: a form Compare page reviews one Requirement."""

from __future__ import annotations

import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.server import Workspace, make_handler
from common.canonical import version_digest
from common.store import load_requirement, save_requirement
from requirements.editing import apply_edits
from requirements.extract.pipeline import draft_pack, extract_annex_vii_risk
from requirements.workspace import create_extraction_copy


class CompareFormPageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def _serve(self) -> str:
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(self.root)))
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(httpd.shutdown)
        self.addCleanup(httpd.server_close)
        return f"http://127.0.0.1:{httpd.server_address[1]}"

    def test_the_committed_script_is_served_and_compare_stays(self):
        base = self._serve()
        compare = urllib.request.urlopen(base + "/requirements/compare").read().decode("utf-8")
        self.assertIn("<h1>Compare</h1>", compare)
        request = urllib.request.Request(base + "/requirements/compare/form.js")
        with urllib.request.urlopen(request) as response:
            body = response.read().decode("utf-8")
            content_type = response.headers.get("Content-Type") or ""
        self.assertIn("javascript", content_type)
        self.assertIn("renderCompareForm", body)
        self.assertNotIn("npm install", body)

    def test_json_names_the_current_and_proposed_notes_and_writes_nothing(self):
        import json

        base_requirement = extract_annex_vii_risk()
        current = apply_edits(base_requirement, {"note": "Current note."})
        proposed = apply_edits(base_requirement, {"note": "Proposed note."})
        same = apply_edits(dict(base_requirement, id="REQ-SAME"), {"note": "Same note."})
        destination = create_extraction_copy(
            self.root, "cra-baseline", draft_pack(), at="2026-10-13T090000Z"
        )
        proposal = create_extraction_copy(
            self.root, "cra-baseline", draft_pack(), at="2026-10-13T143000Z"
        )
        save_requirement(destination, current)
        save_requirement(destination, same)
        save_requirement(proposal, proposed)
        save_requirement(proposal, same)
        before = {
            path: path.read_bytes()
            for path in list(destination.rglob("*.json")) + list(proposal.rglob("*.json"))
        }
        base = self._serve()
        query = "proposal=2026-10-13T143000Z&destination=2026-10-13T090000Z"
        changed = json.loads(
            urllib.request.urlopen(
                base + "/requirements/compare/form.json?requirement=CRA-ANNEX-VII-RISK&" + query
            ).read().decode("utf-8")
        )
        unchanged = json.loads(
            urllib.request.urlopen(
                base + "/requirements/compare/form.json?requirement=REQ-SAME&" + query
            ).read().decode("utf-8")
        )
        self.assertEqual(changed["current"]["note"], "Current note.")
        self.assertEqual(changed["proposed"]["note"], "Proposed note.")
        self.assertEqual(changed["destination_digest"], version_digest(current))
        self.assertEqual(changed["source_digest"], version_digest(proposed))
        self.assertEqual(changed["changed"], ["note"])
        self.assertEqual(unchanged["changed"], [])
        after = {
            path: path.read_bytes()
            for path in list(destination.rglob("*.json")) + list(proposal.rglob("*.json"))
        }
        self.assertEqual(after, before)

    def test_the_list_shows_changes_for_the_extract_and_the_import_pair(self):
        import urllib.error

        from common.jsonio import write_json
        from common.store import save_pack
        from discovery.door import created_curbpack, set_open_repo
        from discovery.repos import add_repo, load_repos, save_repos
        from requirements.workspace import mark_selected
        from studio.pack.pack_exchange import export_pack_zip

        base_requirement = extract_annex_vii_risk()
        current = apply_edits(base_requirement, {"note": "Current note."})
        proposed = apply_edits(base_requirement, {"note": "Proposed note."})
        same = apply_edits(dict(base_requirement, id="REQ-SAME"), {"note": "Same note."})
        create_extraction_copy(self.root, "cra-baseline", draft_pack(), at="2026-10-13T090000Z")
        create_extraction_copy(self.root, "cra-baseline", draft_pack(), at="2026-10-13T143000Z")
        destination = self.root / "cra-baseline" / "2026-10-13T090000Z"
        proposal = self.root / "cra-baseline" / "2026-10-13T143000Z"
        save_requirement(destination, current)
        save_requirement(destination, same)
        save_requirement(proposal, proposed)
        save_requirement(proposal, same)
        base = self._serve()
        listed = urllib.request.urlopen(
            base
            + "/requirements/copy?proposal=2026-10-13T143000Z&destination=2026-10-13T090000Z"
        ).read().decode("utf-8")
        self.assertIn("<th>New</th>", listed)
        self.assertIn(
            'href="/requirements/compare/form?requirement=CRA-ANNEX-VII-RISK'
            '&amp;proposal=2026-10-13T143000Z&amp;destination=2026-10-13T090000Z"',
            listed,
        )
        self.assertIn(">Changes</a>", listed)
        same_row = listed.split("REQ-SAME", 1)[1].split("</tr>", 1)[0]
        self.assertNotIn("Changes", same_row)
        compare = urllib.request.urlopen(base + "/requirements/compare").read().decode("utf-8")
        self.assertIn("<h1>Compare</h1>", compare)

        mark_selected(self.root, "cra-baseline", "2026-10-13T090000Z")
        imported = apply_edits(base_requirement, {"note": "Imported note."})
        imported_pack = dict(draft_pack(), version="1.1.0")
        folder = self.root / "zip-source"
        save_pack(folder, imported_pack)
        save_requirement(folder, imported)
        save_requirement(folder, same)
        payload, _rows = export_pack_zip(folder, {})
        repo = self.root / "product"
        repo.mkdir()
        write_json(repo / "curbpack.json", created_curbpack(namespace_base="RISE", packs=["cra-baseline"]))
        save_repos(self.root, add_repo(self.root, load_repos(self.root), name="Product", path=str(repo)))
        set_open_repo(self.root, "product")
        boundary = "vl03boundarytoken"
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="archive"; filename="pack.zip"\r\n'
            "Content-Type: application/zip\r\n\r\n"
        ).encode("utf-8") + payload + f"\r\n--{boundary}--\r\n".encode("utf-8")

        class _NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        opener = urllib.request.build_opener(_NoRedirect)
        try:
            opener.open(
                urllib.request.Request(
                    base + "/requirements",
                    data=body,
                    method="POST",
                    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                )
            )
            self.fail("import did not redirect")
        except urllib.error.HTTPError as exc:
            location = exc.headers.get("Location") or ""
            exc.close()
        self.assertIn("proposal=", location)
        self.assertIn("destination=2026-10-13T090000Z", location)
        imported_list = urllib.request.urlopen(base + location).read().decode("utf-8")
        self.assertIn("<th>New</th>", imported_list)
        self.assertIn("CRA-ANNEX-VII-RISK", imported_list)
        self.assertIn(">Changes</a>", imported_list)
        self.assertIn(
            'href="/requirements/requirement/CRA-ANNEX-VII-RISK?timestamp=2026-10-13T090000Z&amp;proposal=',
            imported_list,
        )

    def test_import_without_a_selected_copy_has_no_changes_link(self):
        import urllib.error

        from common.jsonio import write_json
        from common.store import save_pack
        from discovery.door import created_curbpack, set_open_repo
        from discovery.repos import add_repo, load_repos, save_repos
        from studio.pack.pack_exchange import export_pack_zip

        folder = self.root / "zip-source"
        save_pack(folder, draft_pack())
        save_requirement(folder, apply_edits(extract_annex_vii_risk(), {"note": "Imported note."}))
        payload, _rows = export_pack_zip(folder, {})
        repo = self.root / "product"
        repo.mkdir()
        write_json(repo / "curbpack.json", created_curbpack(namespace_base="RISE", packs=["cra-baseline"]))
        save_repos(self.root, add_repo(self.root, load_repos(self.root), name="Product", path=str(repo)))
        set_open_repo(self.root, "product")
        boundary = "vl03boundarytoken"
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="archive"; filename="pack.zip"\r\n'
            "Content-Type: application/zip\r\n\r\n"
        ).encode("utf-8") + payload + f"\r\n--{boundary}--\r\n".encode("utf-8")

        class _NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        opener = urllib.request.build_opener(_NoRedirect)
        base = self._serve()
        try:
            opener.open(
                urllib.request.Request(
                    base + "/requirements",
                    data=body,
                    method="POST",
                    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                )
            )
            self.fail("import did not redirect")
        except urllib.error.HTTPError as exc:
            location = exc.headers.get("Location") or ""
            exc.close()
        self.assertEqual(location, "/requirements/copy?imported=1")
        page = urllib.request.urlopen(base + location).read().decode("utf-8")
        self.assertNotIn("<th>New</th>", page)
        self.assertNotIn(">Changes</a>", page)

    def test_node_checks_the_disclosure_and_select_all(self):
        import subprocess

        root = Path(__file__).resolve().parents[1]
        completed = subprocess.run(
            ["node", "--test", "tests/vl03_compare_form.test.mjs"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def _pair(self, *, namespace: str = "RISE/CRA baseline", name: str = "CRA baseline"):
        from common.jsonio import write_json
        from discovery.door import created_curbpack, set_open_repo
        from discovery.repos import add_repo, load_repos, save_repos

        base_requirement = extract_annex_vii_risk()
        current_source = {
            "framework": "EU",
            "instrument": "CRA",
            "url": "https://old.example/cra",
            "identifier": "CELEX",
            "language": "en",
        }
        proposed_source = {
            "framework": "SE",
            "instrument": "CRA",
            "url": "https://new.example/cra",
            "identifier": "CELEX",
            "language": "en",
        }
        current = apply_edits(
            base_requirement,
            {
                "note": "Current note.",
                "remediation_hint": "Current hint.",
                "source": current_source,
            },
        )
        proposed = apply_edits(
            base_requirement,
            {
                "note": "Proposed note.",
                "remediation_hint": "Proposed hint.",
                "source": proposed_source,
            },
        )
        if namespace != "RISE/CRA baseline":
            pack = dict(draft_pack(), name=name, namespace=namespace)
            current["namespace"] = namespace
            proposed["namespace"] = namespace
        else:
            pack = draft_pack()
        destination = create_extraction_copy(
            self.root, "cra-baseline", pack, at="2026-10-13T090000Z"
        )
        proposal = create_extraction_copy(
            self.root, "cra-baseline", pack, at="2026-10-13T143000Z"
        )
        save_requirement(destination, current)
        save_requirement(proposal, proposed)
        repo = self.root / "product"
        repo.mkdir()
        write_json(repo / "curbpack.json", created_curbpack(namespace_base="RISE", packs=["cra-baseline"]))
        save_repos(self.root, add_repo(self.root, load_repos(self.root), name="Product", path=str(repo)))
        set_open_repo(self.root, "product")
        return destination, proposal

    def test_apply_writes_only_the_new_leaves_and_opens_the_editor(self):
        import json
        import urllib.parse

        destination, _proposal = self._pair()
        base = self._serve()
        form = urllib.request.urlopen(
            base
            + "/requirements/compare/form?requirement=CRA-ANNEX-VII-RISK"
            + "&proposal=2026-10-13T143000Z&destination=2026-10-13T090000Z"
        ).read().decode("utf-8")
        self.assertIn('href="/requirements/copy?proposal=2026-10-13T143000Z&amp;destination=2026-10-13T090000Z"', form)
        self.assertIn(">Cancel</a>", form)
        before = (destination / "CRA-ANNEX-VII-RISK.json").read_bytes()
        urllib.request.urlopen(base + "/requirements/copy?proposal=2026-10-13T143000Z&destination=2026-10-13T090000Z").read()
        self.assertEqual((destination / "CRA-ANNEX-VII-RISK.json").read_bytes(), before)
        posted = urllib.parse.urlencode(
            {
                "requirement": "CRA-ANNEX-VII-RISK",
                "proposal": "2026-10-13T143000Z",
                "destination": "2026-10-13T090000Z",
                "choice": json.dumps({"note": "new", "remediation_hint": "old"}),
            }
        ).encode("utf-8")
        editor = urllib.request.urlopen(
            urllib.request.Request(
                base + "/requirements/compare/form/apply",
                data=posted,
                method="POST",
            )
        ).read().decode("utf-8")
        saved = load_requirement(destination / "CRA-ANNEX-VII-RISK.json")
        self.assertEqual(saved["note"], "Proposed note.")
        self.assertEqual(saved["remediation_hint"], "Current hint.")
        self.assertIn("Proposed note.", editor)
        self.assertIn(">Sign</button>", editor)

    def test_apply_keeps_an_unchanged_source_sibling(self):
        import json
        import urllib.parse

        destination, _proposal = self._pair()
        base = self._serve()
        posted = urllib.parse.urlencode(
            {
                "requirement": "CRA-ANNEX-VII-RISK",
                "proposal": "2026-10-13T143000Z",
                "destination": "2026-10-13T090000Z",
                "choice": json.dumps({"source.framework": "new", "source.url": "old"}),
            }
        ).encode("utf-8")
        urllib.request.urlopen(
            urllib.request.Request(
                base + "/requirements/compare/form/apply",
                data=posted,
                method="POST",
            )
        ).read()
        saved = load_requirement(destination / "CRA-ANNEX-VII-RISK.json")
        self.assertEqual(saved["source"]["framework"], "SE")
        self.assertEqual(saved["source"]["url"], "https://old.example/cra")
        self.assertEqual(saved["source"]["instrument"], "CRA")
        self.assertEqual(saved["note"], "Current note.")

    def test_apply_does_not_rewrite_a_foreign_pack(self):
        import json
        import urllib.error
        import urllib.parse

        destination, _proposal = self._pair(namespace="OTHER/Imported", name="Imported")
        before = (destination / "CRA-ANNEX-VII-RISK.json").read_bytes()
        base = self._serve()
        posted = urllib.parse.urlencode(
            {
                "requirement": "CRA-ANNEX-VII-RISK",
                "proposal": "2026-10-13T143000Z",
                "destination": "2026-10-13T090000Z",
                "choice": json.dumps({"note": "new"}),
            }
        ).encode("utf-8")
        try:
            body = urllib.request.urlopen(
                urllib.request.Request(
                    base + "/requirements/compare/form/apply",
                    data=posted,
                    method="POST",
                )
            ).read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8")
        self.assertIn("Take ownership of this Pack?", body)
        self.assertEqual((destination / "CRA-ANNEX-VII-RISK.json").read_bytes(), before)

    def test_a_foreign_addition_is_copied_only_when_new_is_chosen(self):
        import json
        import urllib.error
        import urllib.parse

        destination, proposal = self._pair(namespace="OTHER/Imported", name="Imported")
        extra = dict(load_requirement(proposal / "CRA-ANNEX-VII-RISK.json"))
        extra["id"] = "CRA-ANNEX-VII-EXTRA"
        extra.pop("signed", None)
        save_requirement(proposal, extra)
        before = sorted(path.name for path in destination.glob("*.json"))
        base = self._serve()
        old = urllib.parse.urlencode(
            {
                "requirement": "CRA-ANNEX-VII-EXTRA",
                "proposal": "2026-10-13T143000Z",
                "destination": "2026-10-13T090000Z",
                "choice": json.dumps({"requirement": "old"}),
            }
        ).encode("utf-8")
        try:
            kept = urllib.request.urlopen(
                urllib.request.Request(base + "/requirements/compare/form/apply", data=old, method="POST")
            )
            location = kept.geturl()
            body = kept.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            location = ""
            body = exc.read().decode("utf-8")
        self.assertNotIn("Take ownership of this Pack?", body)
        self.assertIn("/requirements/copy", location or body)
        self.assertEqual(sorted(path.name for path in destination.glob("*.json")), before)
        posted = urllib.parse.urlencode(
            {
                "requirement": "CRA-ANNEX-VII-EXTRA",
                "proposal": "2026-10-13T143000Z",
                "destination": "2026-10-13T090000Z",
                "choice": json.dumps({"requirement": "new"}),
                "take_ownership": "1",
            }
        ).encode("utf-8")
        editor = urllib.request.urlopen(
            urllib.request.Request(base + "/requirements/compare/form/apply", data=posted, method="POST")
        ).read().decode("utf-8")
        self.assertIn("CRA-ANNEX-VII-EXTRA", editor)
        self.assertEqual(sorted(path.name for path in destination.glob("*.json")), before)
        copies = list((self.root / "cra-baseline").glob("*/CRA-ANNEX-VII-EXTRA.json"))
        self.assertEqual(len(copies), 2)

    def test_saving_a_current_requirement_returns_to_the_extract_list(self):
        import urllib.parse
        import urllib.request

        from common.canonical import version_digest
        from common.jsonio import write_json
        from common.store import load_requirement, save_pack, save_requirement
        from discovery.door import created_curbpack, set_open_repo
        from discovery.repos import add_repo, load_repos, save_repos
        from requirements.extract.pipeline import draft_pack, extract_annex_vii_risk
        from requirements.workspace import create_extraction_copy

        current = extract_annex_vii_risk()
        extracted = dict(current)
        extracted["id"] = "REQ-EXTRACTED"
        extracted["note"] = "From the extract."
        pack = draft_pack()
        repo = self.root / "product"
        repo.mkdir()
        write_json(
            repo / "curbpack.json",
            created_curbpack(namespace_base="RISE", packs=["cra-baseline"]),
        )
        pack_dir = repo / "curbpack" / "packs" / "cra-baseline" / pack["version"]
        save_pack(pack_dir, pack)
        save_requirement(pack_dir, current)
        proposal = create_extraction_copy(self.root, "cra-baseline", pack, at="2026-11-19T132441Z")
        save_requirement(proposal, current)
        save_requirement(proposal, extracted)
        save_repos(
            self.root,
            add_repo(self.root, load_repos(self.root), name="Product", path=str(repo)),
        )
        set_open_repo(self.root, "product")
        base = self._serve()
        query = "proposal=2026-11-19T132441Z&pack=cra-baseline&repo=product"
        listing = urllib.request.urlopen(base + "/requirements/copy?" + query).read().decode("utf-8")
        self.assertIn("REQ-EXTRACTED", listing)
        self.assertIn(
            'href="/requirements/requirement/CRA-ANNEX-VII-RISK?pack=cra-baseline&amp;repo=product&amp;proposal=2026-11-19T132441Z"',
            listing,
        )
        editor = urllib.request.urlopen(
            base
            + "/requirements/requirement/CRA-ANNEX-VII-RISK?pack=cra-baseline&repo=product&proposal=2026-11-19T132441Z"
        ).read().decode("utf-8")
        self.assertIn(
            'href="/requirements/copy?proposal=2026-11-19T132441Z&amp;pack=cra-baseline&amp;repo=product"',
            editor,
        )
        digest = version_digest(load_requirement(pack_dir / "CRA-ANNEX-VII-RISK.json"))
        saved = urllib.request.urlopen(
            urllib.request.Request(
                base + "/requirements/requirement/CRA-ANNEX-VII-RISK",
                data=urllib.parse.urlencode(
                    {
                        "repo": "product",
                        "pack": "cra-baseline",
                        "proposal": "2026-11-19T132441Z",
                        "present": "note",
                        "note": "Edited after extract.",
                        "expected_digest": digest,
                    }
                ).encode("utf-8"),
                method="POST",
            )
        ).read().decode("utf-8")
        self.assertIn("Saved.", saved)
        self.assertIn(
            'href="/requirements/copy?proposal=2026-11-19T132441Z&amp;pack=cra-baseline&amp;repo=product"',
            saved,
        )
        again = urllib.request.urlopen(base + "/requirements/copy?" + query).read().decode("utf-8")
        self.assertIn("REQ-EXTRACTED", again)
        self.assertIn("CRA-ANNEX-VII-RISK", again)
