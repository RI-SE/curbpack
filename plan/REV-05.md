# REV-05 — Management summary with technical appendices

## Summary

- **Story:** `docs/agile/epics/01-pack-editor/stories/REV-05-management-review-pdf.md`
- **Goal:** Make the opening useful to management and put full technical records into appendix tables.
- **Scope / exclusions:** PDF presentation and tests/docs only. Existing JSON compilation, validation, signing and output preservation stay unchanged. Do not resume from completed `impl/REV-04.md`. Do not rewrite the renderer that is already in the working tree.
- **Baseline:** REV-04 renderer and tests were present. On 2026-10-29 the PDF suite was 8 PASS before this story's edits. The uncommitted tree now contains the REV-05 renderer and 10 PDF tests.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | APPROVED |
| Approved by | Daniel, 2026-10-29: make the main report less technical, with details in appendix tables |
| Current task | Task 1 — resume verification of the existing uncommitted renderer |
| Last completed task | Task 1 implementation is in the working tree; review and commit of that code are not done |
| Last verified tests | 2026-10-29 work log: `.venv/bin/python -m unittest tests.test_compile_pdf tests.test_review_compile` — 20 PASS. That command was not rerun when this checkpoint was corrected on 2026-10-30 |
| Last checkpoint commit | None for this plan until the resume commit. Implementation files stay unstaged |
| Requirements | MGMT-01–MGMT-04 in the story |
| Packs v2 | `docs/reference/packs2.md` and `docs/reference/outputs.md`; no object or schema changes |
| Blockers | None |
| **Exact next action** | Keep the files listed under Resume. Rerun `python3 -m unittest tests.test_compile_pdf tests.test_review_compile`. If they pass, render `/tmp/curbpack-output-review-report.json` to `tmp/rev05/review-report.pdf` and inspect it. Then independent review, and one commit of only the REV-05 files. |

## Requirements and acceptance mapping

| Requirement ID | Story | Test / observed evidence | Status |
| --- | --- | --- | --- |
| REV-R01 | MGMT-01 | `tests/test_compile_pdf.py` `test_management_summary_precedes_technical_appendix` | In the working tree; rerun required |
| REV-R02 | MGMT-02 | `test_all_pass_summary_still_requires_human_review`, `test_empty_run_is_not_described_as_success`, `test_decision_and_recorded_signatures_are_not_claimed_verified` | In the working tree; rerun required |
| REV-R03 | MGMT-03 | Same module: appendix text, historical grouping, check indices | In the working tree; rerun required |
| REV-R04 | MGMT-04 | Long Unicode fixture in `test_long_unicode_report_wraps_across_numbered_pages`; visual check of `/tmp/curbpack-output-review-report.json` still open | Partial |

## Resume

The implementation already exists. Read it and the tests. A passing test is the already-implemented observation. Do not add a second acceptance test to manufacture a RED, and do not replace `compile/pdf.py` with a new renderer.

Keep these REV-05 edits:

- `compile/pdf.py`
- `tests/test_compile_pdf.py`
- `docs/reference/outputs.md`
- `docs/agile/epics/01-pack-editor/stories/REV-05-management-review-pdf.md`
- `plan/REV-05.md`

Leave these other working-tree edits untouched. Do not stage them, revert them, or fold them into the REV-05 commit:

- `app/pages.py`
- `checks/ARCHITECTURE.md`
- `docs/agile/epics/01-pack-editor/stories/PE-01-open-pack-editor.md`
- `docs/development/README.md`
- `review/ARCHITECTURE.md`
- `tests/test_cover_navigation.py`
- `tests/test_pilot_pack_selection.py`
- `tests/test_ui_smoke.py`
- `all-nya-curbpack.md`

The acceptance sentences already asserted by `tests/test_compile_pdf.py` are the spec for the opening and the appendix boundary. The opening, meaning the text before `Appendix A — Run and source records`, carries the management summary and the Review findings. It includes counts, follow-up wording, `uncommitted changes`, and `B.1`. It does not include the full commit, the word `worktree`, `digest`, raw check arguments, `https://`, or certificate reasons. Those remain in the appendices. Findings state that changes since the run, unresolved current evidence, and independent signature verification are not assessed.

Sample for MGMT-04, confirmed on 2026-10-30: `/tmp/curbpack-output-review-report.json` is a saved review report with 13 run Claims, 19 Checks, 13 Requirements, 13 embedded Claims and 13 appendix entries. It has no `decision` and no `signed`. It lives outside this repository. If that file is missing, stop and ask. Do not invent 13 Claims. Write the new PDF to `tmp/rev05/review-report.pdf` and leave any earlier PDF in place. Generate the long Unicode fixture from `tests.test_compile_pdf.report_fixture(long=True)` as well. Inspect the main page, an appendix table, a split long row, and the footer with local PDFKit or `qlmanage`. Commit no generated PDF.

## Tasks

### Task 0 — review and baseline (VERIFIED)

Read REV-05, REV-04, REV-03, `compile/ARCHITECTURE.md`, system architecture/requirements, policies and the existing renderer/tests. Independent review uses the repository workflow's existing reviewer prompt. The maintainer authorized this presentation change.

- [x] Existing work, boundaries and maintainer authorization recorded.
- [x] Independent plan review completed with no blocking findings.

### Task 1 — verify the existing renderer and commit it

**Requirements:** MGMT-01–MGMT-04.
**Files:** the five REV-05 paths under Resume. No other working-tree file.
**Test first:** Already written in `tests/test_compile_pdf.py`. On 2026-10-29 a missing Appendix A boundary was the RED. The current tree contains the renderer those tests describe. Rerun the two modules below. A pass means the behavior is already present.
**Validation:** `python3 -m unittest tests.test_compile_pdf tests.test_review_compile`. Render `/tmp/curbpack-output-review-report.json` and the long Unicode fixture. Inspect pages as in Resume. Independent read-only review of `git diff HEAD` for the five REV-05 files only. Fix blocking findings in those files, rerun the affected tests, and one re-review. Then stage only those files.
**Stop if:** The sample JSON is gone, a change needs a new Packs v2 field, or a fix would require editing a file listed as untouched.

- [x] RED for the missing appendix boundary was observed on 2026-10-29.
- [x] Renderer, findings, appendix tables and acceptance tests are in the working tree.
- [ ] Focused tests rerun on this tree, and the named sample PDF inspected.
- [ ] Independent review completed and blocking findings resolved.
- [ ] One local commit contains only the REV-05 files.

## Work log

- **2026-10-29 / Task 0:** User requested a less technical main report, technical detail in appendix tables. Existing REV-04 is complete; opened a new story and plan rather than resuming `impl/REV-04.md`. Inspected renderer, architecture, previous story and concurrent working-tree edits.

- **2026-10-29 / Task 0:** Fresh baseline `.venv/bin/python -m unittest tests.test_compile_pdf`: 8 PASS. Independent plan reviewer approved with no blocking findings. Existing user authorization applies.

- **2026-10-29 / Task 1 IMPL-START:** New acceptance RED observed: PDF had no Appendix A boundary. User supplied Copilot layout guidance mid-task: retain a short management summary, add separate Review findings with recorded failure/skip reasons and human-review questions, and a compact reviewed-item index before detailed appendix tables. Keep decision free text; do not invent verification or live-comparison counts. Compact checker/revision identity is allowed in the summary; full hashes remain in the appendix. Initial table implementation passed 9/10 tests; the remaining test selected the summary cross-reference rather than the actual appendix heading and was corrected to use the full heading.

- **2026-10-29 / Task 1 REVIEW-START:** Renderer now has management summary, separate Review findings, and three appendix table sections with a compact reviewed-item index. `.venv/bin/python -m unittest tests.test_compile_pdf tests.test_review_compile`: 20 PASS. Actual sample had 24 pages, main narrative on pages 1–2, Appendix A on page 3. Summary, findings, reviewed-item table and a long split row were inspected via local PDFKit. Widened narrow Passage/id columns after that inspection. The session stopped before the final regeneration, the independent review, and the commit.

- **2026-10-30 / Task 1 resume checkpoint:** Corrected this plan so a new session does not start over. Confirmed `/tmp/curbpack-output-review-report.json` is still the 13-Claim/19-Check report (13 Requirements, 13 embedded Claims, 13 appendix entries, no decision, no signed). Named the REV-05 files to keep and the other dirty files to leave alone. Tests from 2026-10-29 were not rerun for this documentation edit. No product code in this step.
