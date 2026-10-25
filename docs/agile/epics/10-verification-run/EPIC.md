# EP-10 — Verification run

**Status:** Draft. Do not start until TST-01 is accepted. Does not wait for REF-01. Does not edit `cyberready-test-product`. Does not edit `states/R1.sh` through `states/R7.sh`.

**Goal:** A Studio verification run clones the reference product, applies one existing R-state with the product's `setup.sh`, and runs `python3 -m checks` on that clone. The next case deletes the clone and clones it again.

## What the detective pass found

The Executable rows live in `/Users/DanielFl/Documents/aProjects/aslak/curbpack/testing/test_suites/`. There are 32 of them. Each one sources `tmp/verification-run.sh`, then mutates the clone, then runs `curbpack check`. None of them runs `python3 -m checks`.

`scripts/start-verification-run.sh` clones `git@github.com:RI-SE/cyberready-test-product.git` into `tmp/cyberready-test-product`. The pin in `tests/cyberready-test-product.pin` is `2b0c3f30bda411917ca0cd5b5f545e04de11cd25`, and that commit is `origin/main`. The local product checkout is five commits ahead of that pin and is not what a clone returns. `external_test/curbpack-studio/` is untracked there, so a clone does not contain it.

The pin already has `external_test/curbpack/setup.sh` and `states/R1.sh` through `states/R7.sh`. `setup.sh` allows `SUT=curbpack` or `SUT=ctam` and runs `external_test/$SUT/states/<ID>.sh`. It refuses a dirty tree and a HEAD that is not `REFERENCE_PRODUCT_COMMIT`. `--commit` records a local `test_*` branch and does not push.

The filled `tmp/verification-run.sh` exports `CURBPACK_PACKS_DIR` and requires a built `tmp/curbpack`. Those two behaviors belong to `curbpack check`. This epic does not copy them.

## Stories

| ID | User goal | Starts when |
| --- | --- | --- |
| [VER-01](stories/VER-01-verification-run.md) | Clone the reference product, apply R1, run the carried checks | TST-01 is accepted |

The 32 Executable rows are not this story. A later story moves one row, and names the Studio observation for it. This epic does not treat the old `curbpack check` JSON as that observation.

## Epic acceptance

- From the Studio root, one command clones the pinned reference product into `tmp/cyberready-test-product` and writes `tmp/verification-run.sh`. That filled file is not committed.
- Sourcing `tmp/verification-run.sh` deletes that directory and clones it again at the same commit. It prints `Verification run configuration: OK`.
- On that clone, `./external_test/curbpack/setup.sh R1 --commit` exits 0. The script file is unchanged.
- The same clone then has `curbpack.json` and the seven carried claim files. `python3 -m checks --repo <clone> --packs docs/reference/test-packs --out <out>` prints `claims 7 exit 0`.
- The run does not export `CURBPACK_PACKS_DIR`, does not run `curbpack check`, and does not build `tmp/curbpack`.
- A second source of `tmp/verification-run.sh` removes the previous clone before the next case.

## Out of scope

Rewriting the 32 Executable rows. Editing the reference product. Editing an R script or a PF script. Editing `docs/reference/test-packs/` or `docs/reference/packs2.md`. Application code, except a bug that stops the clone-and-R1 path of this epic.
