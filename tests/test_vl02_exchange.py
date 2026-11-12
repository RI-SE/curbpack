"""VL-02: a Pack ZIP keeps the directory bytes and reports signatures."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from common.errors import ModelError
from common.signing import generate_keypair, sign_object
from common.store import save_pack, save_requirement
from requirements.editing import seal_pack_directory
from requirements.workspace import selected_copy
from studio.pack.pack_exchange import export_pack_zip, import_pack_zip


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


def _members(payload: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        return {info.filename: archive.read(info) for info in archive.infolist()}


class ExportZipTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name) / "pack"
        self.private, self.public = generate_keypair()
        self.other, _other_public = generate_keypair()
        save_pack(self.directory, _pack())
        save_requirement(
            self.directory,
            sign_object(
                _requirement("REQ-A"),
                name="Ada",
                private_key=self.private,
                at="2026-11-12T12:00:00Z",
            ),
        )
        save_requirement(self.directory, _requirement("REQ-B"))
        save_requirement(
            self.directory,
            sign_object(
                _requirement("REQ-C"),
                name="Ada",
                private_key=self.other,
                at="2026-11-12T12:00:00Z",
            ),
        )
        (self.directory / ".keep").write_bytes(b"dot\n")
        seal_pack_directory(
            self.directory,
            name="Ada",
            private_key=self.private,
            at="2026-11-12T12:00:00Z",
        )

    def test_the_zip_matches_the_pack_directory(self):
        payload, _rows = export_pack_zip(self.directory, {"Ada": self.public})
        found = _members(payload)
        expected = {
            path.relative_to(self.directory).as_posix(): path.read_bytes()
            for path in sorted(self.directory.rglob("*"))
            if path.is_file()
        }
        self.assertEqual(found, expected)

    def test_export_reports_every_signature_and_still_returns_the_zip(self):
        payload, rows = export_pack_zip(self.directory, {"Ada": self.public})
        self.assertTrue(payload.startswith(b"PK"))
        by_title = {row["title"]: row["status"] for row in rows}
        self.assertEqual(by_title["Pack"], "valid")
        self.assertEqual(by_title["REQ-A"], "valid")
        self.assertEqual(by_title["REQ-B"], "unsigned")
        self.assertEqual(by_title["REQ-C"], "invalid")

    def test_a_symlink_is_not_exported(self):
        outside = Path(self.tmp.name) / "outside.txt"
        outside.write_bytes(b"nope\n")
        (self.directory / "escape").symlink_to(outside)
        with self.assertRaises(ModelError):
            export_pack_zip(self.directory, {"Ada": self.public})


def _file_bytes(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def _facts(rows: list[dict]) -> dict[str, tuple]:
    return {
        row["title"]: (row["status"], row["method"], row["signer"], row["version"])
        for row in rows
    }


class ImportZipTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name) / "source"
        self.studio = Path(self.tmp.name) / "studio"
        self.studio.mkdir()
        private, public = generate_keypair()
        self.trust = {"Ada": public}
        save_pack(
            self.source,
            _pack(origin={"namespace": "OLDER/CRA baseline", "pack": "older", "version": "0.1.0"}),
        )
        save_requirement(
            self.source,
            sign_object(
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
            ),
        )
        save_requirement(self.source, _requirement("REQ-B"))
        (self.source / ".keep").write_bytes(b"dot\n")
        seal_pack_directory(
            self.source,
            name="Ada",
            private_key=private,
            at="2026-11-12T12:00:00Z",
        )
        self.before = _file_bytes(self.source)
        self.payload, self.exported_rows = export_pack_zip(self.source, self.trust)

    def test_import_keeps_the_bytes_and_the_verification(self):
        installed, rows = import_pack_zip(
            self.payload,
            self.studio,
            self.trust,
            at="2026-11-12T140000Z",
        )
        self.assertEqual(installed, selected_copy(self.studio, "cra-baseline"))
        self.assertEqual(_file_bytes(installed), self.before)
        self.assertEqual(_file_bytes(self.source), self.before)
        self.assertEqual(_facts(rows), _facts(self.exported_rows))

    def test_a_single_top_directory_is_the_pack_directory(self):
        wrapped = io.BytesIO()
        with zipfile.ZipFile(wrapped, "w") as archive:
            for name, data in self.before.items():
                archive.writestr(f"cra-baseline/{name}", data)
        installed, _rows = import_pack_zip(
            wrapped.getvalue(),
            self.studio,
            self.trust,
            at="2026-11-12T140000Z",
        )
        self.assertEqual(_file_bytes(installed), self.before)

    def test_the_same_identity_is_not_imported_twice(self):
        import_pack_zip(self.payload, self.studio, self.trust, at="2026-11-12T140000Z")
        first = self.studio / "cra-baseline" / "2026-11-12T140000Z"
        before = _file_bytes(first)
        with self.assertRaises(ModelError) as caught:
            import_pack_zip(self.payload, self.studio, self.trust, at="2026-11-12T150000Z")
        self.assertEqual(caught.exception.field, "version")
        self.assertEqual(_file_bytes(first), before)
        self.assertFalse((self.studio / "cra-baseline" / "2026-11-12T150000Z").exists())

    def test_a_different_version_is_another_pack(self):
        import shutil

        import_pack_zip(self.payload, self.studio, self.trust, at="2026-11-12T140000Z")
        other = Path(self.tmp.name) / "other"
        shutil.copytree(self.source, other)
        pack = json.loads((other / "pack.json").read_text())
        pack["version"] = "1.1.0"
        pack.pop("signed", None)
        (other / "pack.json").write_text(json.dumps(pack, indent=2) + "\n")
        payload, _rows = export_pack_zip(other, self.trust)
        installed, _rows = import_pack_zip(
            payload,
            self.studio,
            self.trust,
            at="2026-11-12T150000Z",
        )
        self.assertEqual(installed.name, "2026-11-12T150000Z")
        self.assertTrue((self.studio / "cra-baseline" / "2026-11-12T140000Z").is_dir())


def _zip(members: dict[str, bytes], *, symlink: str | None = None) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in members.items():
            info = zipfile.ZipInfo(name)
            if name == symlink:
                info.external_attr = 0o120777 << 16
            archive.writestr(info, data)
    return buffer.getvalue()


class UnsafeZipTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.studio = Path(self.tmp.name) / "studio"
        self.studio.mkdir()

    def test_unsafe_archives_leave_the_workspace_empty(self):
        archives = [
            _zip({"../out.txt": b"x", "pack.json": b"{}"}),
            _zip({"pack.json": b"{}", "escape": b"link"}, symlink="escape"),
            _zip({"/pack.json": b"{}"}),
            _zip({"pack.json": b"{}", "foo\\bar.json": b"{}"}),
            _zip({"one/pack.json": b"{}", "two/pack.json": b"{}"}),
            _zip({"cra/pack.json": b"{}", "note.txt": b"x"}),
            _zip({"REQ-A.json": b"{}"}),
        ]
        for payload in archives:
            with self.assertRaises(ModelError):
                import_pack_zip(payload, self.studio, {}, at="2026-11-12T140000Z")
            self.assertFalse((self.studio.parent / "out.txt").exists())
            self.assertEqual(list(self.studio.iterdir()), [])


class SignedImportTest(unittest.TestCase):
    def test_invalid_and_unsigned_requirements_still_import(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        source = Path(tmp.name) / "pack"
        studio = Path(tmp.name) / "studio"
        studio.mkdir()
        private, public = generate_keypair()
        other, _other_public = generate_keypair()
        save_pack(source, _pack())
        save_requirement(source, _requirement("REQ-B"))
        save_requirement(
            source,
            sign_object(
                _requirement("REQ-C"),
                name="Ada",
                private_key=other,
                at="2026-11-12T12:00:00Z",
            ),
        )
        (source / ".keep").write_bytes(b"dot\n")
        before = _file_bytes(source)
        payload, _rows = export_pack_zip(source, {"Ada": public})
        installed, rows = import_pack_zip(
            payload,
            studio,
            {"Ada": public},
            at="2026-11-12T140000Z",
        )
        self.assertEqual(_file_bytes(installed), before)
        by_title = {row["title"]: row["status"] for row in rows}
        self.assertEqual(by_title["REQ-B"], "unsigned")
        self.assertEqual(by_title["REQ-C"], "invalid")


class RequirementsPageTest(unittest.TestCase):
    def setUp(self):
        import threading
        from http.server import ThreadingHTTPServer

        from app.server import Workspace, make_handler
        from discovery.door import created_curbpack, set_open_repo
        from discovery.repos import add_repo, load_repos, save_repos
        from requirements.workspace import mark_selected

        self.threading = threading
        self.Workspace = Workspace
        self.make_handler = make_handler
        self.created_curbpack = created_curbpack
        self.set_open_repo = set_open_repo
        self.add_repo = add_repo
        self.load_repos = load_repos
        self.save_repos = save_repos
        self.mark_selected = mark_selected
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def _serve(self):
        from http.server import ThreadingHTTPServer

        httpd = ThreadingHTTPServer(("127.0.0.1", 0), self.make_handler(self.Workspace(self.root)))
        thread = self.threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(httpd.shutdown)
        self.addCleanup(httpd.server_close)
        return f"http://127.0.0.1:{httpd.server_address[1]}"

    def test_export_zip_is_the_selected_working_copy(self):
        import urllib.parse
        import urllib.request

        stamp = "2026-11-12T140000Z"
        directory = self.root / "cra-xml-baseline" / stamp
        save_pack(
            directory,
            _pack(id="cra-xml-baseline", name="CRA XML", namespace="RISE/CRA XML"),
        )
        save_requirement(
            directory,
            _requirement("REQ-A", pack_id="cra-xml-baseline", namespace="RISE/CRA XML"),
        )
        self.mark_selected(self.root, "cra-xml-baseline", stamp)
        expected, _rows = export_pack_zip(directory, {})
        base = self._serve()
        page = urllib.request.urlopen(
            base + "/requirements/export?document=cra-annex-vii"
        ).read().decode("utf-8")
        self.assertIn('name="destination"', page)
        self.assertIn("Export ZIP", page)
        data = urllib.parse.urlencode(
            {"document": "cra-annex-vii", "exchange": "zip"}
        ).encode("utf-8")
        with urllib.request.urlopen(
            urllib.request.Request(base + "/requirements/export", data=data, method="POST")
        ) as response:
            self.assertEqual(response.headers.get("Content-Type"), "application/zip")
            self.assertEqual(response.read(), expected)

    def test_import_opens_edit_compare_and_ownership(self):
        import html
        import re
        import urllib.error
        import urllib.parse
        import urllib.request

        from common.jsonio import write_json

        repo = self.root / "product"
        repo.mkdir()
        write_json(
            repo / "curbpack.json",
            self.created_curbpack(namespace_base="ACME", packs=["cra-xml-baseline"]),
        )
        self.save_repos(
            self.root,
            self.add_repo(self.root, self.load_repos(self.root), name="Product", path=str(repo)),
        )
        self.set_open_repo(self.root, "product")
        source = self.root / "source"
        save_pack(
            source,
            _pack(id="imported-pack", name="Imported", namespace="OTHER/Imported"),
        )
        save_requirement(
            source,
            _requirement("REQ-A", pack_id="imported-pack", namespace="OTHER/Imported"),
        )
        before = _file_bytes(source)
        payload, _rows = export_pack_zip(source, {})
        base = self._serve()
        sources = urllib.request.urlopen(base + "/requirements").read().decode("utf-8")
        self.assertIn('name="archive"', sources)
        boundary = "vl02boundarytoken"
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="archive"; filename="pack.zip"\r\n'
            "Content-Type: application/zip\r\n\r\n"
        ).encode("utf-8") + payload + f"\r\n--{boundary}--\r\n".encode("utf-8")
        request = urllib.request.Request(
            base + "/requirements",
            data=body,
            method="POST",
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        try:
            with urllib.request.urlopen(request) as response:
                copied = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            self.fail(exc.read().decode("utf-8"))
        self.assertIn("status unsigned", copied)
        self.assertIn("REQ-A", copied)
        editor = urllib.request.urlopen(
            base + "/requirements/requirement/REQ-A"
        ).read().decode("utf-8")
        self.assertIn(">Sign</button>", editor)
        compared = urllib.request.urlopen(base + "/requirements/compare").read().decode("utf-8")
        self.assertIn("Working copy", compared)
        stamp = next(path.name for path in (self.root / "imported-pack").iterdir() if path.is_dir())
        self.assertIn(stamp, compared)
        digest = re.search(r'name="expected_digest" value="([^"]*)"', editor).group(1)
        asked = urllib.request.urlopen(
            urllib.request.Request(
                base + "/requirements/requirement/REQ-A",
                data=urllib.parse.urlencode(
                    {"present": "note", "note": "Owned note.", "expected_digest": digest}
                ).encode("utf-8"),
                method="POST",
            )
        ).read().decode("utf-8")
        self.assertIn("Take ownership of this Pack?", asked)
        form_html = asked.split("<form", 1)[1].split("</form>", 1)[0]
        posted = {
            html.unescape(name): html.unescape(value)
            for name, value in re.findall(
                r'<input type="hidden" name="([^"]*)" value="([^"]*)">',
                form_html,
            )
        }
        try:
            urllib.request.urlopen(
                urllib.request.Request(
                    base + "/requirements/requirement/REQ-A",
                    data=urllib.parse.urlencode(posted).encode("utf-8"),
                    method="POST",
                )
            ).read()
        except urllib.error.HTTPError as exc:
            self.fail(exc.read().decode("utf-8"))
        self.assertEqual(_file_bytes(source), before)
        owned = next(
            path
            for path in (self.root / "imported-pack").iterdir()
            if path.is_dir() and b"Owned note." in (path / "REQ-A.json").read_bytes()
        )
        self.assertIn(b"ACME/Imported", (owned / "pack.json").read_bytes())

    def test_compare_apply_asks_before_changing_a_foreign_pack(self):
        import html
        import re
        import urllib.error
        import urllib.parse
        import urllib.request

        from common.canonical import version_digest
        from common.jsonio import write_json
        from common.store import load_requirement

        repo = self.root / "product"
        repo.mkdir()
        write_json(
            repo / "curbpack.json",
            self.created_curbpack(namespace_base="ACME", packs=["cra-xml-baseline"]),
        )
        self.save_repos(
            self.root,
            self.add_repo(self.root, self.load_repos(self.root), name="Product", path=str(repo)),
        )
        self.set_open_repo(self.root, "product")
        source = self.root / "source"
        save_pack(
            source,
            _pack(id="imported-pack", name="Imported", namespace="OTHER/Imported"),
        )
        save_requirement(
            source,
            _requirement("REQ-A", pack_id="imported-pack", namespace="OTHER/Imported"),
        )
        payload, _rows = export_pack_zip(source, {})
        installed, _rows = import_pack_zip(payload, self.root, {}, at="2026-11-12T140000Z")
        before = _file_bytes(installed)
        digest = version_digest(load_requirement(installed / "REQ-A.json"))
        base = self._serve()
        fields = {
            "source": installed.name,
            "destination": installed.name,
            "requirement_id": "REQ-A",
            "field": "note",
            "value": "Transferred note.",
            "source_digest": digest,
            "destination_digest": digest,
        }
        try:
            asked = urllib.request.urlopen(
                urllib.request.Request(
                    base + "/requirements/compare/apply",
                    data=urllib.parse.urlencode(fields).encode("utf-8"),
                    method="POST",
                )
            ).read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            self.fail(exc.read().decode("utf-8"))
        self.assertIn("Take ownership of this Pack?", asked)
        self.assertEqual(_file_bytes(installed), before)
        form_html = asked.split("<form", 1)[1].split("</form>", 1)[0]
        posted = {
            html.unescape(name): html.unescape(value)
            for name, value in re.findall(
                r'<input type="hidden" name="([^"]*)" value="([^"]*)">',
                form_html,
            )
        }
        try:
            urllib.request.urlopen(
                urllib.request.Request(
                    base + "/requirements/compare/apply",
                    data=urllib.parse.urlencode(posted).encode("utf-8"),
                    method="POST",
                )
            ).read()
        except urllib.error.HTTPError as exc:
            self.fail(exc.read().decode("utf-8"))
        self.assertEqual(_file_bytes(installed), before)
        owned = next(
            path
            for path in (self.root / "imported-pack").iterdir()
            if path.is_dir() and b"Transferred note." in (path / "REQ-A.json").read_bytes()
        )
        self.assertNotEqual(owned, installed)

    def test_compare_apply_without_a_repository_leaves_a_foreign_import(self):
        import urllib.error
        import urllib.parse
        import urllib.request

        from common.canonical import version_digest
        from common.store import load_requirement

        private, _public = generate_keypair()
        source = self.root / "source"
        save_pack(
            source,
            _pack(id="imported-pack", name="Imported", namespace="OTHER/Imported"),
        )
        save_requirement(
            source,
            sign_object(
                _requirement("REQ-A", pack_id="imported-pack", namespace="OTHER/Imported"),
                name="Ada",
                private_key=private,
                at="2026-11-12T12:00:00Z",
            ),
        )
        payload, _rows = export_pack_zip(source, {})
        installed, _rows = import_pack_zip(payload, self.root, {}, at="2026-11-12T140000Z")
        before = _file_bytes(installed)
        digest = version_digest(load_requirement(installed / "REQ-A.json"))
        base = self._serve()
        request = urllib.request.Request(
            base + "/requirements/compare/apply",
            data=urllib.parse.urlencode(
                {
                    "source": installed.name,
                    "destination": installed.name,
                    "requirement_id": "REQ-A",
                    "field": "note",
                    "value": "Transferred note.",
                    "source_digest": digest,
                    "destination_digest": digest,
                }
            ).encode("utf-8"),
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request)
        self.assertEqual(caught.exception.code, 400)
        self.assertIn("the open repository", caught.exception.read().decode("utf-8"))
        self.assertEqual(_file_bytes(installed), before)
        self.assertEqual(
            [path.name for path in (self.root / "imported-pack").iterdir() if path.is_dir()],
            [installed.name],
        )
