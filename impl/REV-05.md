# REV-05 — Management summary with technical appendices

## Summary

- **Story:** `docs/agile/epics/01-pack-editor/stories/REV-05-management-review-pdf.md`
- **Goal:** The saved review report's PDF opens in plain language and keeps the technical records in appendices A–C.
- **Scope / exclusions:** The renderer already in `studio/compile/impl/pdf.py`. No new renderer, no remedy-report PDF, no new Packs v2 field. `compile/pdf.py` stays the import `compile-pdf.py` uses.
- **Baseline:** On 2026-11-26 the existing suite was already green. No product code was added to close the story.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | DONE |
| Approved by | Daniel, 2026-11-26: the PDF renderer already exists; update REV-05 to it and close the story |
| Current task | Task 1 — VERIFIED |
| Last completed task | Task 1 — MGMT-01 through MGMT-04 verified against the existing renderer |
| Last verified tests | 2026-11-26: `.venv/bin/python -m unittest tests.test_compile_pdf` — 13 tests, OK |
| Last checkpoint commit | None. The story and this plan are the closure record. The renderer was already committed. |
| Requirements | MGMT-01–MGMT-04 in the story |
| Packs v2 | `docs/reference/packs2.md` and `docs/reference/outputs.md`. The PDF reads the saved review report. No object or schema change. |
| Blockers | None |
| Exact next action | Complete: no further implementation remains. |

## Requirements and acceptance mapping

| Requirement ID | Story | Test / observed evidence | Status |
| --- | --- | --- | --- |
| REV-R01 | MGMT-01 | `tests/test_compile_pdf.py` `test_management_summary_precedes_technical_appendix` | VERIFIED |
| REV-R02 | MGMT-02 | `test_all_pass_summary_still_requires_human_review`, `test_empty_run_is_not_described_as_success`, `test_decision_and_recorded_signatures_are_not_claimed_verified`, `test_a_passing_check_still_reports_stale_and_missing_bindings` | VERIFIED |
| REV-R03 | MGMT-03 | `test_management_summary_precedes_technical_appendix`, `test_interleaved_claims_group_by_embedded_requirement_and_keep_check_indices` | VERIFIED |
| REV-R04 | MGMT-04 | `test_long_unicode_report_wraps_across_numbered_pages`, `test_cli_creates_readable_pdf_without_changing_report`, `test_existing_pdf_and_source_alias_are_preserved`, `test_invalid_or_missing_source_and_missing_parent_write_nothing`, `test_changed_claim_is_rejected_without_a_pdf` | VERIFIED |

## Tasks

### Task 0 — record the existing renderer (VERIFIED)

The October plan treated the renderer as uncommitted work still to verify. On 2026-11-26 the renderer is `studio/compile/impl/pdf.py`, the command is `compile-pdf.py`, and `tests/test_compile_pdf.py` already describes the opening, the findings order, the three appendices, and the refusal to overwrite an existing PDF. Daniel asked to fit the story to that renderer and close it.

- [x] Current renderer, command, and tests identified.
- [x] Story acceptance rewritten to that behavior, including that a retired Check in this PDF is an assessment `disposition` `retire` on the saved report.

### Task 1 — verify the existing renderer and close

**Requirements:** MGMT-01–MGMT-04.
**Files:** the story, `docs/reference/outputs.md` implementation line, this plan. No renderer change.
**Test first:** Already written. A pass is the already-implemented observation.
**Validation:** `.venv/bin/python -m unittest tests.test_compile_pdf`.
**Stop if:** A test fails, or closing the story would require a new PDF behavior.

- [x] Existing PASS demonstrated: 13 tests, OK, 2026-11-26.
- [x] No implementation added.
- [x] Story status set to DONE and this plan moved to `impl/REV-05.md`.
- [x] `python3 scripts/check_story_plan.py REV-05 --phase done` is the closure check.

## Work log

- **2026-10-29 / Task 1:** Renderer, findings, and appendix tables were written. `.venv/bin/python -m unittest tests.test_compile_pdf tests.test_review_compile`: 20 PASS. The session stopped before review and commit. That history stays here. It is not the closure evidence.

- **2026-11-26 / Task 1:** Daniel: the PDF renderer already exists; update REV-05 to it and close the story. Confirmed `compile-pdf.py` imports `studio.compile.cli`, and `compile/pdf.py` re-exports `studio.compile.impl.pdf.compile_pdf`. The PDF's retired count reads assessment `disposition` `retire` on the saved review report. It does not read remediation `action` `retire`. `.venv/bin/python -m unittest tests.test_compile_pdf`: 13 tests, OK, 2.843s. Story rewritten to that behavior. `outputs.md` now names `studio/compile/impl/pdf.py`. No product code changed.
