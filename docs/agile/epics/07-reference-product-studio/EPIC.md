# EP-07 — Reference product, Studio external test

**Status:** Draft. Do not start until DOC-01, DOC-02, PK2-01, and TST-01 are accepted. EP-08 does not block this epic, and this epic does not edit `docs/testing/`.

**Goal:** `external_test/curbpack-studio` in Glucose Log describes Studio and holds the PK2-01 Pack bytes. The rest of that repository stays untouched. `states/R1.sh` through `states/R7.sh` are byte-identical to the versions present when this epic starts.

## Stories

| ID | User goal | Starts when |
| --- | --- | --- |
| [REF-01](stories/REF-01-external-test-studio.md) | Copy the Packs v2 fixture in and describe `python3 -m checks` | DOC-01, DOC-02, PK2-01, and TST-01 are accepted |

## Epic acceptance

- Text under `external_test/curbpack-studio` names `python3 -m checks`, `curbpack.json`, and `--packs`. It does not name `curbpack check`, `CURBPACK_PACKS_DIR`, or `.curbpack.json` as the way to run this SUT.
- `diff -rq` between each of `packs/cra-baseline`, `packs/house-policy`, and `packs/medtech-iec62304` and the same directory under `docs/reference/test-packs/` in the Studio repo prints nothing. Claim files live in `claims/`, not inside `packs/<id>/`.
- The diff of `states/R1.sh` through `states/R7.sh` is empty.
- The diff of this epic in the Curbpack Studio repository is empty.
- The diff of this epic in `cyberready-test-product` is empty outside `external_test/curbpack-studio/`.

## Out of scope

The getting-started `walkthrough` Pack. Editing `external_test/curbpack` or `external_test/ctam`. Changing a state script to obtain a pass. Changing Studio code.
