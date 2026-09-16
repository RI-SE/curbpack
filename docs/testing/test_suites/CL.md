# CL — Claim review

## Objective

Documentation and generated outputs must not convert structural observations
into unsupported claims of security, compliance, certification, legal
sufficiency, clinical adequacy, CE marking or approval.

## Test basis

Requirements addressed by this suite:

- MUST-01
- MUST-02
- MUST-04

Other test basis:

- SDD opening product claim and SDD §1.1 claim boundary.
- SDD §11 prohibition on model-decided compliance or trust.

A test execution is always part of a test run that starts with [Prepare a verification run](../procedures/README.md).
In short it encompasses cloning the reference product into `<curbpack>/tmp/cyberready-test-product`,
using the recorded `<commit hash>` and `<date>`, and building the CLI. This is done once for a test run.

Each executable case starts the same way: from the Curbpack root, `source tmp/verification-run.sh`. That restore puts the disposable reference product back at the frozen baseline. You can run the cases in any order. Do not keep using the previous case’s directory. CL-001 then inspects frozen Curbpack source, and any generated output included in the assignment. It does not prepare an R-id and does not create a `tmp/R*` repository. CL-002 then prepares R1 or R2 via product `setup.sh` on that already-restored baseline. Then apply EC as the case states.

## Test suite overview


| ID     | Test case / purpose                                              | Requirements addressed | Test class | Procedure status |
| ------ | ---------------------------------------------------------------- | ---------------------- | ---------- | ---------------- |
| CL-001 | Public and generated claim review                                | MUST-01                | A          | Executable       |
| CL-002 | Boundary statement consistency                                   | MUST-02, MUST-04       | A          | Executable       |
| CL-003 | User interpretation of pass                                      | —                      | A          | To be specified  |
| CL-004 | Time/cost benefit claim                                          | —                      | C          | To be specified  |


---

## CL-001 — Verify that public and generated claims do not overclaim

### Requirements

- MUST-01

Passing this case does not close MUST-01: the review covers selected public
and generated surfaces, not every possible Curbpack statement.

### SETUP

- Repository state: no R-id. This case reviews frozen Curbpack source, not a
  reference-product content state. Do not run `setup.sh`. Do not create `tmp/R*`.
- Pack input: no PF-id unless generated output is included in the assignment.
- Execution configuration: no EC-id.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | Remain at `$CURBPACK_ROOT`. Do not `cd "$REFERENCE_PRODUCT_ROOT"` for this case. Do not prepare an R-state.                                       | Current directory is `$CURBPACK_ROOT`. The search corpus is this frozen Curbpack checkout, plus any generated JSON or Review Pack the assignment already includes.                                                                                                                                                                                              |


### TEST STEPS


| Step | Action                                                                                                                                                                                                                         | Expected result                                                                                                                                                          |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1    | Search shipped docs, site text, examples, CLI output, and issue/install material under `$CURBPACK_ROOT` for language that implies security, compliance, certification, CE marking, legal sufficiency, clinical adequacy, regulator acceptance, or RISE approval | Such language is absent, clearly denied, or clearly attributed to an authorised external party. A material overclaim fails this case (release-blocking for the assignment). |
| 2    | If the assignment includes generated JSON or Review Pack files from the same frozen baseline, search those files for the same language. If none are included, record that and skip this step.                                 | Same as Step 1 for any included generated files. Do not construct those files in this case.                                                                              |


---

## CL-002 — Verify that boundary statements stay consistent across machine and human output

### Requirements

- MUST-02
- MUST-04

Passing this case does not close MUST-02: the exact boundary sentence is not
required on every buyer/reviewer artefact. Passing this case does not close
MUST-04: signatures and every scoped score or status are not covered.

The chosen R-id is R1 or R2, recorded on the test record. Do not invent a
third R-id.

### SETUP

- Repository state: [R1](../procedures/0_controlled_repo_setup.md#r1) or [R2](../procedures/0_controlled_repo_setup.md#r2) — prepared by `setup.sh` in step 3. Record which R-id was used.
- Pack input: [PF-01](../procedures/1_pack_template_instantiation.md#pf-01) — selected by `verification-run.sh` through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-01](../procedures/0_controlled_repo_setup.md#ec-01) — established and verified by the setup steps below.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R1 --commit` or `./external_test/curbpack/setup.sh R2 --commit`, using the R-id recorded above.                | Applies the recorded R-id to the already-restored frozen baseline. Does not restore the baseline. Prints that R-state description. Otherwise, stop. For R2, HEAD is a local `test_*` branch.                                                                                                                                                                    |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `ls SECURITY.md`                                                                                                                                 | R1: the file is present. R2: the file should be missing. Otherwise, stop.                                                                                                                                                                                                                                                                                       |


### TEST STEPS


| Step | Action                                        | Expected result                                                                                                                                                                                                 |
| ---- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --json --as-of "$AS_OF_DATE"` | JSON is printed. Retain it for Step 5. Ignore `digest`, `timestamp`, and `agent`. For R1, `outcome` is `pass` as in EV-001. For R2, `outcome` is `findings` as in EV-002. That outcome is not this case's claim verdict. |
| 2    | `echo $?`                                     | R1: the exit status is `0`. R2: the exit status is `1`. That status is not this case's claim verdict.                                                                                                           |
| 3    | `curbpack share --as-of "$AS_OF_DATE"`        | Human-facing files are written under `$REFERENCE_PRODUCT_ROOT/review-pack/`. Retain them for Step 5. A non-zero exit on a failed check does not mean the Review Pack is missing.                                 |
| 4    | `echo $?`                                     | R1: the exit status is `0`. R2: the exit status is `1`. Share exits non-zero when check is red. Do not treat that as a missing Review Pack.                                                                     |
| 5    | Compare disclaimers and explanatory sentences across the JSON from Step 1 and the human-facing files from Step 3 | No derivative weakens the structural-only boundary or turns a non-pass into assurance. |


---

## CL-003 — Verify user interpretation of pass

### Requirements

This case does not verify a specified requirement.

Other test basis:

- Catalogue purpose: user interpretation of pass.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## CL-004 — Verify a time/cost benefit claim

### Requirements

This case does not verify a specified requirement.

Other test basis:

- Catalogue purpose: time/cost benefit claim.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
  this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
  directly contradicts the suite objective. Unsupported assurance or
  conformity language is a failure.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
  unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.
