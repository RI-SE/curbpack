# REV-09 — Remediation

**Status:** DONE, 2026-11-26. Evidence and completed plan: `impl/REV-09.md`.
**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md).

As the person doing the work after a signed review, I want to change the Check, re-check it, and seal that account, without changing the signed decisions.

The November 2026 split plan said a comment was a history entry. The code does not do that. A comment is the note on the item.

## Acceptance

### REM-01 — The signed review stays locked

Given a signed review,
when Remediation is started,
then the signed `decision`, `priority`, and `comment` stay as signed,
and on the remediation copy `decision` is the recommendation and may change.
The Check row says Start, then Continue, then Completed.

### REM-02 — A comment is the note

Given an open remediation row,
when Add comment is used,
then `comment` replaces the previous note, or clears it,
and that note is not a `remediation_history` entry.

### REM-03 — History records what was done

Given a re-check that changes the outcome,
when it is recorded,
then the history entry has `transition`, such as `must_fix -> pass`, and the recommendation follows the new outcome.
A changed Check configuration keeps the item, writes `action` `retarget` and `old_check_digest`, and updates `key.check_digest`.
Rebind writes `action` `rebind` when the Claim is signed.
Retire writes `action` `retire` and removes that Check from the live Claim immediately. When no Check remains, the Claim file is removed. Retiring the Claim retires every row of that Claim. The Check result does not become `pass`.

### REM-04 — A full run that fails outside the queue

Given Re-check,
when it runs every Check,
then the original deviations are updated and a new failure outside those deviations is not added to the queue.
That failure is Checks outside the original report.
OK records the event with `choice` `ok` and leaves the new failure out of the queue.
Rollback restores only the latest Studio change of the Claim and records `choice` `rolled_back`. A file changed outside Studio is left as it is. There is no Rollback when Studio has no change to restore.

### REM-05 — Sign Off seals the remedy

Given the open remediation,
when Sign Off is used,
then Studio writes `remedy-report_<stamp>.json` with the items, `remedy` `true`, the round notes when present, `reference`, `full_checks`, and `outside` when an outside Check was acknowledged.
The seal is read with `what` `remedy report`. It does not change the signed review decisions.
The Markdown and PDF written beside the JSON are not covered by the seal.
Revoke signature opens the remediation again and leaves the sealed file in place.

## Boundaries

The remedy report's fields are [Outputs](../../../../reference/outputs.md). This story does not redesign the management PDF.
