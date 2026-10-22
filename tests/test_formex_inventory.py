"""Formex source inventory coverage and diagnostics."""

from __future__ import annotations

import json
import unittest

from requirements.extract.formex.inventory import inventory_package
from requirements.extract.formex.package import OFFICIAL_XML


class InventoryTest(unittest.TestCase):
    def test_cra_inventory_lists_articles_and_annexes(self):
        inv = inventory_package(OFFICIAL_XML / "cra")
        kinds = {unit["kind"] for unit in inv["units"]}
        self.assertIn("article", kinds)
        self.assertIn("annex", kinds)
        articles = [unit for unit in inv["units"] if unit["kind"] == "article"]
        annexes = [unit for unit in inv["units"] if unit["kind"] == "annex"]
        self.assertEqual(len(articles), 71)
        self.assertEqual([unit["unit_id"] for unit in annexes], [f"Annex.{r}" for r in
                         ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]])
        self.assertTrue(any(unit["unit_id"] == "Art.13" for unit in articles))

    def test_nis2_reports_table_as_unsupported_diagnostic(self):
        inv = inventory_package(OFFICIAL_XML / "nis2")
        reasons = [item["reason"] for item in inv["diagnostics"]]
        self.assertTrue(any("<TBL>" in reason for reason in reasons), reasons)
        self.assertTrue(any(unit["unit_id"] == "Annex.III" for unit in inv["units"]))

    def test_inventory_is_deterministic(self):
        first = inventory_package(OFFICIAL_XML / "cra")
        second = inventory_package(OFFICIAL_XML / "cra")
        self.assertEqual(
            json.dumps(first, sort_keys=True, ensure_ascii=False),
            json.dumps(second, sort_keys=True, ensure_ascii=False),
        )


if __name__ == "__main__":
    unittest.main()
