"""Regression: Formex NO.P / NO.PARAG markers stay out of law_text."""

from __future__ import annotations

import re
import unittest

from requirements.extract.formex.package import OFFICIAL_XML
from requirements.extract.formex.provisions import extract_section_provisions


_LEAKED_POINT = re.compile(r"^\d+\.\S")


class CraAnnexViiNumberingTest(unittest.TestCase):
    def test_points_3_through_8_omit_no_p_from_law_text(self):
        result = extract_section_provisions(OFFICIAL_XML / "cra", "VII")
        by_locus = {item["locus"]: item["law_text"] for item in result["provisions"]}
        for locus in ("3", "4", "5", "6", "7", "8"):
            law = by_locus[locus]
            self.assertFalse(
                _LEAKED_POINT.match(law),
                f"locus {locus} leaked NO.P into law_text: {law[:40]!r}",
            )
            self.assertFalse(law.startswith(f"{locus}."), f"locus {locus}: {law[:40]!r}")
        # Locators themselves still carry the point numbers.
        self.assertEqual(
            [item["locus"] for item in result["provisions"] if item["locus"] in
             {"3", "4", "5", "6", "7", "8"}],
            ["3", "4", "5", "6", "7", "8"],
        )
        self.assertIn("cybersecurity risks", by_locus["3"])
        self.assertEqual(by_locus["7"], "a copy of the EU declaration of conformity;")


class Nis2ArticleStructuresTest(unittest.TestCase):
    def test_art21_paragraph_and_letter_loci_without_number_leak(self):
        result = extract_section_provisions(OFFICIAL_XML / "nis2", "Art.21")
        loci = [item["locus"] for item in result["provisions"]]
        self.assertIn("21(1)", loci)
        self.assertIn("21(2)(a)", loci)
        self.assertIn("21(5)", loci)
        for item in result["provisions"]:
            self.assertFalse(
                _LEAKED_POINT.match(item["law_text"]),
                f"{item['locus']}: {item['law_text'][:50]!r}",
            )
            self.assertTrue(item["locus"].startswith("21"))

    def test_art1_and_art13_representative_structures(self):
        art1 = extract_section_provisions(OFFICIAL_XML / "nis2", "Art.1")
        self.assertIn("1(1)", [item["locus"] for item in art1["provisions"]])
        self.assertTrue(any(item["locus"].startswith("1(2)(") for item in art1["provisions"]))
        art13 = extract_section_provisions(OFFICIAL_XML / "nis2", "Art.13")
        loci = [item["locus"] for item in art13["provisions"]]
        self.assertGreaterEqual(len(loci), 4)
        self.assertTrue(all(locus.startswith("13") for locus in loci))
        for item in art1["provisions"] + art13["provisions"]:
            self.assertFalse(_LEAKED_POINT.match(item["law_text"]))


if __name__ == "__main__":
    unittest.main()
