# REV-05 — Management summary with technical appendices

**Status:** DONE, 2026-11-26. Evidence and completed plan: `impl/REV-05.md`.
**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md).
**Related:** [REV-04](REV-04-compile-pdf.md).

As a management reader, I want the PDF of a saved review report to explain what needs attention in plain language, with technical details in appendix tables, so I can understand the recorded result before consulting engineering detail.

The renderer is `studio/compile/impl/pdf.py`. `compile-pdf.py` calls it through `compile/pdf.py`. It reads one saved review report and writes one new PDF. It does not read a remedy report, and it does not read `action` `retire` on a `review_item`.

## Acceptance

### MGMT-01 — Plain-language opening

Given a saved review report,
when its PDF is rendered,
then the opening is headed Management summary, names the checker and a compact saved revision when one is recorded, and states the counts of evidence assertions and automated checks,
and keeps the full commit, the word worktree, digests, raw check arguments, source URLs and certificate reasons out of that opening,
and says the checked files included uncommitted changes when the recorded worktree is dirty,
and states that the export prepares evidence for human review and is not a conformity assessment.

### MGMT-02 — Follow-up, findings and the recorded decision

Given failed or skipped Checks,
when the opening is rendered,
then it names how many automated checks need follow-up, lists the recorded assertions that need attention, and points at the appendix item,
and tells the reader to review the evidence and the check configuration, address the cause, and run the checks again,
and does not invent product risk, ownership, deadlines, compliance, or a reviewer decision.
A failed Check whose assessment `disposition` is `retire` is counted as retired, not as an outstanding correction. The recorded result stays in the report. A Check that was retired later by remediation `action` `retire` is not what this count reads.
Review findings follow the summary, before the appendices, in this order: outstanding deviations requiring correction, accepted deviations, retired checks, and passing checks. A finding shows the checker's recorded reason. A passing Check whose stored binding is `stale` or `missing` is still shown, and its Check status stays `pass`.
The findings state that changes since the run, unresolved current evidence, and independent signature verification are not assessed.
Given every Check passed, the summary says all recorded checks passed and that human review is still required.
Given no Checks executed, the summary says there is no successful check result to review.
Given a recorded reviewer decision, the opening shows that text. Given none, it says no reviewer decision was recorded. Signature gaps are counted separately from automated outcomes, with the reasons in Appendix C.

### MGMT-03 — Technical appendix tables

Given the same report,
when the appendix is rendered,
then it starts on a new page, headed Appendix A — Run and source records, and continues with Appendix B — Requirements, evidence and checks and Appendix C — Approval and signature records,
and those tables keep run metadata, loaded Pack versions and digests, embedded Requirements and source passages, embedded Claims and evidence, indexed Check arguments and outcomes, and the recorded signature reasons,
and a table repeats its header and can split a long row across pages,
and the source objects and their historical grouping are unchanged.

### MGMT-04 — Readable output and preserved inputs

Given a report with long Unicode text,
when a new PDF is generated,
then the text is present, every page is numbered, and the file has no annotation controls.
An existing PDF at the output path is left unchanged, and so is the source JSON. A missing report, a report that does not validate, or a missing output directory writes no PDF.

## Boundaries

English presentation. The summary uses the recorded report, not a generated interpretation. A long assertion may be shortened in the follow-up table; the appendix keeps the recorded text. No new persistent fields, model calls, or trust verification. The command is `python3 compile-pdf.py --report <report.json> --out <report.pdf>`.
