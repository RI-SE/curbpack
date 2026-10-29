# REV-04 — Readable monochrome review PDF

**Status:** DONE, 2026-10-29. Evidence and completed plan: `impl/REV-04.md`.
**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md)
**Related:** [REV-03](REV-03-Review-enhancements.md), [TL-05](../../09-standalone-tools/stories/TL-05-start-compile.md), [ARCH-03](../../02-modularize-studio/stories/ARCH-03-subsystem-ownership.md).

**As the person preparing a review**, I want a readable, monochrome PDF of a compiled review report, so that another person can inspect the results without Studio.

## Requested scope

- A `compile-pdf.py` command produces a PDF with the Requirement-first presentation of REV-03, without buttons or interactive controls.
- Compile owns PDF reporting. Current report compilation lives in `review/compile.py`; the architecture target is a separate `compile/` subsystem. Establish the PDF component there without moving unrelated final-review behavior.
- The PDF presents the existing report objects. It does not introduce new Pack, Requirement, Claim, result, decision, or signature fields.

## Proposed acceptance behavior

The following behavior was authorized by the maintainer after the proposal.

### PDF-01 — Render a compiled report

Given a valid saved review-report JSON containing its run result, Requirements, Claims, and appendix,
when `compile-pdf.py --report <report.json> --out <report.pdf>` runs,
then it writes a PDF readable without Studio or a network connection,
and the source report retains its exact bytes,
and no Check, Discovery, signing, or model operation is invoked.

### PDF-02 — Explain the run before its details

Given a report containing passing, failing, or skipped Checks,
when its PDF is opened,
then the opening section identifies the checker build, recorded product commit and worktree state when present, loaded Pack versions, and Claim/Check outcome counts,
and explains that a passing Check is not a legal compliance judgment,
and a dirty run is not described as verification of the exact recorded commit.

### PDF-03 — Group by embedded Requirement

Given a compiled report,
when the PDF is rendered,
then Claims are grouped by their embedded Requirement's id,
and each group shows the source locator and passage, Claim rationale and evidence address, and every configured Check's index, id, arguments, status, and failure/skip detail when present,
and historical grouping and outcomes come from the embedded objects rather than today's mutable repository files,
and all groups are readable without expanding a control.

### PDF-04 — Separate results, decision, and signatures

Given a report with signature appendix entries and optional decision or report signature,
when the PDF is rendered,
then machine outcomes, the recorded reviewer decision, and signature information are clearly separated,
and missing decisions or signatures are not invented,
and embedded signature metadata is not labelled cryptographically verified merely because it is present,
and the PDF does not claim to carry the JSON report's digital signature over its own PDF bytes.

### PDF-05 — Print clearly

Given long passages, multi-path Check arguments, Swedish characters, and a report spanning several pages,
when the PDF is rendered and printed in black and white,
then it uses readable headings, typography, page numbers, and explicit PASS/FAIL/SKIPPED labels without relying on colour,
and text wraps without clipping or overlapping,
and it contains no buttons, forms, or expand/collapse controls.

### PDF-06 — Fail without destroying existing data

Given a missing or invalid report, an unwritable destination, or an existing output file,
when the command is run,
then it reports the relevant error and returns nonzero,
and leaves the input and any existing output unchanged.

## Implementation decisions

- Saved review-report JSON is the initial input. A command that compiles raw run results into JSON and PDF is a separate extension of TL-05.
- ReportLab renders locally with its bundled Vera fonts; pypdf is a development-only readback dependency. No custom PDF engine or cloud renderer.
- The PDF component belongs to `compile/`, with its own architecture contract. Existing JSON assembly stays in `review/compile.py`; this does not perform the full EP-02 migration.
- Present the five signature facts as recorded metadata and a version digest, with an explicit statement that verification was not performed. No trust-store CLI or implied verification.

## Validation

Acceptance tests exercise the real command with a deterministic compiled-report fixture and inspect PDF text, grouping, statuses, and file preservation. Manual visual acceptance inspects a multi-page PDF for monochrome readability, pagination, wrapping, and absence of controls. Existing compilation and final-review regressions must remain passing. No generated product report or confidential fixture is committed.
