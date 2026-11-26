"""VR-00 pack seal. Existing directory seal, including unsigned Requirements."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from common.canonical import pack_directory_digest
from common.errors import ModelError
from common.jsonio import dump_text, write_json
from common.signing import complete_pack_digest, generate_keypair, sign_object, verify_signature
from common.store import load_pack, load_requirement, save_pack, save_requirement
from requirements.editing import read_pack_seal, seal_pack_directory


def _requirement(requirement_id: str = "REQ-A") -> dict:
    return {
        "id": requirement_id,
        "pack_id": "pack",
        "namespace": "RISE/pack",
        "source": {
            "framework": "CRA",
            "instrument": "Annex",
            "identifier": "VII.3",
            "language": "en",
            "url": "https://example.invalid/cra",
        },
        "references": [{"nr": 1, "locator": "VII.3", "law_text": "Assess the risk."}],
    }


class PackSealTest(unittest.TestCase):
    def _sealed_copy(self) -> tuple[Path, dict[str, bytes]]:
        private, public = generate_keypair()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        save_pack(root, {"id": "pack", "name": "pack", "version": "1", "namespace": "RISE/pack"})
        save_requirement(root, _requirement())
        save_requirement(root, _requirement("REQ-B"))
        seal_pack_directory(root, name="Ada", private_key=private, at="2026-11-11T12:00:00Z")
        self.assertNotIn("signed", (root / "REQ-A.json").read_text(encoding="utf-8"))
        return root, {"Ada": public}

    def test_pack_seal_allows_unsigned_requirements(self):
        root, trust = self._sealed_copy()
        reading = read_pack_seal(root, trust)
        self.assertTrue(reading["verifiable"])

    def test_editing_a_requirement_breaks_the_pack_seal(self):
        root, trust = self._sealed_copy()
        path = root / "REQ-A.json"
        path.write_text(path.read_text(encoding="utf-8").replace("Assess", "Ignore"), encoding="utf-8")
        self.assertFalse(read_pack_seal(root, trust)["verifiable"])

    def test_adding_a_requirement_signature_breaks_the_pack_seal(self):
        root, trust = self._sealed_copy()
        private, _public = generate_keypair()
        requirement = _requirement()
        signed = sign_object(requirement, name="Ada", private_key=private, at="2026-11-11T13:00:00Z")
        save_requirement(root, signed)
        self.assertFalse(read_pack_seal(root, trust)["verifiable"])

    def test_adding_format_version_keeps_the_pack_seal(self):
        root, trust = self._sealed_copy()
        pack = load_pack(root / "pack.json", sealed=True)
        pack_before = {key: value for key, value in pack.items()}
        pack["format_version"] = 1
        save_pack(root, pack, sealed=True)
        for name in ("REQ-A.json", "REQ-B.json"):
            requirement = load_requirement(root / name)
            before = {key: value for key, value in requirement.items()}
            requirement["format_version"] = 1
            save_requirement(root, requirement)
            saved = load_requirement(root / name)
            self.assertEqual(saved.pop("format_version"), 1)
            self.assertEqual(saved, before)
        saved_pack = load_pack(root / "pack.json", sealed=True)
        self.assertEqual(saved_pack.pop("format_version"), 1)
        self.assertEqual(saved_pack, pack_before)
        self.assertTrue(read_pack_seal(root, trust)["verifiable"])

    def test_crlf_requirement_keeps_the_same_pack_directory_digest(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        save_pack(root, {"id": "pack", "name": "pack", "version": "1", "namespace": "RISE/pack"})
        save_requirement(root, _requirement())
        path = root / "REQ-A.json"
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        before = pack_directory_digest(root)
        document = load_requirement(path)
        document["format_version"] = 1
        path.write_bytes(dump_text(document).replace("\n", "\r\n").encode("utf-8"))
        self.assertIn(b"\r\n", path.read_bytes())
        self.assertEqual(pack_directory_digest(root), before)

    def test_format_version_2_is_rejected_and_the_file_is_unchanged(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "REQ-A.json"
        requirement = _requirement()
        requirement["format_version"] = 2
        write_json(path, requirement)
        before = path.read_bytes()
        with self.assertRaises(ModelError) as caught:
            load_requirement(path)
        self.assertEqual(caught.exception.field, "format_version")
        self.assertEqual(caught.exception.expected, "1, or absent")
        self.assertEqual(path.read_bytes(), before)

    def test_a_dotfile_is_part_of_the_same_seal(self):
        private, public = generate_keypair()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        save_pack(root, {"id": "pack", "name": "pack", "version": "1", "namespace": "RISE/pack"})
        save_requirement(root, _requirement())
        (root / ".note").write_text("hidden", encoding="utf-8")
        seal_pack_directory(root, name="Ada", private_key=private, at="2026-11-11T12:00:00Z")
        trust = {"Ada": public}
        pack = load_pack(root / "pack.json")
        result = verify_signature(complete_pack_digest(root), pack.get("signed"), trust)
        self.assertTrue(read_pack_seal(root, trust)["verifiable"])
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["method"], "object")
        (root / ".note").write_text("changed", encoding="utf-8")
        changed = verify_signature(complete_pack_digest(root), pack.get("signed"), trust)
        self.assertFalse(read_pack_seal(root, trust)["verifiable"])
        self.assertEqual(changed["status"], "invalid")
        self.assertEqual(changed["method"], "object")
