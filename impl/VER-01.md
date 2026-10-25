# VER-01 — Verify curbcheck on a fresh clone

## Summary

- **Story:** `docs/agile/epics/10-verification-run/stories/VER-01-verification-run.md`
- **Goal:** `make test-curbcheck` clones the pinned product, applies R1, and the seven carried checks pass.
- **Scope / exclusions:** No `CURBPACK_PACKS_DIR`, no `curbpack check`, no `tmp/curbpack`, no Studio application, no edit of the reference product or `states/R1.sh`.
- **Baseline:** `python3 -m unittest tests.test_curbcheck_catalogue -v` — 3 OK. `make test-curbcheck` — `claims 7 exit 0`.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | DONE |
| Approved by | Maintainer, 2026-10-25, ordered the verification chain finished the same day |
| Current task | Task 1 — clone, R1, and the seven checks |
| Last completed task | Task 1 — clone, R1, and the seven checks |
| Last verified tests | `make test-curbcheck` printed `claims 7 exit 0` and manual CR-01 through CR-11. `python3 -m unittest tests.test_curbcheck_catalogue -v` printed 3 OK. |
| Last checkpoint commit | `890628ac3f577aea34583f2749194c44f7c7b474` |
| Requirements | VER-R01 and VER-R02, approved in this plan |
| Packs v2 | Claim files stay in `docs/reference/test-packs/claims/`. No new Packs v2 field. |
| Blockers | None |
| Exact next action | No further implementation step. VER-02 keeps the remaining catalogue rows. |

## Requirements and acceptance mapping

| Requirement | Acceptance | Evidence |
| --- | --- | --- |
| VER-R01 | `make test-curbcheck` clones pin `2b0c3f30bda411917ca0cd5b5f545e04de11cd25`, applies R1, and prints `claims 7 exit 0` | 2026-10-25 run, exit 0 |
| VER-R02 | CR-01 through CR-11 are printed and are not in the pass count | The same run printed `manual CR-01` through `manual CR-11` after the seven passes |

## Tasks

### Task 1 — clone, R1, and the seven checks

- [x] Add the start script, the template without `CURBPACK_PACKS_DIR` and without `tmp/curbpack`, the pin, and `make test-curbcheck`.
- [x] Copy the seven claim files into the clone and run `python3 -m checks`.
- [x] Print the eleven manual rows without counting them.

## Work log

- **2026-10-25 — Task 1.** `make test-curbcheck` cloned `git@github.com:RI-SE/cyberready-test-product.git`, printed `Verification run configuration: OK`, applied R1, and printed `claims 7 exit 0` with seven `pass` claim lines and no `fail` line. It then printed `manual CR-01` through `manual CR-11`. `git diff` on `external_test/curbpack/states/R1.sh` inside the clone was empty. Commit `890628ac3f577aea34583f2749194c44f7c7b474`.
