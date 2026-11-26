"""FMT-01 load returns version 1 in memory. Save is the only write."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checks.defaults import created_curbpack
from claims.bind import build_claim
from common.canonical import version_digest
from common.errors import ModelError
from common.jsonio import read_json, write_json
from common.signing import generate_keypair
from common.store import (
    load_claim,
    read_claim,
    read_pack,
    read_requirement,
    read_run_result,
    save_claim,
    save_pack,
    save_requirement,
    save_run_result,
)
from common.validate import read_curbpack, save_curbpack
from studio.compile.impl.report import compile_report, read_review_report, write_report
from studio.review.impl.present import same_run
from studio.review.impl.items import (
    read_remedy_report,
    read_review_items,
    read_run_files,
    save_remedy_report,
    save_review_items,
    save_run_files,
    sign_remedy_document,
)


def _requirement() -> dict:
    return {
        "id": "REQ-A",
        "pack_id": "pack",
        "namespace": "RISE/pack",
        "status": "draft",
        "source": {
            "framework": "CRA",
            "instrument": "Annex",
            "identifier": "VII.3",
            "language": "en",
            "url": "https://example.invalid/cra",
        },
        "references": [{"nr": 1, "locator": "VII.3", "law_text": "Assess the risk."}],
    }


def _claim() -> dict:
    return build_claim(
        claim_id="claim-a",
        requirement=_requirement(),
        source="documents",
        args={"path": "docs/a.md"},
        checks=[{"check": "exist", "args": {"paths": ["docs/a.md"]}}],
        description="The file is the evidence.",
    )


def _run_result(claim: dict) -> dict:
    return {
        "tool": "curbcheck",
        "tool_version": "0.0.1a",
        "packs": [{"id": "pack", "version": "1", "digest": "abc"}],
        "claims": [
            {
                "id": claim["id"],
                "digest": version_digest(claim),
                "status": "pass",
                "checks": [
                    {
                        "index": 0,
                        "check": "exist",
                        "args": claim["checks"][0]["args"],
                        "status": "pass",
                    }
                ],
            }
        ],
    }


class FormatLoadTest(unittest.TestCase):
    def _round_trip(self, document: dict, filename: str, read, save) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / filename
        write_json(path, document)
        before = path.read_bytes()
        loaded, read_version, current_version = read(path)
        self.assertEqual(loaded["format_version"], 1)
        self.assertEqual(read_version, 0)
        self.assertEqual(current_version, 1)
        self.assertEqual(path.read_bytes(), before)
        save(path, loaded)
        stored = read_json(path)
        self.assertEqual(stored.pop("format_version"), 1)
        self.assertEqual(stored, document)

    def test_unversioned_pack_loads_as_version_1_until_save(self):
        document = {"id": "pack", "name": "pack", "version": "1", "namespace": "RISE/pack", "status": "draft"}
        self._round_trip(
            document,
            "pack.json",
            read_pack,
            lambda path, loaded: save_pack(path.parent, loaded),
        )

    def test_unversioned_requirement_loads_as_version_1_until_save(self):
        self._round_trip(
            _requirement(),
            "REQ-A.json",
            read_requirement,
            lambda path, loaded: save_requirement(path.parent, loaded),
        )

    def test_unversioned_claim_loads_as_version_1_until_save(self):
        self._round_trip(
            _claim(),
            "claim-a.json",
            read_claim,
            lambda path, loaded: save_claim(path.parent, loaded),
        )

    def test_unversioned_curbpack_loads_as_version_1_until_save(self):
        self._round_trip(created_curbpack(), "curbpack.json", read_curbpack, lambda path, loaded: save_curbpack(path, loaded))

    def test_unversioned_run_result_loads_as_version_1_until_save(self):
        self._round_trip(
            _run_result(_claim()),
            "run-result_20261126T080000Z.json",
            read_run_result,
            lambda path, loaded: save_run_result(path, loaded),
        )

    def test_unversioned_review_items_load_as_version_1_until_save(self):
        self._round_trip(
            {"items": [], "notes": "keep"},
            "review_items.json",
            read_review_items,
            lambda path, loaded: save_review_items(path, loaded),
        )

    def test_unversioned_review_report_loads_as_version_1_and_is_not_rewritten(self):
        from studio.compile.impl.report import compile_report

        claim = _claim()
        report = compile_report(
            run_result=_run_result(claim),
            requirements=[_requirement()],
            claims=[claim],
        )
        self._round_trip(report, "review-report_20261126T080000Z.json", read_review_report, lambda path, loaded: write_report(path, loaded))

    def test_unversioned_remedy_report_loads_as_version_1_and_is_not_rewritten(self):
        private, _public = generate_keypair()
        sealed = sign_remedy_document(
            [],
            name="Ada",
            private_key=private,
            at="2026-11-26T08:00:00Z",
            notes="done",
        )
        self._round_trip(
            sealed,
            "remedy-report_20261126T080000Z.json",
            read_remedy_report,
            lambda path, loaded: save_remedy_report(path, loaded),
        )

    def test_unversioned_run_files_sidecar_loads_as_version_1_until_save(self):
        self._round_trip(
            {"checks": []},
            "run-result_20261126T080000Z.files.json",
            read_run_files,
            lambda path, loaded: save_run_files(path, loaded),
        )

    def test_retired_claim_loads_as_the_current_shape_and_the_file_stays(self):
        legacy = {
            "id": "claim-old",
            "requirement_id": "REQ-A",
            "namespace": "RISE/pack",
            "pack_id": "pack",
            "requirement_digest": "recorded",
            "check": "exist",
            "args": {"paths": ["docs/a.md"]},
        }
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "claim-old.json"
        write_json(path, legacy)
        before = path.read_bytes()
        loaded = load_claim(path)
        reading, read_version, current_version = read_claim(path)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(loaded["checks"], [{"check": "exist", "args": {"paths": ["docs/a.md"]}}])
        self.assertNotIn("check", loaded)
        self.assertEqual(loaded["format_version"], 1)
        self.assertEqual(reading["format_version"], 1)
        self.assertEqual((read_version, current_version), (0, 1))
        self.assertIn("check", read_json(path))

    def test_a_version_1_file_reports_read_version_1(self):
        document = _requirement()
        document["format_version"] = 1
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "REQ-A.json"
        write_json(path, document)
        before = path.read_bytes()
        loaded, read_version, current_version = read_requirement(path)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(loaded["format_version"], 1)
        self.assertEqual((read_version, current_version), (1, 1))

    def test_retired_claim_with_format_version_2_is_rejected_and_the_file_stays(self):
        legacy = {
            "id": "claim-old",
            "requirement_id": "REQ-A",
            "namespace": "RISE/pack",
            "pack_id": "pack",
            "requirement_digest": "recorded",
            "check": "exist",
            "args": {"paths": ["docs/a.md"]},
            "format_version": 2,
        }
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "claim-old.json"
        write_json(path, legacy)
        before = path.read_bytes()
        with self.assertRaises(ModelError) as caught:
            read_claim(path)
        self.assertEqual(caught.exception.field, "format_version")
        self.assertEqual(caught.exception.expected, "1, or absent")
        self.assertEqual(path.read_bytes(), before)

    def test_retired_claim_at_version_1_reports_that_read_version(self):
        legacy = {
            "id": "claim-old",
            "requirement_id": "REQ-A",
            "namespace": "RISE/pack",
            "pack_id": "pack",
            "requirement_digest": "recorded",
            "check": "exist",
            "args": {"paths": ["docs/a.md"]},
            "format_version": 1,
        }
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "claim-old.json"
        write_json(path, legacy)
        before = path.read_bytes()
        loaded, read_version, current_version = read_claim(path)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(loaded["format_version"], 1)
        self.assertEqual((read_version, current_version), (1, 1))
        self.assertIn("check", read_json(path))
        self.assertNotIn("check", loaded)

    def test_an_older_review_matches_its_run_and_compile_leaves_nested_copies_unstamped(self):
        claim = _claim()
        requirement = _requirement()
        run = _run_result(claim)
        report = compile_report(run_result=run, requirements=[requirement], claims=[claim])
        self.assertNotIn("format_version", report["run_result"])
        self.assertNotIn("format_version", report["claims"][0])
        self.assertNotIn("format_version", report["requirements"][0])
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        write_json(root / "run-result.json", run)
        write_json(root / "review-report.json", report)
        loaded_run, read_version, _current = read_run_result(root / "run-result.json")
        loaded_report, report_read_version, _report_current = read_review_report(root / "review-report.json")
        self.assertEqual(read_version, 0)
        self.assertEqual(report_read_version, 0)
        self.assertEqual(loaded_run["format_version"], 1)
        self.assertNotIn("format_version", loaded_report["run_result"])
        self.assertTrue(same_run(loaded_report, loaded_run))
        versioned_run = dict(run)
        versioned_run["format_version"] = 1
        versioned_claim = dict(claim)
        versioned_claim["format_version"] = 1
        versioned_requirement = dict(requirement)
        versioned_requirement["format_version"] = 1
        compiled = compile_report(
            run_result=versioned_run,
            requirements=[versioned_requirement],
            claims=[versioned_claim],
        )
        self.assertNotIn("format_version", compiled["run_result"])
        self.assertNotIn("format_version", compiled["claims"][0])
        self.assertNotIn("format_version", compiled["requirements"][0])
        self.assertEqual(version_digest(compiled), version_digest(report))
        self.assertTrue(same_run(compiled, loaded_run))
