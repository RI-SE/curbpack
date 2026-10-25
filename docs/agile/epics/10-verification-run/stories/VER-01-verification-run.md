# VER-01 — Clone, mutate, then run the carried checks

**Epic:** [EP-10 Verification run](../EPIC.md)

**Starts when:** TST-01 is accepted. REF-01 is not a gate. A clone of `origin/main` does not contain `external_test/curbpack-studio/`, and the R1 script this story runs is already on the pin.

**As a tester**, I want one verification run to clone the reference product, apply R1 with the product's own `setup.sh`, and run the seven carried checks there, so the next case starts from a fresh clone instead of the checkout I have open.

## Read

- `/Users/DanielFl/Documents/aProjects/aslak/curbpack/scripts/start-verification-run.sh`
- `/Users/DanielFl/Documents/aProjects/aslak/curbpack/testing/verification_run_template.sh`
- `/Users/DanielFl/Documents/aProjects/aslak/curbpack/tests/cyberready-test-product.pin`
- `/Users/DanielFl/Documents/aProjects/aslak/curbpack/testing/test_suites/README.md` and `EV.md` through the EV-001 steps only
- `docs/testing/README.md` and `plan/TST-01.md` as TST-01 left them
- Read-only: `external_test/curbpack/setup.sh` and `states/R1.sh` at pin `2b0c3f30bda411917ca0cd5b5f545e04de11cd25`

## Write only

- `scripts/start-verification-run.sh`
- `testing/verification_run_template.sh`
- `tests/cyberready-test-product.pin`
- The preparation section of `docs/testing/README.md` and `docs/testing/procedures/README.md`

Do not edit the reference product. Do not edit `states/R1.sh` through `states/R7.sh`. Do not edit `docs/reference/test-packs/` or `docs/reference/packs2.md`. Do not commit `tmp/`. If OUT-01 has added its link line to `docs/testing/README.md`, leave that line.

## The run

1. `scripts/start-verification-run.sh` records the Studio commit, the pin commit, and one date. It clones `git@github.com:RI-SE/cyberready-test-product.git` into `tmp/cyberready-test-product` and checks out the pin. The default pin is `2b0c3f30bda411917ca0cd5b5f545e04de11cd25`. A commit origin does not have stops the run. The local product checkout is not the clone.
2. `testing/verification_run_template.sh` is the version-controlled text. The filled `tmp/verification-run.sh` is the run copy. Sourcing it from the Studio root checks that Studio HEAD is still the recorded commit, deletes `tmp/cyberready-test-product`, clones it again, and checks out the same pin. It does not export `CURBPACK_PACKS_DIR`. It does not put a `curbpack` binary on `PATH`.
3. On that clone, `./external_test/curbpack/setup.sh R1 --commit` applies R1. The case does not copy the body of `states/R1.sh` into the procedure.
4. The case then writes `curbpack.json` with packs `cra-baseline`, `house-policy`, and `medtech-iec62304`, and copies the seven carried claim files into the clone's `claims/`. Those files are the ones `plan/TST-01.md` marks carried. PF-01 for this runner is `--packs docs/reference/test-packs`. This story does not call `mutate_pack.sh`.
5. From the Studio root:

```sh
python3 -m checks --repo tmp/cyberready-test-product --packs docs/reference/test-packs --out tmp/cyberready-test-product/run-result.json
```

6. A second `source tmp/verification-run.sh` deletes that clone, including the local `test_*` branch `setup.sh` created, and clones again.

## Accept when

- The pin file records `2b0c3f30bda411917ca0cd5b5f545e04de11cd25` and the clone URL.
- Sourcing the filled file prints `Verification run configuration: OK` and the clone's HEAD is that pin.
- `setup.sh R1 --commit` exits 0 on that clone. `git diff` on `external_test/curbpack/states/R1.sh` inside the clone is empty.
- The checks command prints `claims 7 exit 0`. The pass count is 7 and the fail count is 0. Those seven ids are the carried ids in `plan/TST-01.md`, each still expected `pass`.
- The filled run file and the clone are absent from `git status` in the Studio repository.
- `docs/testing/` names this sequence. It does not tell the tester to export `CURBPACK_PACKS_DIR`, to run `curbpack check`, or to `git archive` the developer's product checkout.

## Definition of done

The checks command on the R1 clone is the evidence. The work log records the pin, the Studio commit, the date, the pass count, and the fail count. The Studio commit for this story contains only the four write paths. The reference-product repository has no commit from this story.

## Stop if

The pin is not on origin. Pushing the product is not part of this story.

R1 passes only after an edit to `states/R1.sh` or to another R or PF script. Leave the script. Stop.

A carried claim fails for the reason TST-01 already recorded (`curbcheck-dep-ban` missing, or a `contents` path absent). That claim stays outside. Do not add it to the seven.

An Executable row from `curbpack/testing/test_suites/` is copied in with its old JSON (`outcome`, `readiness_score`, `evaluated_rules`) as the expected result. Leave the row in Curbpack. This story does not move it.
