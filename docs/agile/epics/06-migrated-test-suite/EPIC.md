# EP-06 — Migrated verification suite

**Status:** Draft. Do not start until DOC-01, DOC-02, DOC-03, and PK2-01 are accepted.

**Goal:** The suite command in `docs/testing/README.md` exits 0 only when every case `plan/TST-01.md` marks carried has its expected exit status.

## Stories

| ID | User goal | Starts when |
| --- | --- | --- |
| [TST-01](stories/TST-01-migrate-testing-docs.md) | Migrate `curbpack/docs/testing` so the carried cases run on Studio | DOC-01, DOC-02, DOC-03, and PK2-01 are accepted |

Phase A is the plan. Phase B does not start until that plan names the maintainer and a date.

## Epic acceptance

- This epic's commits contain only `plan/TST-01.md` and paths under `docs/testing/`.
- `plan/TST-01.md` marks every source file under `curbpack/docs/testing/` as carried or outside. Carried plus outside equals the source-file count.
- The argv in `docs/testing/README.md` exits 0 only when the pass count equals the carried-case count and the fail count is 0.
- Cases the plan marks outside are listed by id in `docs/testing/outside.md`. That list is not a pass. Their disposition file is OUT-01, not this epic.
- `R1`–`R7` and `PF-01`–`PF-17` keep the ids and product effects in the Curbpack procedures. `R8`, `R9`, `PF-18`, and `PF-19` keep the ids in `ctam/docs/testing/procedures.md`. No state script in the reference product is edited.
- The runner is `python3 -m checks` with `--repo`, `--packs`, and `--out`. It reads `curbpack.json`. It does not read `.curbpack.json` or `CURBPACK_PACKS_DIR`.

## Out of scope

`cyberready-test-product`, `daniel/ny_sdd/`, `docs/reference/test-packs/`, `docs/reference/packs2.md`, and application code.
