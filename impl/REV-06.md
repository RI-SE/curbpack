# REV-06 — Item, provenance and reuse

## Summary

- **Story:** `docs/agile/epics/01-pack-editor/stories/REV-06-item-provenance-and-reuse.md`
- **Goal:** One `review_item` per Check, with provenance from the run, reused only when the checked material is unchanged.
- **Scope / exclusions:** The behavior already in `studio/review/impl/items.py`. No new field and no new test.
- **Baseline:** The suite below was already green on 2026-11-26.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | DONE |
| Approved by | Daniel, 2026-11-26: the split-plan stories are already implemented; write them from the code and close them |
| Current task | Task 1 — VERIFIED |
| Last completed task | Task 1 — ITEM-01 through ITEM-03 verified against the existing items |
| Last verified tests | 2026-11-26: `.venv/bin/python -m unittest tests.test_review_items tests.test_check_rounds tests.test_remedy_report tests.test_review_ux tests.test_review_find` — 76 tests, OK |
| Last checkpoint commit | None. The story and this plan are the closure record. The code was already committed. |
| Requirements | ITEM-01–ITEM-03 in the story |
| Packs v2 | `docs/reference/studio-internal.md`. No Packs v2 field added. |
| Blockers | None |
| Exact next action | Complete: no further implementation remains. |

## Requirements and acceptance mapping

| Requirement ID | Story | Test / observed evidence | Status |
| --- | --- | --- | --- |
| REV-R01 | ITEM-01 | `tests/test_review_items.py` items created from a run, including the binding Check | VERIFIED |
| REV-R02 | ITEM-02 | `FilesSidecarTest.test_a_dirty_studio_check_records_size_and_mtime_once`, `DirtyProvenanceTest.test_opening_a_review_copies_the_dirty_sidecar_into_provenance` | VERIFIED |
| REV-R03 | ITEM-03 | `ReuseTest.test_clean_commits_reuse_only_the_check_whose_file_is_unchanged`, `ReuseTest.test_a_missing_dirty_sidecar_keeps_the_decision_and_requires_a_new_one`, `DecisionAndHistoryTest.test_the_next_review_shows_history_without_copying_it_into_the_decision` | VERIFIED |

## Tasks

### Task 0 — read the code, not the old plan (VERIFIED)

The split plan of 23 November named REV-06 and marked its todo complete. No story file existed. The code and `studio-internal.md` are the behavior this story now states.

- [x] Item, provenance, and reuse read from `studio/review/impl/items.py` and the existing tests.
- [x] Story acceptance written to that behavior.

### Task 1 — verify and close

**Requirements:** ITEM-01–ITEM-03.
**Files:** the story and this plan. No product code.
**Test first:** Already written. A pass is the already-implemented observation.
**Validation:** the 76-test command in the checkpoint.
**Stop if:** A cited test fails.

- [x] Existing PASS demonstrated, 2026-11-26.
- [x] No implementation added.
- [x] Story status set to DONE and this plan written to `impl/REV-06.md`.
- [x] `python3 scripts/check_story_plan.py REV-06 --phase done` is the closure check.

## Work log

- **2026-11-26 / Task 1:** Daniel: the split-plan stories are implemented; write them from the code and close them. Dirty sidecar, provenance copy, clean reuse, and a missing sidecar were green in `tests.test_review_items`. 76 tests across the five review modules, OK. No product code changed.
