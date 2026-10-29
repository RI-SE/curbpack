# REV-04 — Readable monochrome review PDF

## Summary

- **Story:** `docs/agile/epics/01-pack-editor/stories/REV-04-compile-pdf.md`.
- **Goal:** `compile-pdf.py --report report.json --out report.pdf` renders an existing review report offline as a paginated monochrome PDF.
- **Scope:** New PDF reporting in `compile/`, thin root command, existing validation reused from `review.compile`. No general Compile/Review migration; no UI changes. User explicitly authorized implementation on 2026-10-29 after the draft proposal and rejected another approval pause.
- **Baseline:** `python3 -m unittest tests.test_review_compile tests.test_review_report_kept`: 12 tests, 10 passed, 2 HTTP tests unable to bind sockets in sandbox. Focused compilation suite passes. No PDF dependency installed initially.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | DONE |
| Approved by | Daniel, conversation 2026-10-29: proceed after REV-04 proposal, no additional approval pause |
| Current task | Task 1 — VERIFIED |
| Last completed task | Task 1 — PDF-01 through PDF-06 verified |
| Last verified tests | 24 PASS, no skips: PDF, compilation, coverage, replace flow and preserved-report regressions |
| Last checkpoint commit | Resolve: git log -1 --format=%H -- impl/REV-04.md |
| Requirements | Story PDF-01 through PDF-06; mapping below, no derived schema |
| Packs v2 | docs/reference/packs2.md and outputs.md; existing report schema unchanged |
| Blockers | None |
| Exact next action | Complete: no further implementation remains; resolve final step commit with git log -- impl/REV-04.md |

## Requirements and acceptance mapping

| Requirement ID | Story | Test / observed evidence | Status |
| --- | --- | --- | --- |
| REV-R01 | PDF-01 | Real CLI, PDF readback, source bytes unchanged | VERIFIED |
| REV-R02 | PDF-02 | Extract run metadata, counts and dirty explanation | VERIFIED |
| REV-R03 | PDF-03 | Embedded Requirement grouping, passages, evidence, Check args and details | VERIFIED |
| REV-R04 | PDF-04 | Decision/signature metadata separate, never claim verification, appendix retained | VERIFIED |
| REV-R05 | PDF-05 | Unicode and multi-page extraction plus raster visual inspection | VERIFIED |
| REV-R06 | PDF-06 | Missing/malformed/mismatched input, existing target, unusable destination preserve input/output | VERIFIED |

## Tasks

### Task 0 — settle scope and review plan (VERIFIED)

Saved review-report JSON is the sole input. Rendering does not read evidence, contact URLs, verify signatures, or load current repository state. Render recorded seal metadata with an explicit verification-not-performed label; retain appendix reasons verbatim. Use ReportLab with its bundled Bitstream Vera TrueType fonts for Unicode text, pypdf as development-only readback dependency. Add ReportLab to requirements.txt and pypdf to requirements-dev.txt. No cloud or custom PDF engine. New `compile/ARCHITECTURE.md` specifies the PDF component only and references current JSON compilation ownership without migrating it. These choices implement the proposal authorized in the conversation. Independent plan review required.

### Task 1 — implement, verify, review and commit PDF rendering (VERIFIED)

**Files:** `compile/__init__.py`, `compile/pdf.py`, `compile/cli.py`, `compile/ARCHITECTURE.md`, root `compile-pdf.py`, requirements files, `tests/test_compile_pdf.py`, `.github/workflows/ci.yml`, outputs.md, story and this plan.
**Test first:** `.venv/bin/python -m unittest tests.test_compile_pdf.CompilePdfTest.test_cli_creates_readable_pdf_without_changing_report` runs a subprocess and fails an assertion that the requested PDF exists. No production imports are used in the test module; this is observable command acceptance rather than an import error. Fixtures use real canonical Claim digests and existing schemas; pypdf inspects generated PDF text, page count and preservation. CLI tested through subprocess.
**Implementation:** Validate input with existing load_report. ReportLab Platypus paragraphs with escaped text, word wrapping, built-in black/white rules, A4 pages, page footer. Include the exact reviewer-facing statement `Prepares evidence for human review — not a conformity assessment.` and assert it in PDF text readback. Overview, explicit totals, loaded Packs, Requirement groups with all Claims and Checks, source passages, rationale, source args and raw Check args, recorded signature metadata and appendix. Show PASS/FAIL/SKIPPED as text; no controls. Do not read remote URLs or artefacts. Build to a temporary file in target directory, publish without clobbering via exclusive hard link, remove temporary file on any error. Reject existing target including source alias. No mkdir outside explicit target parent.
**Validation:** Real CLI, pypdf readback, Unicode/long multi-page case, source and output preservation, metadata escaping, empty result. Focused existing compilation regressions. Generate a PDF from the user's test product report in /tmp, raster-preview pages locally. Existing HTTP regression failures remain baseline, unrelated to this component.
**Stop:** Do not alter JSON schema, live report bytes or signed/published source. No whole-tree refactor. New concrete blockers get recorded rather than silently changing contracts.
**Review:** Independent read-only code review with story, contracts, policy, diff. Address blocking findings and rerun affected tests before a local commit of only this step's changes.

## Work log

- **2026-10-29 / Task 0:** Inspected current architecture, REV-03, REV-04 proposal, review.compile validation, relevant tests, policies, baseline and dependency availability. User's instruction authorizes proceeding without renewed plan approval. Plan-mode switching is unavailable in this client; canonical plan retained here. No production code yet. First plan review found two issues: add the required reviewer-facing statement and establish RED via the executable acceptance assertion, not an import failure. Both addressed. CI installs requirements-dev.txt so pypdf stays a test dependency. Visual fixture explicitly covers Swedish text, long multi-path arguments, long passages, and several pages.

- **2026-10-29 / Task 0:** Independent re-review approved, no issues. Advisory: show five signature facts with version digest, install test dependencies in both CI jobs, and record multi-page visual acceptance. User approval already recorded above.

- **2026-10-29 / Task 1 IMPL-START:** CLI acceptance RED: 1 test failed at the assertion that PDF output exists; requested command absent. Implementing PDF-01–PDF-06 in planned files. Installed ReportLab 4.5.1 and pypdf 6.21.4 in .venv; network download required sandbox escalation, approved automatically.

- **2026-10-29 / Task 1 REVIEW-START:** Implemented PDF renderer, CLI, architecture, dependency and CI wiring, docs. `.venv/bin/python -m unittest tests.test_compile_pdf`: 7 PASS. `.venv/bin/python -m unittest tests.test_compile_pdf tests.test_review_compile tests.test_review_coverage tests.test_review_replace_flow tests.test_review_report_kept` with local socket permission: 23 PASS, no skips. Generated actual-product PDF (21 pages) and Swedish/long-path fixture (7 pages) under ignored tmp/rev04. First-page visual inspection passes; multipage inspection in progress.

- **2026-10-29 / Task 1 VERIFIED:** Final command `.venv/bin/python -m unittest tests.test_compile_pdf tests.test_review_compile tests.test_review_coverage tests.test_review_replace_flow tests.test_review_report_kept`: 24 PASS in 5.136s, no skips, run with local-port permission. PDF suite: 8 cases. Initial sandbox HTTP errors disappeared with that permission; no regression remains in this scope.
- **2026-10-29 / Task 1 review:** Independent code review: no Critical/Important findings. Minor recommendation for multiple Requirements/interleaved Claims/repeated Check ids addressed with an additional real-command PDF-readback test; all 24 checks above rerun afterwards. No production changes after review.
- **2026-10-29 / Task 1 visual acceptance:** Generated `tmp/rev04/review-report.pdf` from `/tmp/curbpack-output-review-report.json` (actual 13-Claim/19-Check run; 21 pages) and `tmp/rev04/long-report.pdf` from `tests.test_compile_pdf.report_fixture(long=True)` (7 pages). Rendered first actual-report page and selected later pages with `qlmanage -t -s 1200`; inspected actual report pages 1–2 and long fixture pages 2 and 5. Rendered long fixture page 2 independently with local macOS PDFKit to confirm the full page, including footer. Swedish characters, escaped literal markup, long tokens and paths wrap; no clipping, overlap, colours or controls observed on inspected pages. Remaining pages checked by text readback and page-count tests, not individually visually inspected.
- **2026-10-29 / Task 1 preservation:** Source report bytes unchanged; missing/invalid reports, changed Claim digest, missing output parent, existing output and input/output alias covered. Existing PDFs cannot be replaced. No product files, signatures, decisions or schemas changed. PDF signature metadata is explicitly unverified. Full repository test suite not run; focused impacted regressions passed. Dependencies now include ReportLab runtime and pypdf development-only. Samples are ignored under tmp/ and excluded from commits.
