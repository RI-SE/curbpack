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
- **MANUAL BUT REPEATABLE** — exact manual steps exist;
- **BLOCKED** — a named script or case exists, but it does not yet follow
  the preparation model in this file; and
- **NOT YET SPECIFIED** — no agreed reproducible preparation procedure exists.

The mechanical sequence is:

1. Start a verification run once.
2. Start each independent testcase by sourcing `tmp/verification-run.sh`.
3. Prepare the named R-state through `setup.sh`.
4. Select the named pack input through `mutate_pack.sh` when the case does
   not use the already-present PF-01 set.
5. Apply any additional EC condition the case names.
6. Execute the testcase and record the result. Leave the repository and
   evidence for inspection.

The next testcase starts again at step 2. That source deletes and recreates
the disposable reference-product checkout.

## Prepare a verification run

Do this once before preparing any case prerequisites.

A verification run first selects and records one Curbpack commit, one
reference-product commit, one `AS_OF_DATE`, and the applicable test-method
revision. Those values stay frozen for the whole run. A later testcase does
not select a different reference-product revision.

`testing/verification_run_template.sh` is version-controlled.
`make start-verification-run` (`scripts/start-verification-run.sh`) prompts
for the run values (empty keeps the default). If `tmp/` already exists it
asks to delete that directory completely and stops if not. It never
touches `/tmp` or a sibling product checkout. If `tmp/` is missing it
creates it, clones the reference product, checks out the selected
revisions, runs `make build`, and fills `tmp/verification-run.sh`. That
copy is run-specific; do not check it in.

Defaults: this Curbpack `HEAD`, the reference-product revision defined in
`tests/cyberready-test-product.pin`, and today.

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

   Continue only if it reports `Verification run configuration: OK`.
   Sourcing that file is described in
   [Start of every independent case](#start-of-every-independent-case).
   It prepends `$CURBPACK_ROOT/tmp` to `PATH` so `curbpack` is
   `tmp/curbpack`. It sets `CURBPACK_PACKS_DIR` to
   `$REFERENCE_PRODUCT_ROOT/external_test/curbpack/packs` (PF-01).

Record the procedure revision: the Curbpack commit containing
`docs2/testing/strategy.md`, this procedures directory, and the selected
suite file.

With those values frozen, prepare the selected case’s R/PF/EC prerequisites,
execute its stated stimulus, and record the observed result and evidence.

## Start of every independent case

Each Executable case is independent of the previous case. Start every
independent testcase from the Curbpack repository root:

```sh
source tmp/verification-run.sh
```

Continue only if it reports `Verification run configuration: OK`. Sourcing
that file:

1. verifies the frozen Curbpack commit and binary;
2. obtains the origin URL from the existing disposable reference-product
   clone;
3. deletes `"$CURBPACK_ROOT/tmp/cyberready-test-product"` completely;
4. clones the reference product again into that same path;
5. checks out exactly `"$REFERENCE_PRODUCT_COMMIT"`; and
6. verifies that checkout and exposes the frozen run variables.

It does not select a new reference-product revision for the testcase. It
does not preserve local branches or other state from the previous disposable
clone. The revision was already selected for the verification run.

At the start of every case, Curbpack `HEAD` must still equal
`CURBPACK_COMMIT`, and `command -v curbpack` must still be
`$CURBPACK_ROOT/tmp/curbpack` built from that commit. If the binary is
missing, `make build` and source the file again.

The per-case sequence is then:

```text
source tmp/verification-run.sh
    -> frozen Curbpack commit and binary verified
    -> disposable reference product deleted and cloned again
    -> exactly $REFERENCE_PRODUCT_COMMIT checked out

cd "$REFERENCE_PRODUCT_ROOT"
prepare R-state through setup.sh
    -> complete reusable starting repository state established

select PF through mutate_pack.sh when the case names one
    -> finished pack files installed on this checkout

verify/apply EC
    -> any additional execution condition established

execute test and record
    -> leave the repository and evidence for inspection
```

Then change to the disposable checkout and invoke the selected R-state
through the reference product:

```sh
cd "$REFERENCE_PRODUCT_ROOT"
./external_test/curbpack/setup.sh <R-ID> --commit
./external_test/curbpack/mutate_pack.sh <PF-ID>
```

Call `mutate_pack.sh` only when the case names a PF other than the
committed PF-01 set, or must replace a previous PF on this checkout.
The only argument is the PF-id.

`--commit` records the prepared tree. It is not a revision argument.
`setup.sh` must not be given a commit, branch, tag, pin, or other revision.
The reference-product revision is already checked out by
`tmp/verification-run.sh`. Allowing `setup.sh` to select another revision
would break the frozen run.

`setup.sh` and the R-state scripts own all preparation of that state,
including file changes and any Git init, stage, commit, checkout, or clean
needed to establish it. The testcase consumes and verifies the prepared
state. It does not reproduce the internal operations of the R script. It
must not use `git init`, `git add`, or `git commit` to construct the
R-state.

Do not run product `reset.sh` between normal test cases. Do not assume the
previous case’s working directory or product tree is still valid.

## Repository content states

The detailed state definitions and commands are in
[0. Controlled repository content setup](0_controlled_repo_setup.md).

An R-id names the complete prepared repository state needed by a testcase.
That includes repository content; required file presence, absence, or
modification; the Git repository state needed as the starting condition;
and any initialization, staging, committing, checkout, or cleaning required
to establish that state. It is not defined by which script happens to
prepare it. Do not treat R as meaning “reference-product state” in general.

All R-states operate on the same disposable checkout:

```sh
"$CURBPACK_ROOT/tmp/cyberready-test-product"
"$REFERENCE_PRODUCT_ROOT"
```

No R-state may create or use a separate repository such as `tmp/R4` or
`tmp/R5`.

| ID | Condition | Preparation status | Implementation | Used by |
|---|---|---|---|---|
| R1 | Starting Glucose Log product content, including `SECURITY.md` and the heading `## Classification Rationale` in `docs/medtech/software_safety_class.md` | SCRIPTED | `./external_test/curbpack/setup.sh R1 --commit`; `states/R1.sh` | Curbpack, CTAM |
| R2 | R1 with `SECURITY.md` removed | SCRIPTED | `./external_test/curbpack/setup.sh R2 --commit`; `states/R2.sh` | Curbpack |
| R3 | R1 with the heading `## Classification Rationale` removed from `docs/medtech/software_safety_class.md` | SCRIPTED | `./external_test/curbpack/setup.sh R3 --commit`; `states/R3.sh` | Curbpack |
| R4 | demo-app content with token-only honesty-eval `SECURITY.md` and `package.json` identifying `acme-widget` | SCRIPTED | `./external_test/curbpack/setup.sh R4 --commit`; `states/R4.sh` | Curbpack |
| R5 | demo-app content with thin rule-satisfying honesty-eval `SECURITY.md` and original demo-app `package.json` | SCRIPTED | `./external_test/curbpack/setup.sh R5 --commit`; `states/R5.sh` | Curbpack |
| R6 | R1 plus stale `docs/review-log.md` and `docs/owned-policy.md` committed as `Owner <owner@example.com>` dated `2022-01-01T00:00:00Z` | SCRIPTED | `./external_test/curbpack/setup.sh R6 --commit`; `states/R6.sh` | Curbpack |
| R7 | R1 plus `docs/review-log.md` and `docs/owned-policy.md` committed as `Wrong Author <wrong@example.com>` dated `2026-09-13T12:00:00Z` | SCRIPTED | `./external_test/curbpack/setup.sh R7 --commit`; `states/R7.sh` | Curbpack |

CTAM-owned states live in the product `external_test/ctam/` tree and are
defined in CTAM `docs/testing/procedures.md`. Do not add those ids here.

After the sourced environment has recreated the frozen checkout,
`setup.sh R1 --commit` applies R1 to that checkout. `states/R1.sh` prints
the R1 description from this procedures set, then verifies the required
files, heading, and `package.json` conditions. The testcase checks that the
prepared state is the intended one. It does not copy those script
operations.

`--commit` changes Git recording, not repository content. For example,
`setup.sh R2` and `setup.sh R2 --commit` both prepare R2 content. Use
`--commit` when the case needs a recorded commit and a clean working tree
(EC-01). EC-01 is separate from the R-id and is stated by the case.

## Pack inputs

Details are in [1. Pack inputs](1_pack_template_instantiation.md).

| ID | Condition | Preparation status | Implementation | Used by |
|---|---|---|---|---|
| PF-01 | Reference-product pack set (`house-policy`, `cra-baseline`, `medtech-iec62304`) | SCRIPTED | Committed under `external_test/curbpack/packs/`; `CURBPACK_PACKS_DIR` from `verification-run.sh`; restore with `mutate_pack.sh PF-01` | Curbpack, CTAM |
| PF-02 | A second representative instantiated product pack | NOT YET SPECIFIED | Reserved. `mutate_pack.sh PF-02` is refused. | Curbpack |
| PF-03–PF-17 | One exact prepared input each (evaluator packs or Review Pack files) | SCRIPTED | `./external_test/curbpack/mutate_pack.sh PF-xx`. Registry: [1. Pack inputs](1_pack_template_instantiation.md) | Curbpack |

## Execution configurations

These conditions do not redefine repository content or pack input. R
preparation establishes the complete reusable starting repository state.
EC identifies any additional execution condition needed by the testcase
after that base R-state. Do not record the same property inconsistently
in both an R-id and an EC-id. A one-off testcase stimulus remains in the
testcase and does not require a new R-id.

| ID | Condition | Preparation status | Preparation / implementation |
|---|---|---|---|
| EC-01 | Recorded commit / clean working tree | SCRIPTED | After the named R-state, `setup.sh <R-id> --commit`. Verify `git status --porcelain` is empty. The testcase does not run `git init`, `git add`, or `git commit` |
| EC-02 | Dirty working tree | MANUAL BUT REPEATABLE | Prepare the named R-state, apply the case’s exact uncommitted edit, and verify `git status --porcelain` is non-empty |
| EC-03 | Detached HEAD | MANUAL BUT REPEATABLE | Prepare EC-01, then run `git checkout --detach HEAD` |
| EC-04 | Shallow clone | NOT YET SPECIFIED | The ID exists, but no complete case-specific preparation procedure is agreed |
| EC-05 | Sparse checkout / linked working tree / submodule | NOT YET SPECIFIED | The ID exists, but no complete case-specific preparation procedure is agreed |
| EC-06 | Offline | NOT YET SPECIFIED | The ID exists, but an exact platform-specific isolation and observation procedure is not yet defined |
| EC-07 | Locale / timezone variation | NOT YET SPECIFIED | The ID exists, but the locale and timezone matrix and commands are not yet defined |
| EC-08 | Concurrent local execution | NOT YET SPECIFIED | The ID exists, but no synchronization mechanism currently proves overlapping execution against a named shared output/cache location |
| EC-09 | Output failure injection | NOT YET SPECIFIED | The ID exists, but unwritable output, storage exhaustion, and controlled termination do not yet have reliable preparation procedures |
| EC-10 | Platform execution | NOT YET SPECIFIED | The ID exists, but per-platform installation and execution procedures are not yet defined |

EC-01 for R4 and R5 is `setup.sh R4 --commit` or `setup.sh R5 --commit` on
`"$REFERENCE_PRODUCT_ROOT"`.

## Names and directories

| Name | Meaning |
|---|---|
| **Curbpack** | This repository and the tool under test. |
| **Disposable reference-product checkout** | `"$CURBPACK_ROOT/tmp/cyberready-test-product"` (`"$REFERENCE_PRODUCT_ROOT"`). Every R-state is prepared here. |
| **Reference-product preparation directory** | `$REFERENCE_PRODUCT_ROOT/external_test/curbpack/`; invoke `setup.sh` from `"$REFERENCE_PRODUCT_ROOT"`. |
| **Throwaway repo** | A temporary Git repository created exactly as a case specifies when the case does not use an R-id. This is not `tmp/R4` or `tmp/R5`. |
| **Curbpack test data** | Existing fixtures under `<curbpack>/testdata/`. |

## Execute and record a case

1. Complete [Prepare a verification run](#prepare-a-verification-run) and copy
   the [test record](../generated_test_record_template.md) outside this
   repository.
2. Open the selected [suite](../../../testing/test_suites/README.md). Do not execute a row
   marked To be specified. Do not execute a case whose R-state is BLOCKED.
3. Do [Start of every independent case](#start-of-every-independent-case),
   then prepare the case’s stated `R-*`, `PF-*`, and `EC-*` prerequisites.
4. Execute the exact stimulus and compare the observed response with the
   declared response.
5. Keep raw output and record the disposition and evidence. Do not repair
   output files manually.
6. Leave the completed or failed repository and evidence available for
   inspection. Do not destroy them as part of the case. Destructive cleanup
   happens when the next testcase sources `tmp/verification-run.sh`.

Keep completed records outside this repository. A corrected Curbpack version
or changed test basis starts a new frozen baseline.

Independent source and release review uses
[2. Code and release review](2_code_review_procedures.md).
