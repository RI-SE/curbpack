"""CRA Annex VII provision extraction from official Formex XML."""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from requirements.extract.atomize import atomize
from requirements.extract.formex.package import OFFICIAL_XML
from requirements.extract.formex.provisions import extract_section_provisions


class CraAnnexViiProvisionsTest(unittest.TestCase):
    def test_annex_vii_loci_match_text_atomizer_set(self):
        result = extract_section_provisions(OFFICIAL_XML / "cra", "VII")
        loci = [item["locus"] for item in result["provisions"]]
        self.assertEqual(
            loci,
            ["1(a)", "1(b)", "1(c)", "1(d)", "2(a)", "2(b)", "2(c)", "3", "4", "5", "6", "7", "8"],
        )
        point3 = next(item for item in result["provisions"] if item["locus"] == "3")
        self.assertIn("cybersecurity risks", point3["law_text"])

    def test_repeated_extract_is_byte_identical(self):
        first = extract_section_provisions(OFFICIAL_XML / "cra", "VII")
        second = extract_section_provisions(OFFICIAL_XML / "cra", "VII")
        self.assertEqual(first, second)

    def test_source_xml_bytes_unchanged(self):
        path = OFFICIAL_XML / "cra" / "L_202402847EN.007501.fmx.xml"
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        extract_section_provisions(OFFICIAL_XML / "cra", "VII")
        after = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(before, after)

    def test_text_adapter_still_emits_same_loci(self):
        # Regression anchor for the existing CRA text fixture path.
        text = Path(__file__).resolve().parents[1] / "requirements/extract/data/annex_vii.txt"
        loci = [item["locus"] for item in atomize(text.read_text(encoding="utf-8"))]
        self.assertEqual(
            loci,
            ["1(a)", "1(b)", "1(c)", "1(d)", "2(a)", "2(b)", "2(c)", "3", "4", "5", "6", "7", "8"],
        )


if __name__ == "__main__":
    unittest.main()
