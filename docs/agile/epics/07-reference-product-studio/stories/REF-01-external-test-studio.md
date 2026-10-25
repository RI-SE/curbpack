# REF-01 — Install the Studio fixture in the reference product

**Epic:** [EP-07 Reference product, Studio external test](../EPIC.md)

**Starts when:** DOC-01, DOC-02, PK2-01, and TST-01 are accepted. A suite that merely runs is not the gate. Do not edit the reference product before those four are accepted. Do not edit the Curbpack Studio repository in this story. The fixture path is already in the TST-01 suite text.

**As a tester**, I want `external_test/curbpack-studio` to hold the PK2-01 Packs and to tell me to run `python3 -m checks`, so the carried suite can be repeated from that tree.

## Read

- `/Users/DanielFl/Documents/aProjects/aslak/cyberready-test-product/external_test/curbpack-studio`
- Read-only: `external_test/curbpack` and `external_test/ctam` in that repository
- `docs/reference/test-packs/` in the Studio repository
- `docs/testing/` and `plan/TST-01.md` as TST-01 left them

## Write only

`/Users/DanielFl/Documents/aProjects/aslak/cyberready-test-product/external_test/curbpack-studio/`

## Accept when

- `README.md` and `states.md` name `python3 -m checks`, `curbpack.json`, and `--packs`. They do not tell the tester to export `CURBPACK_PACKS_DIR`, to run `curbpack check`, or to select this SUT with `.curbpack.json`.
- `diff -rq packs/cra-baseline <studio>/docs/reference/test-packs/cra-baseline` prints nothing, and the same for `house-policy` and `medtech-iec62304`. `packs/SOURCE.txt` contains the same Curbpack commit string as `docs/reference/test-packs/SOURCE.txt`.
- Claim files from `docs/reference/test-packs/claims/` are copied to `external_test/curbpack-studio/claims/`. They are not placed inside `packs/<id>/`.
- The diff of `states/R1.sh` through `states/R7.sh` is empty. `setup.sh` still runs `states/<ID>.sh`. `mutate_pack.sh` still selects a `PF-*` id and does not commit.
- `external_test/curbpack-studio/RUN.txt` lists the suite argv from `docs/testing/README.md`, every carried case id from `plan/TST-01.md`, its `R*` id, its `PF*` id when the case uses one, the expected exit status, and the observed exit status. The carried-case count in `RUN.txt` equals the carried-case count in `plan/TST-01.md`. Observed status equals expected status for every carried id, including carried ids whose expected status is non-zero.

## Definition of done

`RUN.txt` satisfies the count and the status equality. `git diff` in `cyberready-test-product` shows changes only under `external_test/curbpack-studio/`. `git diff` in the Curbpack Studio repository for this story is empty.

## Stop if

Matching Studio would require an edit outside `external_test/curbpack-studio`, or an edit to `states/R1.sh`–`states/R7.sh`, or an edit to `docs/reference/test-packs/`. Leave those bytes unchanged. Write the two evidence paths and the reason into `RUN.txt` and stop the story.
