"""Working-copy edits keep a signature only when the payload is unchanged."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from common.canonical import version_digest
from common.errors import ModelError
from common.signing import generate_keypair, sign_object
from claims.bind import build_claim
from common.store import load_pack_directory, load_requirement, save_pack, save_requirement
from requirements.consolidate import apply_consolidation
from requirements.editing import (
    apply_edits,
    approve_working_copy,
    assign_reference_numbers,
    publish_requirement,
    save_working_requirement,
    seal_pack_directory,
    working_copy,
)
from requirements.extract.adapter import ADAPTERS, load_adapter
from requirements.extract.pipeline import draft_pack, extract_annex_vii_risk
from requirements.workspace import (
    create_extraction_copy,
    extract_section,
    list_publication_blockers,
    load_working_copy,
)


def _with_edition(requirement: dict) -> dict:
    source = dict(requirement["source"])
    source["edition"] = "2024-11-20"
    return apply_edits(
        requirement,
        {
            "source": source,
            "remediation_hint": "The file should be the product's own assessment, not a placeholder.",
        },
    )


class WorkingEditTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_same_value_edit_keeps_signed_and_stale_save_does_not_write(self):
        private, _public = generate_keypair()
        requirement = publish_requirement(
            _with_edition(extract_annex_vii_risk()),
            name="Ada Jurist",
            private_key=private,
            at="2026-10-12T09:00:00Z",
        )
        again = apply_edits(requirement, {"remediation_hint": requirement["remediation_hint"]})
        self.assertEqual(again["signed"], requirement["signed"])
        changed = apply_edits(requirement, {"remediation_hint": "A different hint."})
        self.assertNotIn("signed", changed)
        self.assertEqual(changed["discovery_hints"], requirement["discovery_hints"])
        root = Path(self.tmp.name)
        save_pack(root, draft_pack())
        save_requirement(root, requirement, published=True)
        digest = version_digest(requirement)
        save_working_requirement(root, changed, expected_digest=digest)
        with self.assertRaises(ModelError):
            save_working_requirement(root, requirement, expected_digest=digest)
        self.assertEqual(
            load_requirement(root / "CRA-ANNEX-VII-RISK.json")["remediation_hint"],
            "A different hint.",
        )

    def test_reference_numbers_reload_and_omitted_hints_keep_args(self):
        requirement = extract_annex_vii_risk()
        requirement["discovery_hints"]["sources"][0]["args"] = {"path": "docs"}
        references = assign_reference_numbers(
            [
                {
                    "locator": requirement["references"][0]["locator"],
                    "law_text": requirement["references"][0]["law_text"],
                },
                {"locator": "VII.1(a)", "law_text": "a statement of the intended purpose"},
            ]
        )
        edited = apply_edits(requirement, {"references": references})
        self.assertEqual([item["nr"] for item in edited["references"]], [1, 2])
        self.assertEqual(edited["discovery_hints"]["sources"][0]["args"], {"path": "docs"})
        root = Path(self.tmp.name)
        save_pack(root, draft_pack())
        save_working_requirement(root, edited, expected_digest=version_digest(requirement))
        loaded = load_requirement(root / "CRA-ANNEX-VII-RISK.json")
        self.assertEqual([item["nr"] for item in loaded["references"]], [1, 2])
        self.assertEqual(loaded["discovery_hints"]["sources"][0]["args"], {"path": "docs"})


def _sample_proposals() -> list[dict]:
    return [
        {
            "locus": "3",
            "id": "CRA-ANNEX-VII-RISK",
            "locator": "VII.3",
            "discovery_hints": {
                "concepts": ["risk assessment"],
                "path_hints": ["*risk*assessment*", "*THREAT*"],
                "sources": [{"source": "documents"}],
            },
        },
        # Pipeline fixture only. Not a CRA id convention.
        {"locus": "1(a)", "id": "FIXTURE-VII-1A", "locator": "VII.1(a)"},
    ]


def _snapshot(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


class PublishPackTest(unittest.TestCase):
    def setUp(self):
        from requirements.workspace import publish_pack

        self.publish_pack = publish_pack
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.private, public = generate_keypair()
        self.trust = {"Ada Jurist": public}
        self.cra = load_adapter(ADAPTERS / "cra" / "adapter.json")

    def _extracted(self):
        return extract_section(
            self.root,
            ADAPTERS / "cra",
            self.cra,
            "VII",
            _sample_proposals(),
            draft_pack(),
            at="2026-10-13T090000Z",
        )

    def _seal(self, copy: Path, requirements: list[dict], *, unsigned_ids: set[str] | None = None) -> None:
        unsigned_ids = unsigned_ids or set()
        for requirement in requirements:
            edited = _with_edition(requirement)
            if requirement["id"] in unsigned_ids:
                save_requirement(copy, edited, published=False)
            else:
                signed = publish_requirement(
                    edited,
                    name="Ada Jurist",
                    private_key=self.private,
                    at="2026-10-12T09:00:00Z",
                )
                save_requirement(copy, signed, published=True)
        seal_pack_directory(copy, name="Ada Jurist", private_key=self.private, at="2026-10-12T10:00:00Z")

    def test_publish_copies_two_signed_requirements_and_refuses_a_repeat(self):
        result = self._extracted()
        coverage = json.loads((result["work"] / "coverage.json").read_text(encoding="utf-8"))
        self.assertEqual(coverage["status"], "incomplete")
        self.assertTrue(any(row["status"] == "excluded" for row in coverage["loci"]))
        _pack, requirements = load_working_copy(result["copy"])
        self._seal(result["copy"], requirements)
        before = _snapshot(result["copy"])
        work_before = _snapshot(result["work"])
        destination = self.publish_pack(self.root, result["copy"], version="0.1.0", trust=self.trust)
        self.assertEqual(
            sorted(path.name for path in destination.iterdir()),
            ["CRA-ANNEX-VII-RISK.json", "FIXTURE-VII-1A.json", "pack.json"],
        )
        self.assertFalse((destination / "coverage.json").exists())
        released_pack, released = load_pack_directory(destination)
        self.assertEqual(released_pack["version"], "0.1.0")
        self.assertEqual({item["id"] for item in released}, {"CRA-ANNEX-VII-RISK", "FIXTURE-VII-1A"})
        for item in released:
            self.assertIn("signed", item)
            self.assertNotIn("origin", item)
            self.assertEqual(item["source"]["edition"], "2024-11-20")
        self.assertEqual(_snapshot(result["copy"]), before)
        self.assertEqual(_snapshot(result["work"]), work_before)
        released_bytes = _snapshot(destination)
        with self.assertRaises(ModelError):
            self.publish_pack(self.root, result["copy"], version="0.1.0", trust=self.trust)
        self.assertEqual(_snapshot(destination), released_bytes)
        self.assertEqual(_snapshot(result["copy"]), before)

    def test_publication_blockers_ignore_incomplete_coverage(self):
        result = self._extracted()
        blockers = list_publication_blockers(self.root, result["copy"], self.trust)
        self.assertTrue(blockers)
        self.assertFalse(any("coverage" in item.lower() or "incomplete" in item.lower() for item in blockers))
        self.assertTrue(any("unsigned" in item for item in blockers))
        _pack, requirements = load_working_copy(result["copy"])
        self._seal(result["copy"], requirements)
        self.assertEqual(list_publication_blockers(self.root, result["copy"], self.trust), [])

    def test_incomplete_coverage_status_does_not_block_publication(self):
        result = self._extracted()
        _pack, requirements = load_working_copy(result["copy"])
        self._seal(result["copy"], requirements)
        coverage_path = result["work"] / "coverage.json"
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
        coverage["status"] = "failed"
        coverage_path.write_text(json.dumps(coverage), encoding="utf-8")
        destination = self.publish_pack(self.root, result["copy"], version="0.1.0", trust=self.trust)
        self.assertTrue(destination.is_dir())
        self.assertEqual(json.loads(coverage_path.read_text(encoding="utf-8"))["status"], "failed")
        self.assertFalse((destination / "coverage.json").exists())

    def test_published_release_refuses_edits_and_loads_for_claims(self):
        result = self._extracted()
        _pack, requirements = load_working_copy(result["copy"])
        self._seal(result["copy"], requirements)
        destination = self.publish_pack(self.root, result["copy"], version="0.1.0", trust=self.trust)
        before = _snapshot(destination)
        released_pack, released = load_pack_directory(destination)
        point3 = next(item for item in released if item["id"] == "CRA-ANNEX-VII-RISK")
        changed = apply_edits(point3, {"remediation_hint": "must not write into the release"})
        with self.assertRaises(ModelError) as caught:
            save_working_requirement(
                destination, changed, expected_digest=version_digest(point3)
            )
        self.assertEqual(caught.exception.field, "path")
        with self.assertRaises(ModelError):
            apply_consolidation(
                destination,
                ["CRA-ANNEX-VII-RISK", "FIXTURE-VII-1A"],
                "CRA-ANNEX-VII-RISK",
                {},
                [
                    {
                        "locator": point3["references"][0]["locator"],
                        "law_text": point3["references"][0]["law_text"],
                    }
                ],
                digests={item["id"]: version_digest(item) for item in released},
            )
        self.assertEqual(_snapshot(destination), before)
        claim = build_claim(
            claim_id="risk-assessment-exists",
            requirement_id=point3["id"],
            source="documents",
            args={"path": "docs/annex-vii/risk_assessment.md"},
            checks=[{"check": "exist", "args": {"paths": ["docs/annex-vii/risk_assessment.md"]}}],
            description="The risk assessment file is the reviewed evidence.",
        )
        self.assertEqual(claim["requirement_id"], "CRA-ANNEX-VII-RISK")
        self.assertEqual(released_pack["id"], "cra-baseline")
        self.assertEqual(_snapshot(destination), before)

    def test_unsigned_requirement_is_refused_and_leaves_no_release(self):
        result = self._extracted()
        _pack, requirements = load_working_copy(result["copy"])
        self._seal(result["copy"], requirements, unsigned_ids={"FIXTURE-VII-1A"})
        before = _snapshot(result["copy"])
        with self.assertRaises(ModelError) as caught:
            self.publish_pack(self.root, result["copy"], version="0.1.0", trust=self.trust)
        self.assertEqual(caught.exception.field, "signed")
        self.assertIn("seal", caught.exception.expected)
        self.assertNotIn("verifies", caught.exception.expected)
        self.assertFalse((self.root / "published").exists())
        self.assertEqual(list(self.root.glob(".publish-tmp-*")), [])
        self.assertEqual(_snapshot(result["copy"]), before)

    def test_tampered_signature_is_refused(self):
        result = self._extracted()
        _pack, requirements = load_working_copy(result["copy"])
        self._seal(result["copy"], requirements)
        path = result["copy"] / "FIXTURE-VII-1A.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["signed"]["signature"] = "A" * 88
        path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(ModelError) as caught:
            self.publish_pack(self.root, result["copy"], version="0.1.0", trust=self.trust)
        self.assertEqual(caught.exception.field, "signed")
        self.assertIn("verifies", caught.exception.expected)
        self.assertFalse((self.root / "published").exists())
        self.assertEqual(list(self.root.glob(".publish-tmp-*")), [])

    def test_missing_edition_and_publisher_origin_are_refused(self):
        result = self._extracted()
        _pack, requirements = load_working_copy(result["copy"])
        for requirement in requirements:
            signed = sign_object(
                requirement,
                name="Ada Jurist",
                private_key=self.private,
                at="2026-10-12T09:00:00Z",
            )
            save_requirement(result["copy"], signed, published=False)
        seal_pack_directory(result["copy"], name="Ada Jurist", private_key=self.private, at="2026-10-12T10:00:00Z")
        with self.assertRaises(ModelError) as caught:
            self.publish_pack(self.root, result["copy"], version="0.1.0", trust=self.trust)
        self.assertEqual(caught.exception.field, "edition")
        self.assertFalse((self.root / "published").exists())

        origin = self._extracted_at("2026-10-13T143000Z")
        _pack, requirements = load_working_copy(origin["copy"])
        by_id = {item["id"]: item for item in requirements}
        published = publish_requirement(
            _with_edition(by_id["CRA-ANNEX-VII-RISK"]),
            name="Ada Jurist",
            private_key=self.private,
            at="2026-10-12T09:00:00Z",
        )
        save_requirement(origin["copy"], published, published=True)
        approved = approve_working_copy(
            working_copy(_with_edition(by_id["FIXTURE-VII-1A"]), draft_pack()),
            name="Ada Jurist",
            private_key=self.private,
            at="2026-10-15T09:00:00Z",
        )
        save_requirement(origin["copy"], approved, published=False)
        seal_pack_directory(origin["copy"], name="Ada Jurist", private_key=self.private, at="2026-10-12T10:00:00Z")
        before = _snapshot(origin["copy"])
        with self.assertRaises(ModelError) as caught:
            self.publish_pack(self.root, origin["copy"], version="0.1.0", trust=self.trust)
        self.assertEqual(caught.exception.field, "origin")
        self.assertEqual(_snapshot(origin["copy"]), before)
        self.assertFalse((self.root / "published").exists())

    def test_zero_requirements_and_a_different_version_are_refused(self):
        empty = create_extraction_copy(self.root, "cra-baseline", draft_pack(), at="2026-10-13T090000Z")
        seal_pack_directory(empty, name="Ada Jurist", private_key=self.private, at="2026-10-12T10:00:00Z")
        with self.assertRaises(ModelError) as caught:
            self.publish_pack(self.root, empty, version="0.1.0", trust=self.trust)
        self.assertEqual(caught.exception.field, "requirements")
        self.assertFalse((self.root / "published").exists())

        result = self._extracted_at("2026-10-13T143000Z")
        _pack, requirements = load_working_copy(result["copy"])
        self._seal(result["copy"], requirements)
        before = _snapshot(result["copy"])
        with self.assertRaises(ModelError) as caught:
            self.publish_pack(self.root, result["copy"], version="9.9.9", trust=self.trust)
        self.assertEqual(caught.exception.field, "version")
        self.assertEqual(_snapshot(result["copy"]), before)
        self.assertFalse((self.root / "published").exists())

    def test_broken_directory_seal_is_refused(self):
        result = self._extracted()
        _pack, requirements = load_working_copy(result["copy"])
        self._seal(result["copy"], requirements)
        pack_path = result["copy"] / "pack.json"
        document = json.loads(pack_path.read_text(encoding="utf-8"))
        document["signed"]["signature"] = "B" * 88
        pack_path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(ModelError) as caught:
            self.publish_pack(self.root, result["copy"], version="0.1.0", trust=self.trust)
        self.assertEqual(caught.exception.object_name, "pack")
        self.assertIn("directory seal", caught.exception.expected)
        self.assertFalse((self.root / "published").exists())

    def _extracted_at(self, at: str):
        return extract_section(
            self.root,
            ADAPTERS / "cra",
            self.cra,
            "VII",
            _sample_proposals(),
            draft_pack(),
            at=at,
        )
