"""Tests for the story plan guardrail; independent of PoC2 application imports."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_story_plan.py"
spec = importlib.util.spec_from_file_location("story_plan_guardrail", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

SAMPLE = """# CHK-05 — Test

## Summary

- Goal: test

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | APPROVED |
| Approved by | Project owner, 2026-10-23 |
| Current task | Task 1 |
| Last completed task | Task 1 |
| Last verified tests | `python -m unittest x` — PASS 3 tests |
| Last checkpoint commit | Resolve from git log |
| Requirements | docs/req/checks.md CHK-R01 |
| Packs v2 | docs/reference/packs2.md at commit abc123 |
| Blockers | None |
| **Exact next action** | Task 2: write test |

## Requirements and acceptance mapping

| Requirement ID | Story | Test / observed evidence | Status |
| --- | --- | --- | --- |
| CHK-R01 | CHK-05 | tests/test_checks.py | APPROVED |

## Tasks

### Task 1 — test
- [x] Test exists.

## Work log

- **2026-10-23 / Task 1:** `python -m unittest x` PASS 3 tests. Diff reviewed.
"""


class StoryPlanTest(unittest.TestCase):
    def test_approved_checkpoint_passes(self):
        self.assertEqual([], module.validate_plan(SAMPLE, "checkpoint"))

    def test_missing_next_action_rejected(self):
        changed = SAMPLE.replace("| **Exact next action** | Task 2: write test |", "")
        self.assertIn("Missing/empty checkpoint field: Exact next action", module.validate_plan(changed, "ready"))

    def test_unapproved_plan_cannot_build(self):
        changed = SAMPLE.replace("Plan status | APPROVED", "Plan status | DRAFT")
        self.assertTrue(any("status" in e for e in module.validate_plan(changed, "ready")))

    def test_test_not_run_rejected_for_checkpoint(self):
        changed = SAMPLE.replace("`python -m unittest x` — PASS 3 tests", "Not run")
        self.assertTrue(any("Last verified tests" in e for e in module.validate_plan(changed, "checkpoint")))

    def test_done_must_close_tasks(self):
        changed = SAMPLE.replace("Plan status | APPROVED", "Plan status | DONE").replace("- [x] Test exists.", "- [ ] Test exists.")
        self.assertTrue(any("Unchecked" in e for e in module.validate_plan(changed, "done")))

    def test_template_is_draft_only(self):
        template = (SCRIPT.parents[1] / "plan" / "TEMPLATE.md").read_text()
        self.assertEqual([], module.validate_plan(template, "draft"))
        self.assertTrue(module.validate_plan(template, "ready"))


if __name__ == "__main__":
    unittest.main()
