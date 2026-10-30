# REV-05 — Management summary with technical appendices

**Status:** Authorized by Daniel, 2026-10-29. Resume from `plan/REV-05.md`. The renderer, its tests and the outputs note are already in the working tree and are not committed. Keep them and finish verification.
**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md).

As a management reader, I want the PDF to explain what needs attention in plain language, with technical details in appendix tables, so I can understand the recorded result before consulting engineering detail.

## Acceptance

### MGMT-01 — Plain-language opening

Given a saved review report,
when its PDF is rendered,
then the opening identifies the checker and a compact saved revision when recorded, and explains the scope, counts of evidence assertions and automated checks, and what needs human follow-up,
and avoids full hashes, raw JSON arguments, source URLs, certificate diagnostics and Git terminology in that opening,
and describes uncommitted changes in plain language when the recorded worktree is dirty,
and preserves the distinction between technical outcomes and a human/legal conclusion.

### MGMT-02 — Follow-up and recorded decision

Given failed or skipped results,
when the opening is rendered,
then it identifies the affected recorded assertions in understandable text and references the corresponding appendix section,
and recommends reviewing the evidence and check configuration, correcting the cause, and checking again,
and does not invent product risk, ownership, deadlines, compliance, or a reviewer decision.
A separate Review findings section presents each failed/skipped assertion with the checker's recorded reason and neutral human-review questions before the technical appendices.
Changes since the run, unresolved current evidence and independent signature verification are explicitly described as not assessed, rather than reported as zero or verified.
The appendix starts its detailed evidence section with a compact row per Claim and its Requirement, outcomes and detail reference.
Given all Checks passed or no Checks executed,
then the summary accurately distinguishes those cases.
Given a recorded reviewer decision and recorded signature gaps,
then the opening shows the decision and explains the gaps separately from automated outcomes, with details in the appendix.

### MGMT-03 — Technical appendix tables

Given the same report,
when the appendix is rendered,
then run metadata and loaded Pack versions/digests, embedded Requirements and source passages, embedded Claims and evidence addresses, indexed Check arguments/outcomes/details, recorded signature metadata and appendix reasons remain available,
and technical records are arranged in readable tables with repeated headers, wrapping, and page splitting,
and the source objects and historical grouping remain unchanged.

### MGMT-04 — Readable output and preserved inputs

Given the actual 13-Claim/19-Check example and a multi-page Unicode/long-text fixture,
when new PDFs are generated,
then the main report is readable in black and white without controls,
and technical content follows an explicit page break into labelled appendices,
and visual inspection confirms that tables, long text, headers and page footers do not overlap or clip.
Existing preservation and validation behavior from REV-04 continues to hold.

## Boundaries

English presentation remains consistent with the existing report. The executive summary uses deterministic wording and recorded assertions, not generated interpretations. A long assertion may be shortened for the follow-up table, with its complete text retained in the appendix. No new persistent fields, model calls, or trust verification is introduced. New PDFs use a new filename; previous PDFs and source JSON remain intact.

The user supplied a Copilot review-layout suggestion on 2026-10-29. It informed the summary/findings/appendix structure. Its proposed tick-box decisions and new live-comparison or verification counts are not introduced: the report decision remains free text and the export reads only recorded historical data.
