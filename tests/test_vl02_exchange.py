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
from studio.pack.pack_exchange import export_pack_zip


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
