# REV-09 — Remediation

## Summary

- **Story:** `docs/agile/epics/01-pack-editor/stories/REV-09-remediation.md`
- **Goal:** Remediation edits the Check, records history, and Sign Off seals a remedy report without changing the locked review.
- **Scope / exclusions:** The remediation already in `studio/review`. A comment is the note, not a history entry. The management PDF is REV-05.
- **Baseline:** The suite below was already green on 2026-11-26.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | DONE |
| Approved by | Daniel, 2026-11-26: the split-plan stories are already implemented; write them from the code and close them |
| Current task | Task 1 — VERIFIED |
| Last completed task | Task 1 — REM-01 through REM-05 verified |
| Last verified tests | 2026-11-26: `.venv/bin/python -m unittest tests.test_review_items tests.test_check_rounds tests.test_remedy_report tests.test_review_ux tests.test_review_find` — 76 tests, OK |
| Last checkpoint commit | None. The story and this plan are the closure record. The code was already committed. |
| Requirements | REM-01–REM-05 in the story |
| Packs v2 | `docs/reference/outputs.md` remedy report and `docs/reference/packs2.md` `what` `remedy report`. No new field. |
| Blockers | None |
| Exact next action | Complete: no further implementation remains. |

## Requirements and acceptance mapping

| Requirement ID | Story | Test / observed evidence | Status |
| --- | --- | --- | --- |
| REV-R01 | REM-01 | `CheckDirectoryTest.test_signed_review_moves_from_start_to_continue_to_view_report` | VERIFIED |
| REV-R02 | REM-02 | `DecisionAndHistoryTest.test_a_comment_replaces_the_previous_note_and_can_be_cleared` | VERIFIED |
| REV-R03 | REM-03 | `ProjectRunTest`, `test_a_changed_check_is_found_through_old_check_digest`, `test_rebind_history_is_written_next_to_the_run`, `test_retiring_the_claim_retires_every_row_and_one_check_does_not`, `tests.test_review_find` | VERIFIED |
| REV-R04 | REM-04 | `RegressionTest.test_ok_updates_the_original_deviation_and_leaves_the_new_failure_out`, `test_rollback_restores_the_claim_and_records_the_event`, `test_the_same_failures_are_inside_and_a_different_pair_is_outside` | VERIFIED |
| REV-R05 | REM-05 | `RemedySignatureTest`, `tests.test_remedy_report` | VERIFIED |

## Tasks

### Task 0 — read the code, not the old plan (VERIFIED)

The split plan said a comment is a history entry and that Retire is recorded for a later sign. The code keeps the note on `comment`, retires the Check immediately, and Sign Off writes the remedy report. Outside, OK, and Rollback are part of that same remediation. The story says that.

- [x] Remediation actions read from `studio/review/impl/items.py` and the remedy tests.
- [x] Story acceptance written to that behavior.

### Task 1 — verify and close

**Requirements:** REM-01–REM-05.
**Files:** the story and this plan. No product code.
**Test first:** Already written.
**Validation:** the 76-test command in the checkpoint.
**Stop if:** A cited test fails.

- [x] Existing PASS demonstrated, 2026-11-26.
- [x] No implementation added.
- [x] Story status set to DONE and this plan written to `impl/REV-09.md`.
- [x] `python3 scripts/check_story_plan.py REV-09 --phase done` is the closure check.

## Work log

- **2026-11-26 / Task 1:** Comment replace, retire, retarget, rebind, outside, OK, Rollback, and the remedy seal were green. 76 tests, OK. No product code changed.
