"""VL-01: taking ownership copies a foreign Pack and leaves the original."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

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
        with self.assertRaises(Exception):
            take_ownership(
                self.source,
                self.destination,
                namespace_base="ACME",
                requirement_id="REQ-A",
                edits={"note": "Owned note."},
                at="2026-11-12T130000Z",
            )
        self.assertEqual(_file_bytes(self.source), self.before)
        self.assertEqual(_file_bytes(existing), before_existing)
        self.assertFalse((self.destination / "cra-baseline" / "2026-11-12T130000Z").exists())

    def test_a_failed_edit_leaves_no_partial_copy(self):
        with self.assertRaises(Exception):
            take_ownership(
                self.source,
                self.destination,
                namespace_base="ACME",
                requirement_id="REQ-A",
                edits={"not-a-field": "x"},
                at="2026-11-12T130000Z",
            )
        self.assertEqual(_file_bytes(self.source), self.before)
        self.assertFalse((self.destination / "cra-baseline").exists())
