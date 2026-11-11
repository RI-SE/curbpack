"""VR-00 signature result. Object signatures, then Git."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from common.canonical import pack_directory_digest, version_digest
from common.jsonio import write_json
from common.signing import complete_pack_digest, generate_keypair, signed_block, verify_object


class ObjectSignatureTest(unittest.TestCase):
    def test_valid_object_signature_reports_signer_and_digest(self):
        private, public = generate_keypair()
        payload = {"id": "REQ-1", "pack_id": "pack"}
        digest = version_digest(payload)
        block = signed_block(digest, name="Ada", private_key=private, at="2026-11-11T12:00:00Z")
        result = verify_object(digest, block, {"Ada": public})
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["method"], "object")
        self.assertEqual(result["signer"], "Ada")
        self.assertEqual(result["version"], digest)

    def test_bad_object_signature_stays_invalid(self):
        private, public = generate_keypair()
        payload = {"id": "REQ-1", "pack_id": "pack"}
        digest = version_digest(payload)
        block = signed_block(digest, name="Ada", private_key=private, at="2026-11-11T12:00:00Z")
        result = verify_object(digest + "ff", block, {"Ada": public})
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["method"], "object")
        self.assertIn("does not verify", result["reason"])

    def test_missing_certificate_is_invalid_without_fetching(self):
        private, _public = generate_keypair()
        payload = {"id": "REQ-1"}
        digest = version_digest(payload)
        block = signed_block(digest, name="Ada", private_key=private, at="2026-11-11T12:00:00Z")
        result = verify_object(digest, block, {})
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["method"], "object")
        self.assertIn("not available", result["reason"])
        self.assertIn("does not fetch", result["reason"])

    def test_dotfile_changes_the_pack_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root / "pack.json", {"id": "pack", "version": "1"})
            hidden = root / ".note"
            hidden.write_text("a", encoding="utf-8")
            before = complete_pack_digest(root)
            ignored = pack_directory_digest(root)
            hidden.write_text("b", encoding="utf-8")
            after = complete_pack_digest(root)
            self.assertNotEqual(before, after)
            self.assertEqual(ignored, pack_directory_digest(root))
