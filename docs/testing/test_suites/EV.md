# EV — Evaluation semantics

## Objective

Supported checks must report their defined result states correctly. Missing,
unreadable, unsupported or skipped required targets must never be represented
as passed.

## Test basis

Requirements addressed by this suite::

- MUST-22
- MUST-23
- MUST-24
- MUST-53

A test execution is always part of a test run that starts with [Prepare a verification run](../procedures/README.md).
In short it encompasses cloning the reference product into `<curbpack>/tmp/cyberready-test-product`,
using the recorded `<commit hash>` and `<date>`, and building the CLI. This is done once for a test run.

Each executable case starts the same way: from the Curbpack root, `source tmp/verification-run.sh`. That restore puts the disposable reference product back at the frozen baseline. You can run the cases in any order. Do not keep using the previous case’s directory. Then prepare the case’s named R-state: R1–R3 via product `setup.sh` on that already-restored baseline; R4/R5 via product `states/R4.sh` / `states/R5.sh` (targets under Curbpack `tmp/`, fixtures from Curbpack testdata). Then apply EC as the case states. 

## Test suite overview


| ID     | Test case / purpose                                               | Requirements addressed | Test class | Procedure status |
| ------ | ----------------------------------------------------------------- | ---------------------- | ---------- | ---------------- |
| EV-001 | Good reference product yields a pass                              | MUST-53                | A          | Executable       |
| EV-002 | Missing required file yields a fail                               | MUST-53                | A          | Executable       |
| EV-003 | Missing required section yields a fail                            | —                      | A          | Executable       |
| EV-004 | Unreadable required target is not reported as a pass              | MUST-22, MUST-24       | A          | To be specified  |
| EV-005 | Skipped, excluded or unsupported target is not treated as a pass  | MUST-23                | A          | To be specified  |
| EV-006 | Token-only text does not yield a pass                             | —                      | A          | Executable       |
| EV-007 | Each supported check type fails when its condition is changed     | —                      | A          | To be specified  |
| EV-008 | Outcome does not depend on rule order or file order               | —                      | A          | To be specified  |
| EV-009 | Thin rule-satisfying text yields a pass without a substance claim | —                      | A          | Executable       |


---



## EV-001 — Verify that a good reference product yields a pass



### SETUP

- Repository state: [R1](../procedures/0_controlled_repo_setup.md#r1) — prepared by `setup.sh` in step 3.
- Pack input: [PF-01](../procedures/1_pack_template_instantiation.md#pf-01) — selected by `verification-run.sh` through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-01](../procedures/0_controlled_repo_setup.md#ec-01) — established and verified by the setup steps below.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                           |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                         |
| 3    | `./external_test/curbpack/setup.sh R1 --commit`                                                                                                  | Applies R1 to the already-restored frozen baseline. Does not restore the baseline. Prints the R1 state description (required files, heading, `package.json` conditions). Otherwise, stop.                                                                                                              |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                         |




### TEST STEPS


| Step | Action                                        | Expected result                                                                                                                                                                  |
| ---- | --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --json --as-of "$AS_OF_DATE"` | The command completes successfully. Ignore `digest`, `timestamp`, `agent`, and `statechart_context`. Verify the final result fields against the expected values shown in Fig. 1. |
| 2    | `echo $?`                                     | The exit status is `0`.                                                                                                                                                          |


```json
{
  "failures": null,
  "pack_id": "house-policy,medtech-iec62304",
  "readiness_score": 100,
  "outcome": "pass",
  "evaluated_rules": 15,
  "conformity_claim": "none"
}
```

**Fig. 1.** Example of a successful execution of Step 1.

Empty lists in this JSON are encoded as `null`, not `[]`. This applies to both `failures` and `failed_orthogonal_regions`. A successful result has `"outcome": "pass"` and no failure objects under `failures`.

---



## EV-002 — Verify that a missing required file yields a fail



### SETUP

- Repository state: [R2](../procedures/0_controlled_repo_setup.md#r2) — prepared by `setup.sh` in step 3.
- Pack input: [PF-01](../procedures/1_pack_template_instantiation.md#pf-01) — selected by `verification-run.sh` through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-01](../procedures/0_controlled_repo_setup.md#ec-01) — established and verified by the setup steps below.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                           |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                         |
| 3    | `./external_test/curbpack/setup.sh R2 --commit`                                                                                                  | Applies R2 to the already-restored frozen baseline. Does not restore the baseline. Prints the R2 state description (`SECURITY.md` absent, not empty). Otherwise, stop. HEAD is a local `test_*` branch.                                                                                                |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                         |
| 5    | `ls SECURITY.md`                                                                                                                                 | The file should be missing.                                                                                                                                                                                                                                               |




### TEST STEPS


| Step | Action                                        | Expected result                                                                                                                                                                                       |
| ---- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --json --as-of "$AS_OF_DATE"` | JSON is printed. Ignore `digest`, `timestamp`, and `agent`. Verify the final result fields against Fig. 2. `outcome` is `findings`, not `pass`. The `SECURITY.md` check is not represented as passed. |
| 2    | `echo $?`                                     | The exit status is `1`.                                                                                                                                                                               |


```json
{
  "failures": [
    {
      "gate_id": "HOUSE-SECURITY-MD",
      "severity": "high",
      "type": "POLICY_VIOLATION",
      "sanitized_description": "SECURITY.md missing, too short, or lacking required header.",
      "ast_coordinates": {
        "target_file": "SECURITY.md",
        "node_path": "",
        "target_symbol": "",
        "fallback_lines": ""
      },
      "remediation": {
        "action_required": "Add SECURITY.md with vulnerability reporting and response expectations.",
        "expected_state": "SECURITY.md present with Security header and substantive content."
      }
    }
  ],
  "pack_id": "house-policy,medtech-iec62304",
  "readiness_score": 80,
  "outcome": "findings",
  "failed_rules": 1,
  "evaluated_rules": 15,
  "conformity_claim": "none"
}
```

**Fig. 2.** Example of the last fields after Step 1. On this fail, `failed_orthogonal_regions` earlier in the JSON is a list, not `null`. Look at these last fields anyway.

---



## EV-003 — Verify that a missing required section yields a fail



### SETUP

- Repository state: [R3](../procedures/0_controlled_repo_setup.md#r3) — prepared by `setup.sh` in step 3.
- Pack input: [PF-01](../procedures/1_pack_template_instantiation.md#pf-01) — selected by `verification-run.sh` through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-01](../procedures/0_controlled_repo_setup.md#ec-01) — established and verified by the setup steps below.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                           |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                         |
| 3    | `./external_test/curbpack/setup.sh R3 --commit`                                                                                                  | Applies R3 to the already-restored frozen baseline. Does not restore the baseline. Prints the R3 state description (heading `## Classification Rationale` removed). Otherwise, stop. HEAD is a local `test_*` branch.                                                                                  |
| 4    | `git status --porcelain`                                                                                                                         | NO output. Working tree is clean.                                                                                                                                                                                                                                         |
| 5    | `ls docs/medtech/software_safety_class.md`                                                                                                       | The file should be present.                                                                                                                                                                                                                                               |
| 6    | `grep -F "## Classification Rationale" docs/medtech/software_safety_class.md`                                                                    | NO output                                                                                                                                                                                                                                                                 |




### TEST STEPS


| Step | Action                                        | Expected result                                                                                                                                                                                |
| ---- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --json --as-of "$AS_OF_DATE"` | JSON is printed. Ignore `digest`, `timestamp`, and `agent`. Verify the final result fields against Fig. 3. `outcome` is `findings`, not `pass`. `HOUSE-SECURITY-MD` is not among the failures. |
| 2    | `echo $?`                                     | The exit status is `1`.                                                                                                                                                                        |


```json
{
  "failures": [
    {
      "gate_id": "MD-SW-CLASS",
      "severity": "high",
      "type": "POLICY_VIOLATION",
      "sanitized_description": "IEC 62304 software safety classification rationale missing. (missing header: ## Classification Rationale)",
      "ast_coordinates": {
        "target_file": "docs/medtech/software_safety_class.md",
        "node_path": "",
        "target_symbol": "",
        "fallback_lines": ""
      },
      "remediation": {
        "action_required": "Document Class A/B/C rationale in docs/medtech/software_safety_class.md.",
        "expected_state": "Safety class declared with rationale."
      }
    }
  ],
  "pack_id": "house-policy,medtech-iec62304",
  "readiness_score": 80,
  "outcome": "findings",
  "failed_rules": 1,
  "evaluated_rules": 15,
  "conformity_claim": "none"
}
```

**Fig. 3.** Example of the last fields after Step 1.

---



## EV-004 — Verify that an unreadable required target is not reported as a pass



### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---



## EV-005 — Verify that a skipped, excluded or unsupported target is not treated as a pass



### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---



## EV-006 — Verify that token-only text does not yield a pass



### SETUP

- Repository state: [R4](../procedures/0_controlled_repo_setup.md#r4) — prepared by product `states/R4.sh` in step 2.
- Pack input: `house-policy` only (`--packs house-policy`). No PF-id.
- Execution configuration: [EC-01](../procedures/0_controlled_repo_setup.md#ec-01) — established by the git commands in steps 4–7.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                           |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. Otherwise, stop. |
| 2    | `"$REFERENCE_PRODUCT_ROOT/external_test/curbpack/states/R4.sh"`                                                                                    | Applies R4. Recreates `$CURBPACK_ROOT/tmp/R4` only. Prints the R4 state description (token-only `SECURITY.md`, `package.json` name `acme-widget`). Does not init Git. Does not change the reference product. Otherwise, stop.                                             |
| 3    | `cd "$CURBPACK_ROOT/tmp/R4"`                                                                                                                     | Current directory is `$CURBPACK_ROOT/tmp/R4`.                                                                                                                                                                                                                           |
| 4    | `git init`                                                                                                                                       | A new Git repository.                                                                                                                                                                                                                                                     |
| 5    | `git add -A`                                                                                                                                     | The fixture files are staged.                                                                                                                                                                                                                                             |
| 6    | `git -c user.name=curbpack-fixture -c user.email=curbpack-fixture@invalid commit -m fixture`                                                     | One commit.                                                                                                                                                                                                                                                               |
| 7    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                         |




### TEST STEPS


| Step | Action                                                             | Expected result                                                                                                                                                                                      |
| ---- | ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --packs house-policy --json --as-of "$AS_OF_DATE"` | JSON is printed. Ignore `digest`, `timestamp`, and `agent`. Verify the final result fields against Fig. 4. `outcome` is `findings`, not `pass`. A product name in the file is not enough for a pass. |
| 2    | `echo $?`                                                          | The exit status is `1`.                                                                                                                                                                              |


```json
{
  "failures": [
    {
      "gate_id": "HOUSE-ANTI-PLACEHOLDER",
      "severity": "high",
      "type": "POLICY_VIOLATION",
      "sanitized_description": "House policy docs contain placeholder / boilerplate text. (scaffold body overlap)",
      "ast_coordinates": {
        "target_file": "SECURITY.md",
        "node_path": "",
        "target_symbol": "",
        "fallback_lines": ""
      },
      "remediation": {
        "action_required": "Replace TODO / lorem ipsum / [insert ...] with real contact and process details.",
        "expected_state": "No placeholder patterns in required security docs."
      }
    }
  ],
  "pack_id": "house-policy",
  "readiness_score": 80,
  "outcome": "findings",
  "failed_rules": 1,
  "evaluated_rules": 5,
  "conformity_claim": "none"
}
```

**Fig. 4.** Example of the last fields after Step 1. `pack_id` is `house-policy` only. `evaluated_rules` is `5`, not `15`.

---



## EV-007 — Verify that each supported check type fails when its condition is changed



### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---



## EV-008 — Verify that outcome does not depend on rule order or file order



### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---



## EV-009 — Verify that thin rule-satisfying text yields a pass without a substance claim



### SETUP

- Repository state: [R5](../procedures/0_controlled_repo_setup.md#r5) — prepared by product `states/R5.sh` in step 2.
- Pack input: `house-policy` only (`--packs house-policy`). No PF-id.
- Execution configuration: [EC-01](../procedures/0_controlled_repo_setup.md#ec-01) — established by the git commands in steps 4–7.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                           |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. Otherwise, stop. |
| 2    | `"$REFERENCE_PRODUCT_ROOT/external_test/curbpack/states/R5.sh"`                                                                                    | Applies R5. Recreates `$CURBPACK_ROOT/tmp/R5` only. Prints the R5 state description (thin real `SECURITY.md`, original demo-app `package.json`). Does not init Git. Does not change the reference product. Otherwise, stop.                                               |
| 3    | `cd "$CURBPACK_ROOT/tmp/R5"`                                                                                                                     | Current directory is `$CURBPACK_ROOT/tmp/R5`.                                                                                                                                                                                                                           |
| 4    | `git init`                                                                                                                                       | A new Git repository.                                                                                                                                                                                                                                                     |
| 5    | `git add -A`                                                                                                                                     | The fixture files are staged.                                                                                                                                                                                                                                             |
| 6    | `git -c user.name=curbpack-fixture -c user.email=curbpack-fixture@invalid commit -m fixture`                                                     | One commit.                                                                                                                                                                                                                                                               |
| 7    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                         |




### TEST STEPS


| Step | Action                                                             | Expected result                                                                                                                                                                                                                                                                                      |
| ---- | ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --packs house-policy --json --as-of "$AS_OF_DATE"` | JSON is printed. Ignore `digest`, `timestamp`, `agent`, and `statechart_context`. Verify the final result fields against Fig. 5. Nothing in this output claims the text is correct, secure, compliant, certified, or approved. A human may still find the text thin. That is not a Curbpack failure. |
| 2    | `echo $?`                                                          | The exit status is `0`.                                                                                                                                                                                                                                                                              |


```json
{
  "failures": null,
  "pack_id": "house-policy",
  "readiness_score": 100,
  "outcome": "pass",
  "evaluated_rules": 5,
  "conformity_claim": "none"
}
```

**Fig. 5.** Example of a successful execution of Step 1. `pack_id` is `house-policy` only. `evaluated_rules` is `5`, not `15`.

---



## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
directly contradicts the suite objective. A required target represented as
passed when it is missing, unreadable, unsupported, or skipped is a failure.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.

