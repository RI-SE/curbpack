"""VL-00: namespace, origin, and status contracts."""

from __future__ import annotations

import unittest

from checks.defaults import created_curbpack
from common.errors import ModelError
from common.store import load_pack_directory, save_pack, save_requirement
from common.validate import (
    pack_identity,
    requirement_identity,
    validate_curbpack_config,
    validate_pack,
    validate_requirement,
)
from studio.pack.pages import _curbpack_dialog


def _config(**overrides) -> dict:
    document = {
        "packs": ["cra-baseline"],
        "search_hints": {"sources": [{"source": "documents"}]},
        "packs_dir": "curbpack/packs",
        "claims_dir": "curbpack/claims",
        "results_dir": ".curbpack",
        "reports_dir": "curbpack/reports",
        "namespace_base": "RISE",
    }
    document.update(overrides)
    return document


class NamespaceBaseTest(unittest.TestCase):
    def test_a_valid_config_exposes_namespace_base(self):
        document = validate_curbpack_config(_config())
        self.assertEqual(document["namespace_base"], "RISE")

    def test_namespace_base_is_required(self):
        document = _config()
        del document["namespace_base"]
        with self.assertRaises(ModelError) as caught:
            validate_curbpack_config(document)
        self.assertEqual(caught.exception.field, "namespace_base")

    def test_a_blank_namespace_base_is_rejected(self):
        with self.assertRaises(ModelError) as caught:
            validate_curbpack_config(_config(namespace_base="  "))
        self.assertEqual(caught.exception.field, "namespace_base")

    def test_created_file_uses_rise(self):
        self.assertEqual(created_curbpack()["namespace_base"], "RISE")

    def test_dialog_posts_namespace_base(self):
        page = _curbpack_dialog({"curbpack_fields": created_curbpack(), "repo_id": "alpha"})
        self.assertIn('name="namespace_base"', page)
        self.assertIn('value="RISE"', page)


def _pack(**overrides) -> dict:
    document = {
        "id": "cra-baseline",
        "name": "CRA",
        "version": "1.0.0",
        "namespace": "RISE/CRA",
        "status": "draft",
    }
    document.update(overrides)
    return document


def _requirement(**overrides) -> dict:
    document = {
        "id": "REQ-A",
        "pack_id": "cra-baseline",
        "namespace": "RISE/CRA",
        "status": "draft",
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


class PackContractTest(unittest.TestCase):
    def test_pack_identity_keeps_namespace_and_id(self):
        pack = validate_pack(_pack())
        self.assertEqual(pack_identity(pack), ("RISE/CRA", "cra-baseline"))
        self.assertEqual(pack["version"], "1.0.0")

    def test_same_pack_id_in_different_namespaces_stays_distinct(self):
        left = validate_pack(_pack())
        right = validate_pack(_pack(namespace="OTHER/CRA"))
        self.assertNotEqual(pack_identity(left), pack_identity(right))
        self.assertEqual(left["id"], right["id"])

    def test_missing_status_defaults_to_draft(self):
        document = _pack()
        del document["status"]
        self.assertEqual(validate_pack(document)["status"], "draft")

    def test_only_draft_and_reviewed_are_status_values(self):
        validate_pack(_pack(status="reviewed"))
        with self.assertRaises(ModelError) as caught:
            validate_pack(_pack(status="structural_draft"))
        self.assertEqual(caught.exception.field, "status")

    def test_assurance_class_is_rejected(self):
        with self.assertRaises(ModelError) as caught:
            validate_pack(_pack(assurance_class="structural_draft"))
        self.assertEqual(caught.exception.field, "assurance_class")

    def test_pack_origin_is_optional_and_kept(self):
        bare = validate_pack(_pack())
        self.assertNotIn("origin", bare)
        origin = {"namespace": "RISE/CRA", "pack": "cra-baseline", "version": "0.1.0"}
        kept = validate_pack(_pack(origin=origin))
        self.assertEqual(kept["origin"], origin)
        legacy = validate_pack(_pack(origin={"pack": "cra-baseline", "version": "0.1.0"}))
        self.assertEqual(legacy["origin"], {"pack": "cra-baseline", "version": "0.1.0"})


class RequirementContractTest(unittest.TestCase):
    def test_requirement_identity_includes_pack_id(self):
        left = validate_requirement(_requirement())
        right = validate_requirement(_requirement(pack_id="house-policy", namespace="RISE/House"))
        self.assertEqual(requirement_identity(left), ("RISE/CRA", "cra-baseline", "REQ-A"))
        self.assertNotEqual(requirement_identity(left), requirement_identity(right))

    def test_same_requirement_id_in_another_namespace_stays_distinct(self):
        left = validate_requirement(_requirement())
        right = validate_requirement(_requirement(namespace="OTHER/CRA"))
        self.assertEqual(left["id"], right["id"])
        self.assertNotEqual(requirement_identity(left), requirement_identity(right))

    def test_directory_namespace_must_match_the_pack(self):
        import tempfile
        from pathlib import Path

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        save_pack(root, _pack())
        save_requirement(root, _requirement(namespace="OTHER/CRA"))
        with self.assertRaises(ModelError) as caught:
            load_pack_directory(root)
        self.assertEqual(caught.exception.field, "namespace")

    def test_origin_stays_absent_until_supplied(self):
        requirement = validate_requirement(_requirement())
        self.assertNotIn("origin", requirement)
        origin = {
            "namespace": "RISE/CRA",
            "pack": "cra-baseline",
            "version": "1.0.0",
            "requirement": "REQ-A",
        }
        kept = validate_requirement(_requirement(origin=origin))
        self.assertEqual(kept["origin"], origin)

    def test_missing_requirement_status_defaults_to_draft(self):
        document = _requirement()
        del document["status"]
        self.assertEqual(validate_requirement(document)["status"], "draft")


class ReferencePackTest(unittest.TestCase):
    def test_reference_packs_use_rise_namespaces_and_draft_status(self):
        from pathlib import Path

        root = Path("docs/reference/test-packs")
        packs = sorted(root.glob("*/pack.json"))
        self.assertGreaterEqual(len(packs), 1)
        for path in packs:
            pack, requirements = load_pack_directory(path.parent)
            self.assertEqual(pack["namespace"], f"RISE/{pack['name']}")
            self.assertEqual(pack["status"], "draft")
            self.assertNotIn("assurance_class", pack)
            self.assertNotIn("origin", pack)
            for requirement in requirements:
                self.assertEqual(requirement["namespace"], pack["namespace"])
                self.assertEqual(requirement["status"], "draft")
                self.assertNotIn("origin", requirement)


class SignatureStatusTest(unittest.TestCase):
    def test_sealing_a_draft_pack_leaves_status_unchanged(self):
        import tempfile
        from pathlib import Path

        from common.signing import generate_keypair
        from requirements.editing import read_pack_seal, seal_pack_directory

        private, public = generate_keypair()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        save_pack(root, _pack())
        document = _requirement()
        del document["status"]
        save_requirement(root, document)
        seal_pack_directory(root, name="Ada", private_key=private, at="2026-11-12T12:00:00Z")
        pack, requirements = load_pack_directory(root)
        self.assertEqual(pack["status"], "draft")
        self.assertEqual(requirements[0]["status"], "draft")
        self.assertNotIn("signed", requirements[0])
        self.assertTrue(read_pack_seal(root, {"Ada": public})["verifiable"])

    def test_changing_signed_status_namespace_or_origin_breaks_verification(self):
        from common.signing import generate_keypair, read_signature, sign_object

        private, public = generate_keypair()
        signed = sign_object(
            validate_requirement(_requirement()),
            name="Ada",
            private_key=private,
            at="2026-11-12T12:00:00Z",
        )
        trust = {"Ada": public}
        self.assertTrue(read_signature(signed, trust, what="requirement")["verifiable"])
        for field, value in (
            ("status", "reviewed"),
            ("namespace", "OTHER/CRA"),
            ("origin", {"pack": "cra-baseline", "version": "1.0.0"}),
        ):
            changed = dict(signed)
            changed[field] = value
            self.assertFalse(read_signature(changed, trust, what="requirement")["verifiable"])


class ExtractNamespaceTest(unittest.TestCase):
    def test_extract_pack_uses_the_given_namespace_base(self):
        from studio.pack.extract_start import _namespace_base_at, _pack_for_adapter

        cra = _pack_for_adapter({"id": "cra", "pack_id": "cra-baseline"}, "ACME")
        self.assertEqual(cra["namespace"], "ACME/CRA baseline")
        other = _pack_for_adapter({"id": "nis", "pack_id": "nis-pack"}, "ACME")
        self.assertEqual(other["namespace"], "ACME/nis extract")
        self.assertEqual(other["status"], "draft")
        import tempfile
        from pathlib import Path

        self.assertEqual(_namespace_base_at(None), "RISE")
        from checks.defaults import created_curbpack
        from common.jsonio import write_json

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo = Path(tmp.name)
        write_json(repo / "curbpack.json", created_curbpack(namespace_base="ACME"))
        self.assertEqual(_namespace_base_at(repo), "ACME")
        self.assertEqual(_namespace_base_at(repo / "missing"), "RISE")
