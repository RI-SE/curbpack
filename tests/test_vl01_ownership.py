"""VL-01: taking ownership copies a foreign Pack and leaves the original."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from common.errors import ModelError
from common.signing import generate_keypair, read_signature, sign_object
from common.store import load_pack_directory, save_pack, save_requirement
from requirements.editing import read_pack_seal, seal_pack_directory
from requirements.ownership import take_ownership


def _pack(**overrides) -> dict:
    document = {
        "id": "cra-baseline",
        "name": "CRA baseline",
        "version": "1.0.0",
        "namespace": "OTHER/CRA baseline",
        "status": "reviewed",
    }
    document.update(overrides)
    return document


def _requirement(requirement_id: str, **overrides) -> dict:
    document = {
        "id": requirement_id,
        "pack_id": "cra-baseline",
        "namespace": "OTHER/CRA baseline",
        "status": "reviewed",
        "source": {
            "framework": "EU",
            "instrument": "CRA",
            "identifier": "VII.3",
            "language": "en",
            "url": "https://example.invalid/cra",
        },
        "references": [{"nr": 1, "locator": "VII.3", "law_text": "Assess the risk."}],
    }
    document.update(overrides)
    return document


def _file_bytes(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


class OwnershipCopyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "source"
        self.destination = self.root / "studio"
        self.destination.mkdir()
        private, public = generate_keypair()
        self.public = public
        save_pack(
            self.source,
            _pack(origin={"namespace": "OLDER/CRA baseline", "pack": "older", "version": "0.1.0"}),
        )
        first = sign_object(
            _requirement(
                "REQ-A",
                origin={
                    "namespace": "OLDER/CRA baseline",
                    "pack": "older",
                    "version": "0.1.0",
                    "requirement": "REQ-A",
                },
            ),
            name="Ada",
            private_key=private,
            at="2026-11-12T12:00:00Z",
        )
        second = sign_object(
            _requirement("REQ-B"),
            name="Ada",
            private_key=private,
            at="2026-11-12T12:00:00Z",
        )
        save_requirement(self.source, first)
        save_requirement(self.source, second)
        seal_pack_directory(
            self.source,
            name="Ada",
            private_key=private,
            at="2026-11-12T12:00:00Z",
        )
        self.before = _file_bytes(self.source)

    def test_confirming_copies_the_pack_and_leaves_the_source(self):
        copied = take_ownership(
            self.source,
            self.destination,
            namespace_base="ACME",
            requirement_id="REQ-A",
            edits={"note": "Owned note."},
            at="2026-11-12T130000Z",
        )
        self.assertEqual(_file_bytes(self.source), self.before)
        self.assertTrue(read_pack_seal(self.source, {"Ada": self.public})["verifiable"])
        pack, requirements = load_pack_directory(copied)
        by_id = {item["id"]: item for item in requirements}
        self.assertEqual(pack["namespace"], "ACME/CRA baseline")
        self.assertEqual(pack["status"], "draft")
        self.assertNotIn("signed", pack)
        self.assertEqual(
            pack["origin"],
            {"namespace": "OTHER/CRA baseline", "pack": "cra-baseline", "version": "1.0.0"},
        )
        self.assertEqual(by_id["REQ-A"]["note"], "Owned note.")
        self.assertNotIn("note", by_id["REQ-B"])
        for requirement in requirements:
            self.assertEqual(requirement["namespace"], "ACME/CRA baseline")
            self.assertEqual(requirement["status"], "draft")
            self.assertNotIn("signed", requirement)
            self.assertEqual(
                requirement["origin"],
                {
                    "namespace": "OTHER/CRA baseline",
                    "pack": "cra-baseline",
                    "version": "1.0.0",
                    "requirement": requirement["id"],
                },
            )
            reading = read_signature(requirement, {"Ada": self.public}, what="requirement")
            self.assertFalse(reading["verifiable"])
            self.assertIn("No signed block", reading["reason"])
        source_pack, source_requirements = load_pack_directory(self.source)
        source_by_id = {item["id"]: item for item in source_requirements}
        self.assertEqual(source_pack["namespace"], "OTHER/CRA baseline")
        self.assertEqual(source_pack["status"], "reviewed")
        self.assertEqual(
            source_pack["origin"],
            {"namespace": "OLDER/CRA baseline", "pack": "older", "version": "0.1.0"},
        )
        self.assertEqual(
            source_by_id["REQ-A"]["origin"]["namespace"],
            "OLDER/CRA baseline",
        )
        self.assertIn("signed", source_by_id["REQ-A"])

    def test_an_existing_target_is_not_overwritten(self):
        existing = self.destination / "cra-baseline" / "2026-11-01T000000Z"
        save_pack(existing, _pack(namespace="ACME/CRA baseline", status="draft"))
        before_existing = _file_bytes(existing)
        with self.assertRaises(ModelError) as caught:
            take_ownership(
                self.source,
                self.destination,
                namespace_base="ACME",
                requirement_id="REQ-A",
                edits={"note": "Owned note."},
                at="2026-11-12T130000Z",
            )
        self.assertEqual(caught.exception.field, "namespace")
        self.assertEqual(_file_bytes(self.source), self.before)
        self.assertEqual(_file_bytes(existing), before_existing)
        self.assertFalse((self.destination / "cra-baseline" / "2026-11-12T130000Z").exists())

    def test_a_failed_edit_leaves_no_partial_copy(self):
        with self.assertRaises(ModelError) as caught:
            take_ownership(
                self.source,
                self.destination,
                namespace_base="ACME",
                requirement_id="REQ-A",
                edits={"not-a-field": "x"},
                at="2026-11-12T130000Z",
            )
        self.assertEqual(caught.exception.field, "not-a-field")
        self.assertEqual(_file_bytes(self.source), self.before)
        self.assertFalse((self.destination / "cra-baseline").exists())

    def test_a_pack_id_cannot_leave_the_workspace(self):
        for unsafe in ("../out", "published/cra"):
            save_pack(self.source, _pack(id=unsafe))
            for requirement_id in ("REQ-A", "REQ-B"):
                save_requirement(
                    self.source,
                    _requirement(requirement_id, pack_id=unsafe),
                )
            with self.assertRaises(ModelError) as caught:
                take_ownership(
                    self.source,
                    self.destination,
                    namespace_base="ACME",
                    requirement_id="REQ-A",
                    edits={"note": "Owned note."},
                    at="2026-11-12T130000Z",
                )
            self.assertEqual(caught.exception.field, "id")
        self.assertFalse((self.destination.parent / "out").exists())
        self.assertFalse((self.destination / "published" / "cra").exists())


def _editor_bytes(model: dict) -> str:
    from studio.pack.pages import editor_page

    return editor_page(model).decode("utf-8")


class EditorFactsTest(unittest.TestCase):
    def test_identity_origin_and_signature_are_separate(self):
        requirement = _requirement(
            "REQ-A",
            namespace="ACME/CRA baseline",
            origin={
                "namespace": "OTHER/CRA baseline",
                "pack": "cra-baseline",
                "version": "1.0.0",
                "requirement": "REQ-A",
            },
        )
        page = _editor_bytes(
            {
                "requirement": requirement,
                "pack_id": "cra-baseline",
                "reading": {
                    "verifiable": False,
                    "who": None,
                    "reason": "No signed block and no signed Git commit. The object is unsigned.",
                },
            }
        )
        self.assertIn('id="requirement-identity"', page)
        self.assertIn("ACME/CRA baseline", page)
        self.assertIn('id="requirement-origin"', page)
        self.assertIn("OTHER/CRA baseline", page)
        self.assertIn('data-signature="unsigned"', page)
        self.assertNotIn("No signed block", page)
        self.assertNotIn('data-signature="draft"', page)
        invalid = _editor_bytes(
            {
                "requirement": _requirement("REQ-A", namespace="ACME/CRA baseline"),
                "pack_id": "cra-baseline",
                "reading": {
                    "verifiable": False,
                    "who": "Ada",
                    "reason": "The certificate does not verify the signature, or name is not the identity on that certificate.",
                },
            }
        )
        self.assertIn('data-signature="invalid"', invalid)
        self.assertIn("Origin namespace", page)
        bare = _editor_bytes(
            {
                "requirement": _requirement("REQ-A", namespace="ACME/CRA baseline"),
                "pack_id": "cra-baseline",
                "reading": {"verifiable": True, "who": "Ada", "when": "2026-11-12T12:00:00Z"},
            }
        )
        self.assertNotIn('id="requirement-origin"', bare)
        self.assertIn('data-signature="valid"', bare)


class EditorOwnershipTest(unittest.TestCase):
    def setUp(self):
        import threading
        from http.server import ThreadingHTTPServer

        from app.server import Workspace, make_handler
        from checks.defaults import created_curbpack
        from common.jsonio import write_json
        from discovery.door import set_open_repo
        from discovery.repos import add_repo, load_repos, save_repos

        self.threading = threading
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / "product"
        self.repo.mkdir()
        write_json(
            self.repo / "curbpack.json",
            created_curbpack(namespace_base="ACME", packs=["cra-baseline"]),
        )
        self.pack_dir = self.repo / "curbpack" / "packs" / "cra-baseline" / "1.0.0"
        save_repos(self.root, add_repo(self.root, load_repos(self.root), name="Product", path=str(self.repo)))
        set_open_repo(self.root, "product")
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Workspace(self.root)))
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(httpd.shutdown)
        self.addCleanup(httpd.server_close)
        self.base = f"http://127.0.0.1:{httpd.server_address[1]}"

    def _store(self, namespace: str) -> dict:
        from common.canonical import version_digest
        from common.store import load_requirement

        save_pack(self.pack_dir, _pack(namespace=namespace, status="draft"))
        save_requirement(self.pack_dir, _requirement("REQ-A", namespace=namespace, status="draft"))
        save_requirement(self.pack_dir, _requirement("REQ-B", namespace=namespace, status="draft"))
        return {
            "repo": "product",
            "pack": "cra-baseline",
            "present": "note",
            "note": "Owned note.",
            "expected_digest": version_digest(load_requirement(self.pack_dir / "REQ-A.json")),
        }

    def _post(self, form: dict) -> str:
        import urllib.error
        import urllib.parse
        import urllib.request

        data = urllib.parse.urlencode(form).encode("utf-8")
        request = urllib.request.Request(
            self.base + "/requirements/requirement/REQ-A",
            data=data,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8")
            raise AssertionError(f"{exc.code} {body}") from exc

    def test_a_matching_namespace_saves_in_place(self):
        form = self._store("ACME/CRA baseline")
        before_dirs = list((self.root / "cra-baseline").glob("*")) if (self.root / "cra-baseline").exists() else []
        page = self._post(form)
        saved = load_pack_directory(self.pack_dir)
        edited = next(item for item in saved[1] if item["id"] == "REQ-A")
        self.assertEqual(edited["note"], "Owned note.")
        self.assertEqual(edited["namespace"], "ACME/CRA baseline")
        self.assertNotIn("origin", edited)
        self.assertIn("Saved.", page)
        self.assertEqual(list((self.root / "cra-baseline").glob("*")) if (self.root / "cra-baseline").exists() else [], before_dirs)

    def test_a_foreign_pack_asks_before_writing(self):
        form = self._store("OTHER/CRA baseline")
        before = _file_bytes(self.pack_dir)
        page = self._post(form)
        self.assertIn("Take ownership of this Pack?", page)
        self.assertIn("You are about to modify a Pack published under another namespace.", page)
        self.assertIn("Take ownership", page)
        self.assertIn("Cancel", page)
        self.assertEqual(_file_bytes(self.pack_dir), before)
        self.assertIn('href="/requirements/requirement/REQ-A?repo=product&amp;pack=cra-baseline"', page)
        return page

    def test_cancel_leaves_the_source(self):
        import urllib.request

        form = self._store("OTHER/CRA baseline")
        before = _file_bytes(self.pack_dir)
        self._post(form)
        with urllib.request.urlopen(
            self.base + "/requirements/requirement/REQ-A?repo=product&pack=cra-baseline"
        ) as response:
            page = response.read().decode("utf-8")
        self.assertIn("REQ-A", page)
        self.assertNotIn("Owned note.", page)
        self.assertEqual(_file_bytes(self.pack_dir), before)

    def test_confirming_edits_the_copy_only(self):
        import html
        import re

        form = self._store("OTHER/CRA baseline")
        before = _file_bytes(self.pack_dir)
        asked = self._post(form)
        self.assertIn("Take ownership of this Pack?", asked)
        form_html = asked.split("<form", 1)[1].split("</form>", 1)[0]
        posted = {
            html.unescape(name): html.unescape(value)
            for name, value in re.findall(
                r'<input type="hidden" name="([^"]*)" value="([^"]*)">',
                form_html,
            )
        }
        self.assertEqual(posted["note"], "Owned note.")
        self.assertEqual(posted["take_ownership"], "1")
        page = self._post(posted)
        self.assertEqual(_file_bytes(self.pack_dir), before)
        copies = list((self.root / "cra-baseline").glob("*/REQ-A.json"))
        self.assertEqual(len(copies), 1)
        copied = load_pack_directory(copies[0].parent)
        edited = next(item for item in copied[1] if item["id"] == "REQ-A")
        self.assertEqual(edited["note"], "Owned note.")
        self.assertEqual(edited["namespace"], "ACME/CRA baseline")
        self.assertEqual(copied[0]["namespace"], "ACME/CRA baseline")
        self.assertNotIn("signed", edited)
        self.assertIn("Owned note.", page)
        self.assertIn('data-signature="unsigned"', page)
        self.assertNotIn("repo=product", page)
        self.assertNotIn("pack=cra-baseline", page)

