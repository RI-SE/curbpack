# REV-06 — Item, provenance and reuse

**Status:** DONE, 2026-11-26. Evidence and completed plan: `impl/REV-06.md`.
**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md).

As a reviewer, I want one decision per Check, tied to the underlag that was checked, so a later review can reuse that decision only when the underlag is the same.

`review_item` is defined in [Studio-internal](../../../../reference/studio-internal.md). The November 2026 split plan named this story. The behavior below is what the code does.

## Acceptance

### ITEM-01 — One item per Check

Given a Check run,
when review items are created,
then each item has `key.claim_id` and `key.check_digest`, and `check_digest` is the SHA-256 of the canonical `{ "check", "args" }`,
and the binding is the implicit Check `requirement_binding` with `args` `{}`,
and `decision` is `pass`, `accepted`, `not_assessed`, or `must_fix`.

### ITEM-02 — Provenance from the run

Given a dirty Studio Check,
when the run result is written,
then `size` and `mtime` are not fields of the run result,
and the same operation writes `run-result_<stamp>.files.json` once, with each Check's path, size, and mtime,
and a later edit of the worktree does not change that file.
Opening the review copies those values onto `provenance.files`.
`provenance` also keeps `requirement_digest`, `git_commit`, and `dirty_git` from the run. A key the run does not have is omitted.

### ITEM-03 — Reuse fills the decision only

Given a stored decision and a new item with the same `key` and the same `requirement_digest`,
when the underlag is unchanged,
then the new item receives that `decision` and does not receive `remediation_history`.
Clean commits compare the Check's file content. A dirty side compares `path`, `size`, and `mtime`.
When a value the comparison needs is missing, the decision is not reused. The stored decision and history remain.

## Boundaries

No new persistent field. History is recorded by remediation, not by this reuse.
