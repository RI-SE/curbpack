"""VL-02: a Pack ZIP keeps the directory bytes and reports signatures."""

from __future__ import annotations

import io
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
