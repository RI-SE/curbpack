# REV-07 — One workspace per Check

## Summary

- **Story:** `docs/agile/epics/01-pack-editor/stories/REV-07-one-workspace-per-check.md`
- **Goal:** Each Check has its own `review_items.json`, and an existing file asks continue or start over.
- **Scope / exclusions:** The behavior already in the Check directory and `open_review_items`. No new file layout.
- **Baseline:** The suite below was already green on 2026-11-26.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | DONE |
| Approved by | Daniel, 2026-11-26: the split-plan stories are already implemented; write them from the code and close them |
| Current task | Task 1 — VERIFIED |
| Last completed task | Task 1 — WORK-01 and WORK-02 verified |
| Last verified tests | 2026-11-26: `.venv/bin/python -m unittest tests.test_review_items tests.test_check_rounds tests.test_remedy_report tests.test_review_ux tests.test_review_find` — 76 tests, OK |
| Last checkpoint commit | None. The story and this plan are the closure record. The code was already committed. |
| Requirements | WORK-01 and WORK-02 in the story |
| Packs v2 | `docs/reference/workspace.md`. No Packs v2 field added. |
| Blockers | None |
| Exact next action | Complete: no further implementation remains. |

## Requirements and acceptance mapping

| Requirement ID | Story | Test / observed evidence | Status |
| --- | --- | --- | --- |
| REV-R01 | WORK-01 | `WorkspaceTest.test_two_runs_do_not_share_a_file`, `CheckDirectoryTest.test_a_new_studio_check_is_a_directory` | VERIFIED |
| REV-R02 | WORK-02 | `WorkspaceTest.test_continue_merges_and_start_over_keeps_only_the_new_items`, `ReviewStartTest.test_an_unsigned_report_asks_before_the_same_run_opens_again` | VERIFIED |

## Tasks

### Task 0 — read the code, not the old plan (VERIFIED)

The split plan asked for one workspace per run and per report. The code keeps `review_items.json` in the Studio Check directory. The story says that.

- [x] Paths and the continue question read from the tests.
- [x] Story acceptance written to that behavior.

### Task 1 — verify and close

**Requirements:** WORK-01 and WORK-02.
**Files:** the story and this plan. No product code.
**Test first:** Already written.
**Validation:** the 76-test command in the checkpoint.
**Stop if:** A cited test fails.

- [x] Existing PASS demonstrated, 2026-11-26.
- [x] No implementation added.
- [x] Story status set to DONE and this plan written to `impl/REV-07.md`.
- [x] `python3 scripts/check_story_plan.py REV-07 --phase done` is the closure check.

## Work log

- **2026-11-26 / Task 1:** Two runs do not share `review_items.json`. Continue merges and start over keeps the new items. The page asks before an existing file is replaced. 76 tests, OK. No product code changed.
