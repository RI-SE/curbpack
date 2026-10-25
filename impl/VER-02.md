# VER-02 — Bring the rest of the curbcheck catalogue

## Summary

- **Story:** `docs/agile/epics/10-verification-run/stories/VER-02-remaining-check-catalogue.md`
- **Goal:** Every Curbpack suite id is one row under `tests/check/`, with its status kept.
- **Scope / exclusions:** No second runner for the seven. No row passes by calling `curbpack check`. No edit of an R or PF script.
- **Baseline:** `python3 -m unittest tests.test_curbcheck_catalogue -v` — 3 OK.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | DONE |
| Approved by | Maintainer, 2026-10-25, ordered the verification chain finished the same day |
| Current task | Task 1 — list the remaining catalogue rows |
| Last completed task | Task 1 — list the remaining catalogue rows |
| Last verified tests | `python3 -m unittest tests.test_curbcheck_catalogue -v` printed 3 OK. `make test-curbcheck` still printed `claims 7 exit 0`. |
| Last checkpoint commit | `890628ac3f577aea34583f2749194c44f7c7b474` |
| Requirements | VER-R03, approved in this plan |
| Packs v2 | No new Packs v2 field. `outcome`, `readiness_score`, and `evaluated_rules` are not the observation. |
| Blockers | None |
| Exact next action | No further implementation step. |

## Requirements and acceptance mapping

| Requirement | Acceptance | Evidence |
| --- | --- | --- |
| VER-R03 | Every catalogue id from the Curbpack suites is present once. Executable rows that only pass through `curbpack check` stay outside. Manual and unspecified rows are not a pass. | `tests/check/catalogue.md` and `tests/test_curbcheck_catalogue.py`, 3 OK |

## Tasks

### Task 1 — list the remaining catalogue rows

- [x] Copy each suite id once into `tests/check/catalogue.md` with its Curbpack status.
- [x] Leave `curbpack check` rows outside the pass.
- [x] Point `docs/testing/README.md` at that catalogue.

## Work log

- **2026-10-25 — Task 1.** `python3 -m unittest tests.test_curbcheck_catalogue -v` printed 3 OK. `make test-curbcheck` printed `claims 7 exit 0`, then the copied suites: PASS 1, FAIL 0, MANUAL 5, TBD 34, BLOCKED 2, OUTSIDE 25, REF 1, CATALOGUE 68, DISPLAYED 68. The procedure text is in `tests/check/suites/` and `tests/check/docs/procedures/`. A row that calls `curbpack` is outside and is not a pass. Commit `890628ac3f577aea34583f2749194c44f7c7b474` held the first id list. The procedures followed in the next commit.
