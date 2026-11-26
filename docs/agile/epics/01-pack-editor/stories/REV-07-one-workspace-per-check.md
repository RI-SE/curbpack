# REV-07 — One workspace per Check

**Status:** DONE, 2026-11-26. Evidence and completed plan: `impl/REV-07.md`.
**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md).

As a reviewer, I want each Check to keep its own review file, and to be asked before an existing review is replaced, so two runs do not share decisions.

## Acceptance

### WORK-01 — One file per Check

Given two Studio Checks,
when each has review items,
then each directory under `results_dir` holds its own `review_items.json`,
and the two paths are different.
An older flat run still keeps `review_items.json` under `paths.temp_dir`, in a directory named from the source file. A Studio Check does not use that flat file.

### WORK-02 — Continue or start over

Given a Check whose `review_items.json` already exists,
when that Check is opened for review,
then the page asks whether to continue or start over.
Continue merges the new Checks with the existing items and keeps the existing item where the key matches.
Start over keeps only the new Checks.
Cancel writes nothing.

## Boundaries

Save and Sign are REV-08. This story only places the file and chooses which items stay.
