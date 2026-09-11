# Controlled test prerequisites

A test case is Executable only when its prerequisites can be prepared
repeatably and the case states an exact stimulus and expected response.
The three prerequisite namespaces describe separate dimensions of the same
test input:

- `R-*` — controlled target-repository content state;
- `PF-*` — pack selection or deliberate pack mutation; and
- `EC-*` — execution configuration.

An ID in this registry does not by itself mean that repeatable preparation or
an executable test case exists. Each Executable case names the IDs it uses and
gives the exact preparation steps. If a dimension does not apply, the case
says so instead of inventing an ID.

Preparation status uses ordinary terms:

- **SCRIPTED** — an existing script or exact command prepares the condition;
- **MANUAL BUT REPEATABLE** — exact manual steps exist; and
- **NOT YET SPECIFIED** — no agreed reproducible preparation procedure exists.

## Prepare a verification run

Do this once before preparing any case prerequisites.

`docs/testing/verification_run_template.sh` is version-controlled.
`make start-verification-run` (`scripts/start-verification-run.sh`) prompts
for the run values (empty keeps the default). If `tmp/` already exists it
asks to delete that directory completely and stops if not. It never
touches `/tmp` or a sibling product checkout. If `tmp/` is missing it
creates it, clones the reference product, checks out the selected
revisions, runs `make build`, and fills `tmp/verification-run.sh`. That
copy is run-specific; do not check it in.

Defaults: this Curbpack `HEAD`, `HEAD` of an existing
`tmp/cyberready-test-product` (or `tests/cyberready-test-product.pin` if
the clone is missing), and today.

If Curbpack has local changes it stops and suggests `git stash`. If the
product commit is not in the clone after fetch, it stops: origin does not
see unpushed commits from another checkout (push the product, then retry).

The five values in that file are established once per test run and must remain
unchanged for that test run. Later repository-state setup and test cases may
rely on these environment variables being available.

1. From the Curbpack repository root:

   ```sh
   make start-verification-run
   ```

   Record a release tag as well if a release is under test.
2. Source the filled file from the Curbpack root (Make cannot do this;
   PATH would die with the recipe subshell):

   ```sh
   source tmp/verification-run.sh
   ```

   Continue only if it reports `Verification run configuration: OK`. It
   prepends `$CURBPACK_ROOT/tmp` to `PATH` so `curbpack` is `tmp/curbpack`.
   It sets `CURBPACK_PACKS_DIR` to
   `$REFERENCE_PRODUCT_ROOT/external_test/curbpack/packs` (PF-01).
   It also restores the disposable reference-product checkout to
   `$REFERENCE_PRODUCT_COMMIT` as described in
   [Start of every independent case](#start-of-every-independent-case).

Record the procedure revision: the Curbpack commit containing
`docs/testing/strategy.md`, this procedures directory, and the selected
suite file.

With those values frozen, prepare the selected case’s R/PF/EC prerequisites,
execute its stated stimulus, and record the observed result and evidence.

## Start of every independent case

Each Executable case is independent of the previous case. The per-case
sequence is:

```text
source verification-run environment
    -> frozen product baseline restored

prepare R-state
    -> requested controlled repository-content state established

verify/apply EC
    -> execution preconditions established

execute test
```

The destructive baseline restore belongs to the sourced verification-run
environment, not to `setup.sh`.

At the start of every case, Curbpack `HEAD` must still equal
`CURBPACK_COMMIT`, and `command -v curbpack` must still be
`$CURBPACK_ROOT/tmp/curbpack` built from that commit. If the binary is
missing, `make build`. Start each case from the Curbpack repository root:

```sh
source tmp/verification-run.sh
```

Continue only if it reports `Verification run configuration: OK`. Sourcing:

- verifies that Curbpack is still at `CURBPACK_COMMIT`;
- restores the disposable reference-product checkout to exactly
  `REFERENCE_PRODUCT_COMMIT`;
- hard-resets and cleans that disposable product checkout;
- leaves local `test_*` branch refs in the Git database; and
- does not fetch, pull, or clone.

It prepends `$CURBPACK_ROOT/tmp` to `PATH` if needed.

A previous `--commit` case can leave a local `test_*` branch. That is
expected. The next source restores the working tree to the frozen baseline
and leaves those branch refs in place.

Then prepare the case’s named R-state. For R1–R3,
`./external_test/curbpack/setup.sh <R-id> [--commit]` assumes the reference
product is already at the clean frozen baseline and applies that R-state
only. `setup.sh` does not restore the baseline. Do not run product
`reset.sh` between normal test cases. For R4 or R5, run
`"$REFERENCE_PRODUCT_ROOT/external_test/curbpack/states/R4.sh"` or
`"$REFERENCE_PRODUCT_ROOT/external_test/curbpack/states/R5.sh"`.

Do not assume the previous case’s working directory or product tree is
still valid.

## Repository content states

The detailed state definitions and commands are in
[0. Controlled repository content setup](0_controlled_repo_setup.md).

R is a controlled target-repository content state. It is not defined by
which script or repository happens to prepare it. Do not treat R as
meaning “reference-product state”.

R1–R3 target the disposable frozen reference-product checkout. They are
prepared in that product under `external_test/curbpack/`. R4 and R5
target disposable repositories under Curbpack `tmp/` and are prepared by
the same product directory: `states/R4.sh` and `states/R5.sh`. Those
scripts read Curbpack testdata.

| ID | Condition | Preparation status | Implementation |
|---|---|---|---|
| R1 | Starting Glucose Log product content, including `SECURITY.md` and the heading `## Classification Rationale` in `docs/medtech/software_safety_class.md` | SCRIPTED | `external_test/curbpack/setup.sh R1`; `states/R1.sh` |
| R2 | R1 with `SECURITY.md` removed | SCRIPTED | `external_test/curbpack/setup.sh R2`; `states/R2.sh` |
| R3 | R1 with the heading `## Classification Rationale` removed from `docs/medtech/software_safety_class.md` | SCRIPTED | `external_test/curbpack/setup.sh R3`; `states/R3.sh` |
| R4 | demo-app content with token-only honesty-eval `SECURITY.md` and `package.json` identifying `acme-widget` | SCRIPTED | `external_test/curbpack/states/R4.sh` |
| R5 | demo-app content with thin rule-satisfying honesty-eval `SECURITY.md` and original demo-app `package.json` | SCRIPTED | `external_test/curbpack/states/R5.sh` |

After the sourced environment has restored the frozen baseline,
`setup.sh R1` applies R1 to that checkout. `states/R1.sh` prints the R1
description from this procedures set, then verifies the required files,
heading, and `package.json` conditions.

`--commit` changes Git recording, not repository content. For example,
`setup.sh R2` and `setup.sh R2 --commit` both prepare R2. `states/R4.sh`
and `states/R5.sh` establish content only; they may delete and recreate
only their own target directory. EC-01 is separate and is stated by the
case.

## Pack inputs

Details are in [1. Pack inputs](1_pack_template_instantiation.md).

| ID | Condition | Preparation status | Implementation |
|---|---|---|---|
| PF-01 | Reference-product pack set (`house-policy`, `cra-baseline`, `medtech-iec62304`) | SCRIPTED | Set `CURBPACK_PACKS_DIR` to `<reference-product-root>/external_test/curbpack/packs` |
| PF-02 | A second representative instantiated product pack | NOT YET SPECIFIED | No second instantiated product or pack-template preparation mechanism exists |
| PF-03 | Deliberately invalid or modified pack input selected by a named case | SCRIPTED where a named fixture exists; otherwise NOT YET SPECIFIED | Existing fixtures: `<curbpack>/testdata/adversarial/packs/`; a case must name the exact fixture or mutation |

## Execution configurations

These conditions do not redefine repository content or pack input.

| ID | Condition | Preparation status | Preparation / implementation |
|---|---|---|---|
| EC-01 | Recorded commit / clean working tree | SCRIPTED | For R1–R3: `setup.sh <R-id> --commit`. For R4/R5: the case’s explicit `git init`, `git add -A`, and `git commit`. Verify `git status --porcelain` is empty |
| EC-02 | Dirty working tree | MANUAL BUT REPEATABLE | Prepare the named R-state, apply the case’s exact uncommitted edit, and verify `git status --porcelain` is non-empty |
| EC-03 | Detached HEAD | MANUAL BUT REPEATABLE | Prepare EC-01, then run `git checkout --detach HEAD` |
| EC-04 | Shallow clone | NOT YET SPECIFIED | The ID exists, but no complete case-specific preparation procedure is agreed |
| EC-05 | Sparse checkout / linked working tree / submodule | NOT YET SPECIFIED | The ID exists, but no complete case-specific preparation procedure is agreed |
| EC-06 | Offline | NOT YET SPECIFIED | The ID exists, but an exact platform-specific isolation and observation procedure is not yet defined |
| EC-07 | Locale / timezone variation | NOT YET SPECIFIED | The ID exists, but the locale and timezone matrix and commands are not yet defined |
| EC-08 | Concurrent local execution | NOT YET SPECIFIED | The ID exists, but no synchronization mechanism currently proves overlapping execution against a named shared output/cache location |
| EC-09 | Output failure injection | NOT YET SPECIFIED | The ID exists, but unwritable output, storage exhaustion, and controlled termination do not yet have reliable preparation procedures |
| EC-10 | Platform execution | NOT YET SPECIFIED | The ID exists, but per-platform installation and execution procedures are not yet defined |

## Names and directories

| Name | Meaning |
|---|---|
| **Curbpack** | This repository and the tool under test. |
| **Reference-product preparation directory** | `<reference-product-root>/external_test/curbpack/`; run `setup.sh` here. |
| **Throwaway repo** | A temporary Git repository created exactly as a case specifies. |
| **Curbpack test data** | Existing fixtures under `<curbpack>/testdata/`. |

## Execute and record a case

1. Complete [Prepare a verification run](#prepare-a-verification-run) and copy
   the [test record](../generated_test_record_template.md) outside this
   repository.
2. Open the selected [suite](../test_suites/README.md). Do not execute a row
   marked To be specified.
3. Do [Start of every independent case](#start-of-every-independent-case),
   then prepare the case’s stated `R-*`, `PF-*`, and `EC-*` prerequisites.
4. Execute the exact stimulus and compare the observed response with the
   declared response.
5. Keep raw output and record the disposition and evidence. Do not repair
   output files manually.
6. Leave the checkout as directed by TEARDOWN so failed state remains
   inspectable.

Keep completed records outside this repository. A corrected Curbpack version
or changed test basis starts a new frozen baseline.

Independent source and release review uses
[2. Code and release review](2_code_review_procedures.md).
