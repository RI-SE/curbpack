"""PE-11: export the selected working copy as a Packs v2 directory.

REQ-PE-013 and REQ-PE-014 apply: provenance stays in the copied bytes, and
export adds no Pack field.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checks.run import run_repository
from common.canonical import pack_directory_digest
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


def _file_bytes(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }
