# REV-10 — The next review

**Status:** DONE, 2026-11-26. Evidence and completed plan: `impl/REV-10.md`.
**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md).

As a reviewer, I want the next Check to be a new review that can take in the signed remediation, so unchanged checked material keeps its decision and changed checked material does not.

## Acceptance

### NEXT-01 — A new Check is a new row

Given a completed remediation,
when Run Check is used,
then the new Check is a new row under Checks performed.
It does not replace the signed review or the remedy report.

### NEXT-02 — Take in the remedy

Given the new review is offered the remediation report,
when the checked material is unchanged,
then the signed `decision` is filled in, including a prepared `accepted`,
and `remediation_history` is not copied into that decision.
When the checked material changed, that decision is not reused. A pass on the changed material records the transition and suggests `pass`.
The history stays visible either way.
Keep the new decisions leaves the decisions the new run filled in, and stores the history on the items.

### NEXT-03 — Missing only when retired

Given a Check that the remedy report contains and the new run does not,
when the history has `action` `retire`,
then that Check is taken in as retired.
The same absence without `action` `retire` is not retired. A comment alone does not retire it.

## Boundaries

Sign on this new review is REV-08. The remedy seal itself is REV-09.
