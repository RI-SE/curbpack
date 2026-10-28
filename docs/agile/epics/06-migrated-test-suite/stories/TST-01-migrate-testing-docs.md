# TST-01 — Migrate the suite, then run the carried cases

**Epic:** [EP-06 Migrated verification suite](../EPIC.md)

**Starts when:** DOC-01, DOC-02, DOC-03, and PK2-01 are accepted. Do not write the plan before that. The ids DOC-03 kept or moved to `docs/baseline-delta.md` are the ids this suite cites.

**As a tester**, I want the carried cases in `docs/testing/` to run through `python3 -m checks`.

## Read

- `docs/testing/`
- `../ctam/docs/testing/procedures.md` for `R8`, `R9`, `PF-18`, and `PF-19` only
- `daniel/ny_sdd/docs/REQUIREMENTS.md` and `daniel/ny_sdd/docs/baseline-delta.md`
- `docs/reference/test-packs/`
- Read-only: `../cyberready-test-product/external_test/curbpack-studio/states/` and `external_test/ctam/`

## Write only

`plan/TST-01.md` and files under `docs/testing/`. Do not edit application code, `docs/reference/packs2.md`, `docs/reference/test-packs/`, `daniel/ny_sdd/`, or the reference product.

## Phase A

Write `plan/TST-01.md` from `plan/TEMPLATE.md`. Mark every source file under `docs/testing/` as carried or outside. Rewritten text is carried. Record the source-file count, the carried count, and the outside count. Carried plus outside equals the source-file count. Mark `R8`, `R9`, `PF-18`, and `PF-19` carried or outside. Phase B starts only after a dated line in that plan names the maintainer and the plan revision.

## Phase B

- `docs/testing/README.md` states the suite argv: `python3 -m checks` with `--repo`, `--packs docs/reference/test-packs`, and `--out`.
- Procedures that use `R1`–`R7` or `PF-01`–`PF-17` still use those ids. They do not replace a state script.
- For `R8`, `R9`, `PF-18`, and `PF-19`: carried means the suite runs that id and the work log has its exit status. Outside means the id is in `docs/testing/outside.md`. A citation of the CTAM file with no exit status and no outside-list row fails the story.
- For each Claim file under `docs/reference/test-packs/claims/`, the procedure that names that Claim id uses the same `checks[].check` and `checks[].args` as that file.
- `docs/testing/outside.md` has one `id` column. It lists every `MUST-*` from DOC-02 that no carried case names, and `R8`, `R9`, `PF-18`, `PF-19` when those were not carried. An id in that file is not a pass.
- Each carried case's expected exit status is written next to its id in the procedure.

## Definition of done

The work log in `plan/TST-01.md` records the argv, the date, the pass count, the fail count, and the outside ids. Exit 0 is recorded only when the pass count equals the carried-case count and the fail count is 0. After phase B, the plan's carried and outside file marks still sum to the source-file count. Commits contain only `plan/TST-01.md` and paths under `docs/testing/`.

## Stop if

A carried case passes only after an edit to an `R*` or `PF*` script. Mark that case outside in `plan/TST-01.md` and in `docs/testing/outside.md`. Leave the script unchanged. REF-01 does not receive that edit.

A case needs a new Packs v2 field. Mark it outside. Do not add the field.
