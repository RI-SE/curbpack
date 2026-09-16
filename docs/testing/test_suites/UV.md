# UV — User and organisational-use validation

## Objective

Representative users must be able to perform the defined handoff and
correctly interpret what a Curbpack pass means and does not mean. Where
organisational-use validation is in scope, an authorised security or risk
representative must be able to state permitted and prohibited use and residual
risk from the evidence.

## Test basis

Requirements addressed by this suite:

- MUST-60

Other test basis:

- SDD §1 publisher, producer, reviewer, and agent responsibilities.
- SDD §10 no-code operation and human-review interpretation boundary.

A test execution is always part of a test run that starts with [Prepare a verification run](../procedures/README.md).
In short it encompasses cloning the reference product into `<curbpack>/tmp/cyberready-test-product`,
using the recorded `<commit hash>` and `<date>`, and building the CLI. This is done once for a test run.

Each executable case starts the same way: from the Curbpack root, `source tmp/verification-run.sh`. That restore puts the disposable reference product back at the frozen baseline. You can run the cases in any order. Do not keep using the previous case’s directory. UV-001 records the verification envelope on the test record and runs the builder task from the restored reference product without `setup.sh`. UV-002 and UV-003 prepare [R2](../procedures/0_controlled_repo_setup.md#r2) via product `setup.sh` on that already-restored baseline. These are facilitated builder cases: a representative builder performs the handoff; the facilitator prepares state and records observations. They are not unattended CLI oracles with fixed JSON outcomes.

## Test suite overview


| ID     | Test case / purpose                              | Requirements addressed | Test class | Procedure status |
| ------ | ------------------------------------------------ | ---------------------- | ---------- | ---------------- |
| UV-001 | Builder installs or uses the frozen binary       | MUST-60                | A          | Executable       |
| UV-002 | Builder interprets seeded results                | —                      | A          | Executable       |
| UV-003 | Builder corrects one structural gap              | MUST-60                | A          | Executable       |
| UV-004 | Builder creates a Review Pack                    | —                      | A          | To be specified  |
| UV-005 | Reviewer reads identity from the handoff         | —                      | A          | To be specified  |
| UV-006 | Reviewer compares machine JSON to summary        | —                      | A          | To be specified  |
| UV-007 | Organisational permitted-use decision            | —                      | A          | To be specified  |
| UV-008 | Buyer/reviewer comparison of two Review Packs    | —                      | B          | To be specified  |


---

## UV-001 — Builder installs or uses the frozen binary

### Requirements

- MUST-60

Passing this case does not close MUST-60: UV-003 and CR-09 cover other
documented command paths. Selected documented paths are executed, not every
printed operator- or agent-facing command.

### SETUP

- Repository state: no R-id. The builder works on a clean machine or clean
  PATH. The facilitator does not run `setup.sh`; execution is from the restored
  disposable checkout at the frozen baseline.
- Pack input: no PF-id.
- Execution configuration: no EC-id; record the clean platform/environment on
  the test record.
- Other prerequisite: a representative builder selected by the assignment and
  the frozen release’s documented installation path.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`. Do not run `setup.sh`. Record the printed Curbpack commit and tag (if a shipped binary is in scope) on the test record **Run** table. | Current directory is `$REFERENCE_PRODUCT_ROOT`. The verification envelope is recorded. The disposable checkout remains at the frozen baseline from step 1.                                                                                                                                      |


### TEST STEPS


| Step | Action                                                                                                                                              | Expected result                                                                                    |
| ---- | --------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| 1    | Give the builder only the documented install path ([install](../../getting-started/install.md) or the freeze’s release notes). No live author coaching. | The builder has only the documented path.                                                          |
| 2    | Builder installs or runs the frozen `curbpack` from `$REFERENCE_PRODUCT_ROOT` on the clean platform.                                                | The task completes without live product-author support.                                            |
| 3    | Any assistance given                                                                                                                                  | Written on the test record.                                                                        |


---

## UV-002 — Builder interprets seeded results

### Requirements

This case does not verify a specified requirement.

Other test basis:

- SDD §10 no-code operation and human-review interpretation boundary.

This case is builder interpretation of check results; it is not MUST-60
(printed-command execution as written in agent- or operator-facing files).

### SETUP

- Repository state: [R2](../procedures/0_controlled_repo_setup.md#r2) — prepared by `setup.sh` in step 3.
- Pack input: [PF-01](../procedures/1_pack_template_instantiation.md#pf-01) — selected by `verification-run.sh` through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-01](../procedures/0_controlled_repo_setup.md#ec-01) — established and verified by the setup steps below.
- Other prerequisite: the builder has completed UV-001 or already has the
  frozen binary available. Do not tell the builder the expected gate ID or
  interpretation.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R2 --commit`                                                                                                  | Applies R2 to the already-restored frozen baseline. Does not restore the baseline. Prints the R2 state description (`SECURITY.md` absent, not empty). Otherwise, stop. HEAD is a local `test_*` branch.                                                                                                                                                         |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `ls SECURITY.md`                                                                                                                                 | The file should be missing.                                                                                                                                                                                                                                                                                                                                     |
| 6    | Open a builder shell at `$REFERENCE_PRODUCT_ROOT` with `CURBPACK_PACKS_DIR` exported as after step 1 (PF-01 packs).                                                                                              | Shell is at the prepared tree.                                                                                                                                                                                                                                                                                                                                    |
| 7    | In that shell: `pwd`; `echo "$CURBPACK_PACKS_DIR"`; `ls "$CURBPACK_PACKS_DIR/house-policy/pack.json"`.                                                                                                             | Current directory is `$REFERENCE_PRODUCT_ROOT`. Printed `CURBPACK_PACKS_DIR` is exactly `$REFERENCE_PRODUCT_ROOT/external_test/curbpack/packs`. The PF-01 `house-policy` pack file is present. Otherwise, stop.                                                                                                                                                 |
| 8    | Hand control to the builder. Do not disclose the expected gate ID or pass/fail semantics beyond what the product docs provide.                                                                                     | The builder can run `curbpack check` from the prepared tree without facilitator-supplied oracle text.                                                                                                                                                                                                                                                           |


### TEST STEPS


| Step | Action                                                                                              | Expected result                                                                                                      |
| ---- | --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| 1    | Builder runs `curbpack check --as-of "$AS_OF_DATE"` from `$REFERENCE_PRODUCT_ROOT`.               | The command runs as invoked; the facilitator does not correct the command line unless recording assistance on the test record. |
| 2    | Builder explains the first results, including the failure.                                            | Interpretation matches documented semantics. The facilitator records whether live coaching was required.             |


---

## UV-003 — Builder corrects one structural gap

### Requirements

- MUST-60

Passing this case does not close MUST-60: UV-001 and CR-09 cover other
documented command paths. Selected documented paths are executed, not every
printed operator- or agent-facing command.

### SETUP

- Repository state: [R2](../procedures/0_controlled_repo_setup.md#r2) — prepared by `setup.sh` in step 3.
- Pack input: [PF-01](../procedures/1_pack_template_instantiation.md#pf-01) — selected by `verification-run.sh` through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-01](../procedures/0_controlled_repo_setup.md#ec-01) for steps 3–5. After the builder restores `SECURITY.md`, the working tree is dirty ([EC-02](../procedures/README.md#execution-configurations)).
- Other prerequisite: the builder has the frozen binary available. Tell the
  builder only that the reported missing-file finding should be corrected
  using the product baseline. If the builder asks for the exact Git operation,
  record that assistance; the deterministic restoration command for the test
  record is
  `git show $REFERENCE_PRODUCT_COMMIT:SECURITY.md > SECURITY.md`.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R2 --commit`                                                                                                  | Applies R2 to the already-restored frozen baseline. Does not restore the baseline. Prints the R2 state description (`SECURITY.md` absent, not empty). Otherwise, stop.                                                                                                                                                                                         |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `ls SECURITY.md`                                                                                                                                 | The file should be missing.                                                                                                                                                                                                                                                                                                                                     |


### TEST STEPS


| Step | Action                                                                                                                        | Expected result                                                                                                                                 |
| ---- | ----------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Builder restores `SECURITY.md` from the frozen product baseline and reruns `curbpack check --as-of "$AS_OF_DATE"`.            | The `HOUSE-SECURITY-MD` finding is gone from the builder’s reported results; unrelated results stay as the builder and facilitator observe.     |
| 2    | Any assistance given (including the exact Git operation)                                                                      | Written on the test record.                                                                                                                     |
| 3    | After Step 1, facilitator runs `git status --porcelain` at `$REFERENCE_PRODUCT_ROOT`.                                      | Output is non-empty (EC-02). The restoration is present as an uncommitted change.                                                               |


---

## UV-004 — Builder creates a Review Pack

### Requirements

This case does not verify a specified requirement.

Do not invent a Review Pack creation procedure here. A pass cannot close the
suite objective for this handoff because the case is not executable.

### SETUP

Not specified yet. Do not run.

### TEST STEPS

Not specified yet. Do not run.

---

## UV-005 — Reviewer reads identity from the handoff

### Requirements

This case does not verify a specified requirement.

Do not invent a reviewer handoff procedure here. A pass cannot close the
suite objective for this handoff because the case is not executable.

### SETUP

Not specified yet. Do not run.

### TEST STEPS

Not specified yet. Do not run.

---

## UV-006 — Reviewer compares machine JSON to summary

### Requirements

This case does not verify a specified requirement.

Do not invent a reviewer JSON comparison procedure here. A pass cannot close
the suite objective for this handoff because the case is not executable.

### SETUP

Not specified yet. Do not run.

### TEST STEPS

Not specified yet. Do not run.

---

## UV-007 — Organisational permitted-use decision

### Requirements

This case does not verify a specified requirement.

Do not invent an organisational permitted-use procedure here. A pass cannot
close the suite objective for this handoff because the case is not executable.

### SETUP

Not specified yet. Do not run.

### TEST STEPS

Not specified yet. Do not run.

---

## UV-008 — Buyer/reviewer comparison of two Review Packs

### Requirements

This case does not verify a specified requirement.

Do not invent a buyer or reviewer comparison procedure here. A pass cannot
close the suite objective for this handoff because the case is not executable.

### SETUP

Not specified yet. Do not run.

### TEST STEPS

Not specified yet. Do not run.

---

## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
  this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
  directly contradicts the suite objective. Inability to perform the selected
  handoff or material misinterpretation of a Curbpack pass is a failure.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
  unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.
