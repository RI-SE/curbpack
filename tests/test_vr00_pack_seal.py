"""VR-00 pack seal. Existing directory seal, including unsigned Requirements."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from common.signing import complete_pack_digest, generate_keypair, sign_object, verify_signature
from common.store import load_pack, save_pack, save_requirement
from requirements.editing import read_pack_seal, seal_pack_directory


def _requirement(requirement_id: str = "REQ-A") -> dict:
    return {
        "id": requirement_id,
        "pack_id": "pack",
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
        save_pack(root, {"id": "pack", "version": "1"})
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

    def test_a_dotfile_is_part_of_the_same_seal(self):
        private, public = generate_keypair()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        save_pack(root, {"id": "pack", "version": "1"})
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
