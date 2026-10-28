"""PE-11: export the selected working copy as a Packs v2 directory.

REQ-PE-013 and REQ-PE-014 apply: provenance stays in the copied bytes, and
export adds no Pack field.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from checks.run import run_repository
from common.canonical import pack_directory_digest
from common.errors import ModelError
from common.store import load_pack_directory
from requirements.extract.adapter import ADAPTERS, load_adapter
from requirements.extract.pipeline import draft_pack
from requirements.workspace import extract_section
from tests.test_requirements_publish import _sample_proposals


class ExportPackTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cra = load_adapter(ADAPTERS / "cra" / "adapter.json")

    def test_two_requirements_export_outside_the_workspace_and_can_be_loaded(self):
        """PE11-R03, PE11-R04, PE11-R08, PE11-R11, PE11-R12, PE11-R14."""
        from requirements import workspace

        result = extract_section(
            self.root,
            ADAPTERS / "cra",
            self.cra,
            "VII",
            _sample_proposals(),
            draft_pack(),
            at="2026-10-13T090000Z",
        )
        copy = result["copy"]
        source_before = _file_bytes(copy)
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        outside_root = Path(outside.name)
        product = outside_root / "product-repo"
        product.mkdir()
        (product / "claims").mkdir()
        config = product / "curbpack.json"
        config.write_text('{"packs":["cra-baseline"]}\n', encoding="utf-8")
        config_before = config.read_bytes()
        destination = outside_root / "export-root"
        destination.mkdir()

        exported = workspace.export_pack(copy, destination)

        pack_dir = destination / "cra-baseline"
        self.assertEqual(exported, pack_dir.resolve())
        self.assertEqual([path.name for path in destination.iterdir()], ["cra-baseline"])
        self.assertEqual(
            sorted(path.name for path in pack_dir.iterdir()),
            ["CRA-ANNEX-VII-RISK.json", "FIXTURE-VII-1A.json", "pack.json"],
        )
        self.assertFalse((pack_dir / "requirements").exists())
        for name, source_bytes in source_before.items():
            if not name.endswith(".json") or "/" in name:
                continue
            self.assertEqual((pack_dir / name).read_bytes(), source_bytes)
        loaded_pack, loaded = load_pack_directory(pack_dir)
        self.assertEqual(loaded_pack["id"], "cra-baseline")
        self.assertEqual(loaded_pack["version"], "0.1.0")
        self.assertEqual(
            [item["id"] for item in loaded],
            ["CRA-ANNEX-VII-RISK", "FIXTURE-VII-1A"],
        )
        run_result, code = run_repository(product, destination)
        self.assertEqual(code, 1)
        self.assertEqual(run_result["packs"][0]["id"], "cra-baseline")
        self.assertEqual(run_result["packs"][0]["version"], "0.1.0")
        self.assertEqual(run_result["packs"][0]["digest"], pack_directory_digest(pack_dir))
        self.assertEqual(_file_bytes(copy), source_before)
        self.assertEqual(copy.name, "2026-10-13T090000Z")
        self.assertFalse((self.root / "published").exists())
        self.assertEqual(config.read_bytes(), config_before)
        exported_before_edit = _file_bytes(pack_dir)
        risk = copy / "CRA-ANNEX-VII-RISK.json"
        risk.write_bytes(risk.read_bytes() + b"\n")
        self.assertEqual(_file_bytes(pack_dir), exported_before_edit)


class ExportRefusalTest(unittest.TestCase):
    """PE11-R03, PE11-R05, PE11-R06, PE11-R09, PE11-R10, PE11-R11."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cra = load_adapter(ADAPTERS / "cra" / "adapter.json")
        self.copy = extract_section(
            self.root,
            ADAPTERS / "cra",
            self.cra,
            "VII",
            _sample_proposals(),
            draft_pack(),
            at="2026-10-13T090000Z",
        )["copy"]
        self.source_before = _file_bytes(self.copy)
        self.destination = self.root / "outside"
        self.destination.mkdir()

    def test_malformed_pack_json_leaves_no_export(self):
        (self.copy / "pack.json").write_text("{", encoding="utf-8")
        source = _file_bytes(self.copy)
        with self.assertRaises(ModelError):
            _export(self.copy, self.destination)
        self._no_pack(source)

    def test_missing_pack_id_leaves_no_export(self):
        (self.copy / "pack.json").write_text('{"version":"0.1.0"}\n', encoding="utf-8")
        source = _file_bytes(self.copy)
        with self.assertRaises(ModelError):
            _export(self.copy, self.destination)
        self._no_pack(source)

    def test_pack_id_that_is_not_one_directory_name_writes_nothing(self):
        document = json.loads((self.copy / "pack.json").read_text(encoding="utf-8"))
        document["id"] = "a/b"
        (self.copy / "pack.json").write_text(json.dumps(document), encoding="utf-8")
        source = _file_bytes(self.copy)
        with self.assertRaises(ModelError):
            _export(self.copy, self.destination)
        self._no_pack(source)

    def test_invalid_requirement_leaves_no_export(self):
        (self.copy / "BROKEN.json").write_text('{"id":"BROKEN"}\n', encoding="utf-8")
        source = _file_bytes(self.copy)
        with self.assertRaises(ModelError):
            _export(self.copy, self.destination)
        self._no_pack(source)

    def test_wrong_pack_id_leaves_no_export(self):
        path = self.copy / "FIXTURE-VII-1A.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["pack_id"] = "other-pack"
        path.write_text(json.dumps(document), encoding="utf-8")
        source = _file_bytes(self.copy)
        with self.assertRaises(ModelError):
            _export(self.copy, self.destination)
        self._no_pack(source)

    def test_empty_copy_leaves_no_export(self):
        for path in self.copy.glob("*.json"):
            if path.name != "pack.json":
                path.unlink()
        source = _file_bytes(self.copy)
        with self.assertRaises(ModelError):
            _export(self.copy, self.destination)
        self._no_pack(source)

    def test_missing_destination_writes_nothing(self):
        missing = self.root / "missing"
        with self.assertRaises(ModelError):
            _export(self.copy, missing)
        self.assertFalse(missing.exists())
        self.assertEqual(_file_bytes(self.copy), self.source_before)

    def test_destination_file_writes_nothing(self):
        target = self.root / "not-a-directory"
        target.write_text("file", encoding="utf-8")
        before = target.read_bytes()
        with self.assertRaises(ModelError):
            _export(self.copy, target)
        self.assertEqual(target.read_bytes(), before)
        self.assertEqual(_file_bytes(self.copy), self.source_before)

    def test_unwritable_destination_creates_no_pack_directory(self):
        def refuse(self_path, *args, **kwargs):
            raise PermissionError("not writable")

        with patch("pathlib.Path.mkdir", refuse):
            with self.assertRaises(PermissionError):
                _export(self.copy, self.destination)
        self.assertFalse((self.destination / "cra-baseline").exists())
        self.assertEqual(_file_bytes(self.copy), self.source_before)

    def test_empty_existing_directory_is_left_empty(self):
        final = self.destination / "cra-baseline"
        final.mkdir()
        with self.assertRaises(ModelError) as caught:
            _export(self.copy, self.destination)
        self.assertIn(str(final.resolve()), str(caught.exception))
        self.assertEqual(list(final.iterdir()), [])
        self._no_temp(self.source_before)

    def test_existing_sentinel_is_unchanged_without_overwrite(self):
        final = self.destination / "cra-baseline"
        final.mkdir()
        sentinel = final / "keep.txt"
        sentinel.write_bytes(b"keep")
        with self.assertRaises(ModelError) as caught:
            _export(self.copy, self.destination)
        self.assertIn(str(final.resolve()), str(caught.exception))
        self.assertEqual(sentinel.read_bytes(), b"keep")
        self._no_temp(self.source_before)

    def test_overwrite_replaces_the_pack_directory_and_keeps_a_sibling(self):
        final = self.destination / "cra-baseline"
        final.mkdir()
        (final / "keep.txt").write_bytes(b"keep")
        sibling = self.destination / "other-pack"
        sibling.mkdir()
        (sibling / "stay.txt").write_bytes(b"stay")
        _export(self.copy, self.destination, overwrite=True)
        self.assertFalse((final / "keep.txt").exists())
        self.assertEqual((final / "pack.json").read_bytes(), (self.copy / "pack.json").read_bytes())
        self.assertEqual((sibling / "stay.txt").read_bytes(), b"stay")
        self.assertEqual(_file_bytes(self.copy), self.source_before)
        self.assertFalse(any(path.name.startswith(".export-tmp-") for path in self.destination.iterdir()))

    def test_failed_overwrite_placement_restores_the_previous_directory(self):
        from requirements import workspace

        final = self.destination / "cra-baseline"
        final.mkdir()
        sentinel = final / "keep.txt"
        sentinel.write_bytes(b"keep")
        real = workspace.os.rename
        calls = {"n": 0}

        def second_fails(src, dst):
            calls["n"] += 1
            if calls["n"] == 2:
                raise OSError("second rename")
            return real(src, dst)

        with patch.object(workspace.os, "rename", side_effect=second_fails):
            with self.assertRaises(OSError):
                workspace.export_pack(self.copy, self.destination, overwrite=True)
        self.assertEqual(sentinel.read_bytes(), b"keep")
        self.assertFalse(any(path.name.startswith(".export-tmp-") for path in self.destination.iterdir()))
        self.assertFalse(any(path.name.startswith(".cra-baseline-replaced-") for path in self.destination.iterdir()))
        self.assertEqual(_file_bytes(self.copy), self.source_before)

    def test_diagnostics_and_product_files_are_not_exported(self):
        (self.copy / "notes.txt").write_text("not a pack file", encoding="utf-8")
        (self.root / "keys").mkdir()
        (self.root / "keys" / "secret.pem").write_text("secret", encoding="utf-8")
        product = self.root / "product"
        (product / "claims").mkdir(parents=True)
        (product / "curbpack.json").write_text('{"packs":["cra-baseline"]}\n', encoding="utf-8")
        (product / "claims" / "one.json").write_text("{}\n", encoding="utf-8")
        work = self.copy.parent / f"{self.copy.name}.work"
        self.assertTrue((work / "coverage.json").is_file())
        exported = _export(self.copy, self.destination)
        self.assertEqual(
            sorted(path.name for path in exported.iterdir()),
            ["CRA-ANNEX-VII-RISK.json", "FIXTURE-VII-1A.json", "pack.json"],
        )
        self.assertFalse((exported / "notes.txt").exists())
        self.assertFalse((exported / "coverage.json").exists())
        self.assertFalse((self.destination / "keys").exists())
        self.assertFalse((self.destination / "curbpack.json").exists())

    def test_copy_failure_removes_the_temp_directory_and_keeps_a_sentinel(self):
        final = self.destination / "cra-baseline"
        final.mkdir()
        sentinel = final / "keep.txt"
        sentinel.write_bytes(b"keep")

        def fail_write(self_path, data):
            raise OSError("simulated copy failure")

        with patch("pathlib.Path.write_bytes", fail_write):
            with self.assertRaises(OSError):
                _export(self.copy, self.destination)
        self.assertEqual(sentinel.read_bytes(), b"keep")
        self.assertFalse((self.destination / "cra-baseline" / "pack.json").exists())
        self.assertFalse(any(path.name.startswith(".export-tmp-") for path in self.destination.iterdir()))
        self.assertEqual(_file_bytes(self.copy), self.source_before)

    def _no_temp(self, source: dict[str, bytes]) -> None:
        self.assertFalse(any(path.name.startswith(".export-tmp-") for path in self.destination.iterdir()))
        self.assertEqual(_file_bytes(self.copy), source)

    def _no_pack(self, source: dict[str, bytes]) -> None:
        self.assertFalse((self.destination / "cra-baseline").exists())
        self._no_temp(source)


def _export(copy, destination, **kwargs):
    from requirements import workspace

    return workspace.export_pack(copy, destination, **kwargs)


def _file_bytes(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }
