# REV-08 — Sign the review and the items

## Summary

- **Story:** `docs/agile/epics/01-pack-editor/stories/REV-08-sign-the-review-items.md`
- **Goal:** Sign locks the review, seals the items, and reporting reads those decisions.
- **Scope / exclusions:** The Sign path already in `app/review_model.py` and `sign_items_document`. Retire is not a decision on this page.
- **Baseline:** The suite below was already green on 2026-11-26.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | DONE |
| Approved by | Daniel, 2026-11-26: the split-plan stories are already implemented; write them from the code and close them |
| Current task | Task 1 — VERIFIED |
| Last completed task | Task 1 — SIGN-01 through SIGN-03 verified |
| Last verified tests | 2026-11-26: `.venv/bin/python -m unittest tests.test_review_items tests.test_check_rounds tests.test_remedy_report tests.test_review_ux tests.test_review_find` — 76 tests, OK |
| Last checkpoint commit | None. The story and this plan are the closure record. The code was already committed. |
| Requirements | SIGN-01–SIGN-03 in the story |
| Packs v2 | `docs/reference/outputs.md` and `docs/reference/packs2.md` §2.6. `what` `review items` was already in the code. No new field. |
| Blockers | None |
| Exact next action | Complete: no further implementation remains. |

## Requirements and acceptance mapping

| Requirement ID | Story | Test / observed evidence | Status |
| --- | --- | --- | --- |
| REV-R01 | SIGN-01 | Review page choices in `studio/review/review_page.py`; passing Check is Passed or Must be fixed | VERIFIED |
| REV-R02 | SIGN-02 | `SignedReportFileTest.test_save_helpers_leave_the_signed_file_bytes_alone`, `CheckDirectoryTest.test_saved_work_and_a_signed_report_stay_separate` | VERIFIED |
| REV-R03 | SIGN-03 | `DecisionAndHistoryTest.test_signed_items_are_what_reporting_reads`, `test_must_fix_on_a_passing_check_becomes_an_assessment_and_accept_does_not`, `test_a_stale_binding_decision_becomes_a_binding_assessment`, `CheckDirectoryTest.test_signed_review_moves_from_start_to_continue_to_view_report` | VERIFIED |

## Tasks

### Task 0 — read the code, not the old plan (VERIFIED)

The split plan's signing step is the code. The page does not offer Retire. The story says that.

- [x] Sign, items digest, and the Check-row labels read from the code and tests.
- [x] Story acceptance written to that behavior.

### Task 1 — verify and close

**Requirements:** SIGN-01–SIGN-03.
**Files:** the story and this plan. No product code.
**Test first:** Already written.
**Validation:** the 76-test command in the checkpoint.
**Stop if:** A cited test fails.

- [x] Existing PASS demonstrated, 2026-11-26.
- [x] No implementation added.
- [x] Story status set to DONE and this plan written to `impl/REV-08.md`.
- [x] `python3 scripts/check_story_plan.py REV-08 --phase done` is the closure check.

## Work log

- **2026-11-26 / Task 1:** Sealed items are what reporting reads. `must_fix` on a passing Check becomes an assessment and `pass` does not. A stale binding becomes a binding assessment. The Check row moves from Start to Continue to View. 76 tests, OK. No product code changed.
