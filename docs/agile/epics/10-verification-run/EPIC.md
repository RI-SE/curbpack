# EP-10 — Verify curbcheck

**Status:** The seven carried checks run. The Curbpack suite procedures and the manual procedures are copied under `tests/check/`. `make test-curbcheck` prints `claims 7 exit 0` on pin `2b0c3f30bda411917ca0cd5b5f545e04de11cd25`, prints CR-01 through CR-11, and reports every other catalogue row from those files. A copied procedure that calls `curbpack` is outside the pass. Does not wait for REF-01. Does not edit `cyberready-test-product` or `states/R1.sh` through `states/R7.sh`.

**Goal:** `make test-curbcheck` verifies curbcheck. The run lives under `tests/check/`. It clones the reference product, applies one existing R-state with the product's `setup.sh`, and runs curbcheck on that clone. The Studio application is not part of the run. `make test` stays the Studio suite.

curbcheck and Studio stay in this repository. `checks/` may import `common/`. It does not import the application or another tool's UI.

## What the detective pass found

The Executable rows live in `/Users/DanielFl/Documents/aProjects/aslak/curbpack/testing/test_suites/`. There are 32 of them. Each one sources `tmp/verification-run.sh`, then mutates the clone, then runs `curbpack check`. None of them runs curbcheck. Other catalogue rows are **To be specified** or a human step. Those texts stay. A row that is not executable is not turned into a pass.

`scripts/start-verification-run.sh` clones `git@github.com:RI-SE/cyberready-test-product.git` into `tmp/cyberready-test-product`. The pin in `tests/cyberready-test-product.pin` is `2b0c3f30bda411917ca0cd5b5f545e04de11cd25`, and that commit is `origin/main`. The local product checkout is five commits ahead of that pin and is not what a clone returns. `external_test/curbpack-studio/` is untracked there, so a clone does not contain it.

The pin already has `external_test/curbpack/setup.sh` and `states/R1.sh` through `states/R7.sh`. `setup.sh` allows `SUT=curbpack` or `SUT=ctam` and runs `external_test/$SUT/states/<ID>.sh`. It refuses a dirty tree and a HEAD that is not `REFERENCE_PRODUCT_COMMIT`. `--commit` records a local `test_*` branch and does not push.

The filled `tmp/verification-run.sh` in Curbpack exports `CURBPACK_PACKS_DIR` and requires a built `tmp/curbpack`. Those two behaviors belong to `curbpack check`. This epic does not copy them. The stimulus here is `python3 -m checks` with `--repo`, `--packs`, and `--out`. The built `curbcheck-<host>` file takes the same arguments when it is present. The make target does not require that file.

## Stories

| ID | User goal | Starts when |
| --- | --- | --- |
| [VER-01](stories/VER-01-verification-run.md) | `make test-curbcheck` runs the seven carried checks, and the manual rows for that same run | TST-01 is accepted |
| [VER-02](stories/VER-02-remaining-check-catalogue.md) | The remaining Curbpack catalogue rows live under `tests/check/` with the status they already have | VER-01 is accepted |

VER-01 does not copy the 32 Executable rows. VER-02 copies the catalogue, including those rows and the human rows. Neither story treats the old `curbpack check` JSON as the observation.

## Epic acceptance

- From the Studio root, `make test-curbcheck` clones the pinned reference product into `tmp/cyberready-test-product` and writes `tmp/verification-run.sh`. That filled file is not committed.
- Sourcing `tmp/verification-run.sh` deletes that directory and clones it again at the same commit. It prints `Verification run configuration: OK`.
- On that clone, `./external_test/curbpack/setup.sh R1 --commit` exits 0. The script file is unchanged.
- The same clone then has `curbpack.json` and the seven carried claim files. The checks command prints `claims 7 exit 0`.
- The manual rows that belong to that run are listed by `make test-curbcheck` and are not counted as passes.
- The run does not export `CURBPACK_PACKS_DIR`, does not run `curbpack check`, does not build `tmp/curbpack`, and does not start the Studio application.
- A second source of `tmp/verification-run.sh` removes the previous clone before the next case.
- After VER-02, every catalogue row from `curbpack/testing/test_suites/` is present under `tests/check/` with its Curbpack status. A **To be specified** row and a human step stay that way.

## Out of scope

Editing the reference product. Editing an R script or a PF script. Editing `docs/reference/test-packs/` or `docs/reference/packs2.md`. The Studio suite `make test`. A separate curbcheck repository. Application code, except a bug that stops the clone-and-R1 path of this epic.
