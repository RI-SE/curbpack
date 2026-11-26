# REV-10 — The next review

## Summary

- **Story:** `docs/agile/epics/01-pack-editor/stories/REV-10-the-next-review.md`
- **Goal:** The next Check is a new review. Unchanged underlag reuses the signed decision. A missing Check is retired only with `action` `retire`.
- **Scope / exclusions:** The take-in already in `studio/review/impl/items.py`. Sign on the new review stays REV-08.
- **Baseline:** The suite below was already green on 2026-11-26.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | DONE |
| Approved by | Daniel, 2026-11-26: the split-plan stories are already implemented; write them from the code and close them |
| Current task | Task 1 — VERIFIED |
| Last completed task | Task 1 — NEXT-01 through NEXT-03 verified |
| Last verified tests | 2026-11-26: `.venv/bin/python -m unittest tests.test_review_items tests.test_check_rounds tests.test_remedy_report tests.test_review_ux tests.test_review_find` — 76 tests, OK |
| Last checkpoint commit | None. The story and this plan are the closure record. The code was already committed. |
| Requirements | NEXT-01–NEXT-03 in the story |
| Packs v2 | No new field. The new review signs through the existing review report. |
| Blockers | None |
| Exact next action | Complete: no further implementation remains. |

## Requirements and acceptance mapping

| Requirement ID | Story | Test / observed evidence | Status |
| --- | --- | --- | --- |
| REV-R01 | NEXT-01 | `CheckDirectoryTest.test_a_remediation_run_is_not_listed_as_performed`, `test_a_new_studio_check_is_a_directory` | VERIFIED |
| REV-R02 | NEXT-02 | `TakeInRemedyTest.test_unchanged_underlag_reuses_the_signed_decision`, `test_changed_underlag_suggests_pass_and_records_the_transition`, `test_keeping_new_decisions_stores_the_history_on_the_items`, `KeepHistoryTest.test_keep_writes_the_history_into_the_new_review_items` | VERIFIED |
| REV-R03 | NEXT-03 | `DecisionAndHistoryTest.test_a_comment_is_not_retire_and_a_retire_action_is` | VERIFIED |

## Tasks

### Task 0 — read the code, not the old plan (VERIFIED)

The split plan's next review is the take-in the page already offers. A comment does not retire a Check that the new run lacks. The story says that.

- [x] Take-in and retired absence read from the tests.
- [x] Story acceptance written to that behavior.

### Task 1 — verify and close

**Requirements:** NEXT-01–NEXT-03.
**Files:** the story and this plan. No product code.
**Test first:** Already written.
**Validation:** the 76-test command in the checkpoint.
**Stop if:** A cited test fails.

- [x] Existing PASS demonstrated, 2026-11-26.
- [x] No implementation added.
- [x] Story status set to DONE and this plan written to `impl/REV-10.md`.
- [x] `python3 scripts/check_story_plan.py REV-10 --phase done` is the closure check.

## Work log

- **2026-11-26 / Task 1:** Unchanged underlag reuses the signed decision. Changed underlag does not. A comment is not a retire, and `action` `retire` is. 76 tests, OK. No product code changed.
