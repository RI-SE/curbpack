# VER-02 — Bring the rest of the curbcheck catalogue

**Status:** The suite files, their shell procedures, and the manual procedures are copied under `tests/check/`. `make test-curbcheck` reports each catalogue row from those files. A row whose procedure calls `curbpack` is outside the pass. To be specified stays To be specified.

**Epic:** [EP-10 Verify curbcheck](../EPIC.md)

**Starts when:** VER-01 is accepted.

**As a tester**, I want the remaining Curbpack catalogue under `tests/check/`, on `make test-curbcheck`, so the procedures already written are in this repository with the status they have today.

## Read

- `/Users/DanielFl/Documents/aProjects/aslak/curbpack/testing/test_suites/`
- `/Users/DanielFl/Documents/aProjects/aslak/curbpack/docs/testing/procedures/`
- `tests/check/` as VER-01 left it
- `docs/testing/outside.md`

## Write only

- `tests/check/` for the remaining catalogue rows
- The `test-curbcheck` target, only to list the new rows
- A short index in `docs/testing/` that points at `tests/check/`

Do not edit the reference product, an R script, a PF script, `docs/reference/test-packs/`, or `docs/reference/packs2.md`. Do not add these rows to `make test`. Do not commit `tmp/`.

## The move

Copy each catalogue row from `curbpack/testing/test_suites/` into `tests/check/`. Keep its id and its status.

- An **Executable** row names the Studio observation: the curbcheck argv, the R-state, and the expected run-result status. The old `curbpack check` fields `outcome`, `readiness_score`, and `evaluated_rules` are not that observation.
- A row marked **To be specified** stays **To be specified**. The text comes with it. This story does not invent the missing steps.
- A human step stays manual. `make test-curbcheck` prints it and does not count it as a pass. That includes the reviewer rows, the claim-language reading, and the platform rows that a person still executes.
- A row whose Check command is not installed (`dep_ban`, `fresh`, `owned`, and the unimplemented Git checks) stays outside the pass. The detail is the one curbcheck already returns. The row is not deleted.

The seven carried checks stay the rows VER-01 already runs. This story does not give them a second runner.

## Accept when

- Every catalogue id in `curbpack/testing/test_suites/` is under `tests/check/` once.
- `make test-curbcheck` still prints `claims 7 exit 0` for the VER-01 run.
- Manual rows and **To be specified** rows are printed and are absent from the pass count.
- `make test` does not run `tests/check/`.
- No row expects `outcome`, `readiness_score`, or `evaluated_rules`.

## Stop if

An Executable row passes only by calling `curbpack check` or by editing an R or PF script. Leave the row manual or outside, and record the reason. Do not change the product script.

The only way to keep a row is to mark a non-passing Check as `pass`. Leave the row outside.
