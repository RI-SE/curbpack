"""CRA XML and NIS2 XML adapters integrated with Requirements extract."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from common.jsonio import read_json
from requirements.extract.adapter import (
    ADAPTERS,
    list_adapters,
    load_adapter,
    section_provisions,
    section_text,
    stage00,
)
from requirements.extract.formex.package import OFFICIAL_XML
from requirements.workspace import extract_section, list_working_copies


def _pack(pack_id: str, name: str) -> dict:
    return {"id": pack_id, "name": name, "version": "0.1.0"}


class XmlAdapterCatalogTest(unittest.TestCase):
    def test_list_adapters_distinguishes_cra_text_cra_xml_and_nis2(self):
        ids = {item["id"]: item for item in list_adapters()}
        self.assertEqual(ids["cra"]["source_format"], "text")
        self.assertEqual(ids["cra-xml"]["source_format"], "formex")
        self.assertEqual(ids["nis"]["source_format"], "formex")
        self.assertEqual(ids["nis"]["source"]["identifier"], "CELEX:32022L2555")
        self.assertEqual(ids["nis"]["source"]["instrument"], "NIS2")
        self.assertNotIn("Sweden", str(ids["nis"]["source"]))


class CraXmlAdapterTest(unittest.TestCase):
    def setUp(self):
        self.adapter = load_adapter(ADAPTERS / "cra-xml" / "adapter.json")
        self.adapter_dir = ADAPTERS / "cra-xml"

    def test_stage00_lists_vii_ready_and_inventory(self):
        listed = stage00(self.adapter, adapter_dir=self.adapter_dir)
        vii = next(item for item in listed["sections"] if item["id"] == "VII")
        self.assertTrue(vii["ready"])
        self.assertEqual(listed["source_format"], "formex")
        self.assertGreaterEqual(listed["inventory"]["unit_count"], 71)
        self.assertIn("cybersecurity risks", section_text(self.adapter_dir, self.adapter, "VII"))

    def test_extract_writes_working_copy_without_mutating_xml(self):
        annex = OFFICIAL_XML / "cra" / "L_202402847EN.007501.fmx.xml"
        before = hashlib.sha256(annex.read_bytes()).hexdigest()
        proposals = [
            {
                "locus": "3",
                "id": "CRA-ANNEX-VII-RISK",
                "locator": "VII.3",
                "discovery_hints": {"concepts": ["risk assessment"]},
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = extract_section(
                root,
                self.adapter_dir,
                self.adapter,
                "VII",
                proposals,
                _pack(self.adapter["pack_id"], "CRA XML"),
                at="2026-10-13T120000Z",
            )
            copies = list_working_copies(root, self.adapter["pack_id"])
            self.assertEqual(copies, ["2026-10-13T120000Z"])
            requirement = read_json(result["copy"] / "CRA-ANNEX-VII-RISK.json")
            self.assertEqual(requirement["source"]["identifier"], "CELEX:32024R2847")
            self.assertNotIn("edition", requirement["source"])
            coverage = read_json(result["work"] / "coverage.json")
            # Other Annex VII loci have no proposals, so coverage stays incomplete.
            self.assertEqual(coverage["status"], "incomplete")
            self.assertTrue(
                any(item["locus"] == "3" and item["status"] == "written" for item in coverage["loci"])
            )
            extract_section(
                root,
                self.adapter_dir,
                self.adapter,
                "VII",
                proposals,
                _pack(self.adapter["pack_id"], "CRA XML"),
                at="2026-10-13T120001Z",
            )
            self.assertEqual(
                list_working_copies(root, self.adapter["pack_id"]),
                ["2026-10-13T120000Z", "2026-10-13T120001Z"],
            )
        self.assertEqual(before, hashlib.sha256(annex.read_bytes()).hexdigest())


class Nis2XmlAdapterTest(unittest.TestCase):
    def setUp(self):
        self.adapter = load_adapter(ADAPTERS / "nis" / "adapter.json")
        self.adapter_dir = ADAPTERS / "nis"

    def test_art21_provisions_and_working_copy(self):
        extracted = section_provisions(self.adapter_dir, self.adapter, "Art.21")
        loci = [item["locus"] for item in extracted["provisions"]]
        self.assertIn("21(1)", loci)
        self.assertIn("21(2)(a)", loci)
        proposals = [
            {
                "locus": "21(1)",
                "id": "NIS2-ART-21-1",
                "locator": "Art.21(1)",
                "note": "EU Directive (EU) 2022/2555 — not Swedish implementing law",
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = extract_section(
                root,
                self.adapter_dir,
                self.adapter,
                "Art.21",
                proposals,
                _pack(self.adapter["pack_id"], "NIS2 EU Directive"),
                at="2026-10-13T130000Z",
            )
            requirement = read_json(result["copy"] / "NIS2-ART-21-1.json")
            self.assertEqual(requirement["source"]["identifier"], "CELEX:32022L2555")
            self.assertEqual(requirement["source"]["instrument"], "NIS2")
            self.assertIn("appropriate and proportionate", requirement["references"][0]["law_text"])

    def test_annex_iii_not_ready(self):
        with self.assertRaises(Exception):
            section_provisions(self.adapter_dir, self.adapter, "III")

    def test_all_forty_six_articles_ready_annexes_not(self):
        ready = [s for s in self.adapter["sections"] if s.get("ready") is True]
        not_ready = [s for s in self.adapter["sections"] if s.get("ready") is not True]
        self.assertEqual(len(ready), 46)
        self.assertTrue(all(item["id"].startswith("Art.") for item in ready))
        self.assertEqual({item["id"] for item in not_ready}, {"I", "II", "III"})

    def test_art1_extract_writes_validated_working_copy(self):
        extracted = section_provisions(self.adapter_dir, self.adapter, "Art.1")
        first = extracted["provisions"][0]
        proposals = [
            {
                "locus": first["locus"],
                "id": "NIS2-ART-1-PROBE",
                "locator": f"Art.1/{first['locus']}",
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            result = extract_section(
                Path(tmp),
                self.adapter_dir,
                self.adapter,
                "Art.1",
                proposals,
                _pack(self.adapter["pack_id"], "NIS2 EU Directive"),
                at="2026-10-13T140000Z",
            )
            requirement = read_json(result["copy"] / "NIS2-ART-1-PROBE.json")
            self.assertEqual(requirement["source"]["identifier"], "CELEX:32022L2555")
            self.assertEqual(requirement["references"][0]["law_text"], first["law_text"])


if __name__ == "__main__":
    unittest.main()
