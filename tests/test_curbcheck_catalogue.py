"""The copied curbcheck procedures keep every Curbpack row."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITES = ROOT / "tests/check/suites"

SUITE_IDS = (
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
)


class CurbcheckCatalogueTest(unittest.TestCase):
    def test_every_suite_id_is_a_copied_procedure(self):
        texts = [path.read_text(encoding="utf-8") for path in SUITES.glob("*.md")]
        blob = "\n".join(texts)
        for case_id in SUITE_IDS:
            rows = [line for line in blob.splitlines() if line.startswith(f"| {case_id} |")]
            self.assertEqual(len(rows), 1, case_id)
        ev = (SUITES / "EV.md").read_text(encoding="utf-8")
        self.assertIn("## EV-002 —", ev)
        self.assertIn("SUT=curbpack-studio ./setup.sh R1 --commit", ev)
        self.assertIn("R2 via Studio fixture `setup.sh`", ev)

    def test_code_review_procedure_is_the_full_text(self):
        text = (ROOT / "tests/check/docs/procedures/2_code_review_procedures.md").read_text(encoding="utf-8")
        for number in range(1, 12):
            self.assertIn(f"| CR-{number:02d} |", text)
        self.assertIn("Can malformed, ambiguous, duplicate, conflicting or unsupported rules", text)
        ids = (ROOT / "tests/check/manual.ids").read_text(encoding="utf-8").split()
        self.assertEqual(ids, [f"CR-{number:02d}" for number in range(1, 12)])

    def test_runner_uses_the_verification_run(self):
        runner = (ROOT / "tests/check/automation/suit-runner.sh").read_text(encoding="utf-8")
        self.assertIn("tests/check/suites", runner)
        self.assertIn("REFERENCE_PRODUCT_ROOT", runner)
        self.assertIn("python3 -m checks", runner)
        self.assertNotIn("curbpack check", runner)
        self.assertNotIn("procedure calls curbpack", runner)
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        test_recipe = makefile.split("test:\n", 1)[1].split("\n\n", 1)[0]
        self.assertNotIn("tests/check", test_recipe)
