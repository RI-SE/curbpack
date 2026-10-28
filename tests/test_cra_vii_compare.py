"""CRA Annex VII text-versus-XML comparison artifacts."""

from __future__ import annotations

import unittest

from requirements.extract.formex.compare_cra_vii import compare_annex_vii, write_compare_artifacts


class CraViiCompareTest(unittest.TestCase):
    def test_shared_loci_cover_full_annex_vii_set(self):
        report = compare_annex_vii()
        self.assertEqual(report["structural"]["text_only_loci"], [])
        self.assertEqual(report["structural"]["xml_only_loci"], [])
        self.assertEqual(len(report["structural"]["shared_loci"]), 13)
        self.assertEqual(report["text_source"], "requirements/extract/data/annex_vii.txt")
        self.assertTrue(
            report["xml_source"].startswith("requirements/extract/data/official_xml/")
        )

    def test_classification_counts_after_number_leak_fix(self):
        report = compare_annex_vii()
        counts = report["counts"]
        self.assertEqual(counts["shared_loci"], 13)
        # After NO.P leak fix, points 3–8 should no longer be wording diffs from numbers.
        self.assertEqual(counts["exact_matches"] + counts["normalization_only_matches"]
                         + counts["genuine_wording_differences"], 13)
        self.assertIn("1(d)", report["genuine_wording_differences"])
        # Fixture left unchanged; 1(d) remains an open wording discrepancy.
        self.assertEqual(sorted(report["genuine_wording_differences"]), ["1(d)"])

    def test_write_artifacts(self):
        written = write_compare_artifacts()
        self.assertTrue(written["json"].is_file())
        self.assertTrue(written["markdown"].is_file())
        text = written["markdown"].read_text(encoding="utf-8")
        self.assertIn("Genuine wording", text)
        self.assertIn("1(d)", text)


if __name__ == "__main__":
    unittest.main()
