"""The curbcheck catalogue keeps every Curbpack row and does not call it a pass."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CATALOGUE_IDS = (
    "PK-001", "PK-002", "PK-003", "PK-004", "PK-005",
    "EV-001", "EV-002", "EV-003", "EV-004", "EV-005", "EV-006", "EV-007", "EV-008", "EV-009",
    "FS-001", "FS-002", "FS-003", "FS-004", "FS-005", "FS-006", "FS-007",
    "DT-001", "DT-002", "DT-003", "DT-004",
    "PV-001", "PV-002", "PV-003", "PV-004", "PV-005", "PV-006", "PV-007",
    "RP-001", "RP-002", "RP-003", "RP-004", "RP-005", "RP-006", "RP-007",
    "OP-001", "OP-002", "OP-003", "OP-004", "OP-005", "OP-006",
    "NB-001", "NB-002",
    "RB-001", "RB-002", "RB-003", "RB-004",
    "RL-001", "RL-002", "RL-003", "RL-004", "RL-005",
    "CL-001", "CL-002", "CL-003", "CL-004",
    "UV-001", "UV-002", "UV-003", "UV-004", "UV-005", "UV-006", "UV-007", "UV-008",
    "CR-01", "CR-02", "CR-03", "CR-04", "CR-05", "CR-06", "CR-07", "CR-08", "CR-09", "CR-10", "CR-11",
)


class CurbcheckCatalogueTest(unittest.TestCase):
    def test_every_catalogue_id_is_listed_once(self):
        text = (ROOT / "tests/check/catalogue.md").read_text(encoding="utf-8")
        for case_id in CATALOGUE_IDS:
            rows = [line for line in text.splitlines() if line.startswith(f"| {case_id} |")]
            self.assertEqual(len(rows), 1, case_id)

    def test_manual_ids_match_the_code_review_rows(self):
        ids = (ROOT / "tests/check/manual.ids").read_text(encoding="utf-8").split()
        self.assertEqual(ids, [f"CR-{number:02d}" for number in range(1, 12)])

    def test_make_test_does_not_run_the_curbcheck_suite(self):
        text = (ROOT / "Makefile").read_text(encoding="utf-8")
        test_recipe = text.split("test:\n", 1)[1].split("\n\n", 1)[0]
        self.assertNotIn("test-curbcheck", test_recipe)
        self.assertNotIn("tests/check/run.sh", test_recipe)
        self.assertIn("test-curbcheck:\n\t@sh tests/check/run.sh", text.replace("    ", "\t"))
