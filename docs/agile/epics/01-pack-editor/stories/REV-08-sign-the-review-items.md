# REV-08 — Sign the review and the items

**Status:** DONE, 2026-11-26. Evidence and completed plan: `impl/REV-08.md`.
**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md).

As a reviewer, I want Sign to lock the decisions for one Check and seal them, so reporting reads those decisions and a later Save cannot reopen them.

The field rules are [Outputs](../../../../reference/outputs.md). Retire is not a decision on this page.

## Acceptance

### SIGN-01 — The decisions the page offers

Given a deviation,
when it is judged,
then the decision is Not assessed, Accept, or Must be fixed.
A passing Check is Passed or Must be fixed. Accept is not offered for a passing Check.
The Check result stays `pass`, `fail`, or `skipped`.

### SIGN-02 — Save stays on the working file

Given an open review,
when Save is used,
then the decisions and the notes are written to that Check's `review_items.json`,
and no report is written and no signature changes,
and the Check row says Continue.
A review that already has `review_locked`, or a `signed` block on that file, is left unchanged.

### SIGN-03 — Sign seals the report and the items

Given a signer name,
when Sign is used,
then Studio writes `review-report_<stamp>.json` in the Check directory, seals `{ "items": [...] }` as `review-report_<stamp>.items.json`, stores that object's version digest as `items_digest`, sets `review_locked`, and returns to Check.
The Check row then says View.
`accepted` is stored on the report as `disposition` `accept`. `must_fix` is stored as `must_fix`. `pass` and `not_assessed` add no assessment. Accept on a failing Check needs a comment.
A `stale` or `missing` binding with `must_fix` or `accepted` becomes a binding assessment.
Reporting reads `decision` from the sealed items. A later edit of the working copy is not that decision.
Reading the items seal uses `what` `review items`. Reading the report seal uses `what` `review report`.

## Boundaries

Remediation does not edit the sealed decisions. An older report that already has `disposition` `retire` is still accepted by `validate_report`. This page does not post it.
