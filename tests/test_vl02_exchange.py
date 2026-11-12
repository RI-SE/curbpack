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
