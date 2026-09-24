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

A test execution is always part of a test run that starts with [Prepare a verification run](../../docs2/testing/procedures/README.md).
In short it encompasses cloning the reference product into `<curbpack>/tmp/cyberready-test-product`,
using the recorded `<commit hash>` and `<date>`, and building the CLI. This is done once for a test run.

Each executable case starts the same way: from the Curbpack root, `source tmp/verification-run.sh`. That restore puts the disposable reference product back at the frozen baseline. You can run the cases in any order. Do not keep using the previous case’s directory. Then prepare the case’s named R-state through product `setup.sh` on that already-restored baseline. Then apply EC as the case states.

## Test suite overview


| ID     | Test case / purpose                                               | Requirements addressed | Test class | Procedure status |
| ------ | ----------------------------------------------------------------- | ---------------------- | ---------- | ---------------- |
| EV-001 | Good reference product yields a pass                              | MUST-53                | A          | Executable       |
| EV-002 | Missing required file yields a fail                               | MUST-53                | A          | Executable       |
| EV-003 | Missing required section yields a fail                            | —                      | A          | Executable       |
| EV-004 | Unreadable required target is not reported as a pass              | MUST-22, MUST-24       | A          | Executable       |
| EV-005 | Skipped, excluded or unsupported target is not treated as a pass  | MUST-23                | A          | Executable       |
| EV-006 | Token-only text does not yield a pass                             | —                      | A          | Executable       |
| EV-007 | Each supported check type fails when its condition is changed     | —                      | A          | Executable       |
| EV-008 | Outcome does not depend on rule order or file order               | —                      | A          | Partial (A executable; B blocked) |
| EV-009 | Thin rule-satisfying text yields a pass without a substance claim | —                      | A          | Executable       |


---

## EV-001 — Verify that a good reference product yields a pass

### Requirements

- MUST-53

### SETUP

- Repository state: [R1](../../docs2/testing/procedures/0_controlled_repo_setup.md#r1) — prepared by `setup.sh` in step 3.
- Pack input: [PF-01](../../docs2/testing/procedures/1_pack_template_instantiation.md#pf-01) — selected by `verification-run.sh` through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-01](../../docs2/testing/procedures/0_controlled_repo_setup.md#ec-01) — established and verified by the setup steps below.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R1 --commit`                                                                                                  | Applies R1 to the already-restored frozen baseline. Does not restore the baseline. Prints the R1 state description (required files, heading, `package.json` conditions). Otherwise, stop.                                                                                                                                                                       |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |


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

### Requirements

- MUST-53

### SETUP

- Repository state: [R2](../../docs2/testing/procedures/0_controlled_repo_setup.md#r2) — prepared by `setup.sh` in step 3.
- Pack input: [PF-01](../../docs2/testing/procedures/1_pack_template_instantiation.md#pf-01) — selected by `verification-run.sh` through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-01](../../docs2/testing/procedures/0_controlled_repo_setup.md#ec-01) — established and verified by the setup steps below.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R2 --commit`                                                                                                  | Applies R2 to the already-restored frozen baseline. Does not restore the baseline. Prints the R2 state description (`SECURITY.md` absent, not empty). Otherwise, stop. HEAD is a local `test_*` branch.                                                                                                                                                         |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `ls SECURITY.md`                                                                                                                                 | The file should be missing.                                                                                                                                                                                                                                                                                                                                     |


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

### Requirements

This case does not verify a specified requirement.

Other test basis:

- SDD §5.1 check kinds (`annex_file` required headers).

### SETUP

- Repository state: [R3](../../docs2/testing/procedures/0_controlled_repo_setup.md#r3) — prepared by `setup.sh` in step 3.
- Pack input: [PF-01](../../docs2/testing/procedures/1_pack_template_instantiation.md#pf-01) — selected by `verification-run.sh` through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-01](../../docs2/testing/procedures/0_controlled_repo_setup.md#ec-01) — established and verified by the setup steps below.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R3 --commit`                                                                                                  | Applies R3 to the already-restored frozen baseline. Does not restore the baseline. Prints the R3 state description (heading `## Classification Rationale` removed). Otherwise, stop. HEAD is a local `test_*` branch.                                                                                                                                           |
| 4    | `git status --porcelain`                                                                                                                         | NO output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `ls docs/medtech/software_safety_class.md`                                                                                                       | The file should be present.                                                                                                                                                                                                                                                                                                                                     |
| 6    | `grep -F "## Classification Rationale" docs/medtech/software_safety_class.md`                                                                    | NO output                                                                                                                                                                                                                                                                                                                                                       |


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

### Requirements

- MUST-22
- MUST-24

In EV-002 the file is missing. Here the file is still there. This user cannot
read it. The check does not print the usual JSON. It stops with an error on
stderr.

### SETUP

- Repository state: [R1](../../docs2/testing/procedures/0_controlled_repo_setup.md#r1) — prepared by `setup.sh` in step 3. The later `chmod` does not create a new R-id. The text of `SECURITY.md` is still R1. Only the permission bits change.
- Pack input: [PF-01](../../docs2/testing/procedures/1_pack_template_instantiation.md#pf-01) — selected by `verification-run.sh` through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-01](../../docs2/testing/procedures/0_controlled_repo_setup.md#ec-01) — established and verified by steps 3–4. After step 6 the working tree is no longer EC-01. That is expected. Git cannot hash an unreadable `SECURITY.md`.


| Step | Action                                                                                                                                          | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh` Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                  | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R1 --commit`                                                                                                 | Applies R1 to the already-restored frozen baseline. Does not restore the baseline. Prints the R1 state description (required files, heading, `package.json` conditions). Otherwise, stop.                                                                                                                                                                       |
| 4    | `git status --porcelain`                                                                                                                        | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `ls SECURITY.md`                                                                                                                                | The file is present.                                                                                                                                                                                                                                                                                                                                            |
| 6    | `chmod 000 SECURITY.md`                                                                                                                         | `ls -l SECURITY.md` shows no read permission for this user (the mode letters start with `----------`). The file is still present.                                                                                                                                                                                                                               |
| 7    | `test -r SECURITY.md; echo $?`                                                                                                                  | The printed status is `1`. This user cannot read the file. If the status is `0`, stop: this machine can still read it, so the case cannot be run.                                                                                                                                                                                                               |
| 8    | `git status --porcelain`                                                                                                                        | `M SECURITY.md` should be listed.                                                                                                                                                                                                                                                                                                                               |


### TEST STEPS


| Step | Action                                        | Expected result                                                                                                                                                                                           |
| ---- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --json --as-of "$AS_OF_DATE"` | The command does not print JSON. stdout is empty. stderr is the line in the example below (`read input SECURITY.md` and `permission denied`). The absolute path is `$REFERENCE_PRODUCT_ROOT/SECURITY.md`. |
| 2    | `echo $?`                                     | The exit status is `1`.                                                                                                                                                                                   |


```text
read input SECURITY.md: open <reference-product-root>/SECURITY.md: permission denied
```

**Example.** stderr after Step 1. stdout is empty. Compare the words `read input SECURITY.md` and `permission denied`. The open path is the `SECURITY.md` in this run’s reference-product checkout.

---

## EV-005 — Verify that a skipped, excluded or unsupported target is not treated as a pass

### Requirements

- MUST-23

This procedure is the `--diff` skip path only.

Observed deviation: the skipped-rule identifier is not present in every output
channel required by MUST-23. See [REG-SKIP-01](../../docs/software-design-document.md#reg-skip-01).
A pass on this case does not close MUST-23.

### SETUP

- Repository state: [R1](../../docs2/testing/procedures/0_controlled_repo_setup.md#r1) — prepared by `setup.sh` in step 3. Step 6 adds `docs/ev005-skip.md`. That file is stimulus, not a new R-id.
- Pack input: [PF-01](../../docs2/testing/procedures/1_pack_template_instantiation.md#pf-01) — selected by `verification-run.sh` through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-01](../../docs2/testing/procedures/0_controlled_repo_setup.md#ec-01) — established and verified by steps 3–4. After step 6 the working tree is dirty.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R1 --commit`                                                                                                  | Applies R1 to the already-restored frozen baseline. Does not restore the baseline. Prints the R1 state description (required files, heading, `package.json` conditions). Otherwise, stop.                                                                                                                                                                       |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `printf '%s\n' '# EV-005 skip stimulus' 'This file is not a pack target.' > docs/ev005-skip.md`                                                  | The file `docs/ev005-skip.md` now exists.                                                                                                                                                                                                                                                                                                                       |
| 6    | `git status --porcelain`                                                                                                                         | `?? docs/ev005-skip.md`                                                                                                                                                                                                                                                                                                                                         |


### TEST STEPS


| Step | Action                                                                    | Expected result                                                                                                                                                                                           |
| ---- | ------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --diff --json --as-of "$AS_OF_DATE"`                      | JSON is printed. Ignore `digest`, `timestamp`, and `agent`. Verify the final result fields against the example below. `outcome` is `incomplete`. `skipped_rules` is `1`. If `skipped_rules` is `0`, stop. |
| 2    | `echo $?`                                                                 | The exit status is `1`.                                                                                                                                                                                   |
| 3    | `grep -A2 skipped_rule_ids .github/curbpack/cache/latest_evaluation.json` | The printed list contains `HOUSE-SECRET-PATHS`.                                                                                                                                                           |
| 4    | `cat .github/curbpack/cache/latest_action_report.md`                      | The report contains `**Outcome:** incomplete` and `**Failed / evaluated / skipped:** 0 / 14 / 1`. It also contains `Evaluation incomplete: some rules were skipped`.                                              |


```json
{
  "failures": null,
  "pack_id": "house-policy,medtech-iec62304",
  "readiness_score": 100,
  "outcome": "incomplete",
  "skipped_rules": 1,
  "evaluated_rules": 14,
  "conformity_claim": "none"
}
```

**Example.** Last fields after Step 1. `evaluated_rules` is `14`, not `15`. `skipped_rules` is `1`.

---

## EV-006 — Verify that token-only text does not yield a pass

### Requirements

This case does not verify a specified requirement.

Other test basis:

- SDD §5.1 check kinds (`anti_placeholder`).

### SETUP

- Repository state: [R4](../../docs2/testing/procedures/0_controlled_repo_setup.md#r4) — prepared by `setup.sh` in step 3.
- Pack input: `house-policy` only (`--packs house-policy`). No PF-id.
- Execution configuration: [EC-01](../../docs2/testing/procedures/0_controlled_repo_setup.md#ec-01) — established and verified by the setup steps below.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R4 --commit`                                                                                                  | Applies R4 to the already-restored frozen baseline. Does not restore the baseline. Prints the R4 state description (token-only `SECURITY.md`, `package.json` name `acme-widget`). Otherwise, stop. HEAD is a local `test_*` branch. This step does not create `$CURBPACK_ROOT/tmp/R4`.                                                                          |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `grep -F '"name": "acme-widget"' package.json`                                                                                                   | The line is printed.                                                                                                                                                                                                                                                                                                                                            |
| 6    | `grep -Fx acme-widget SECURITY.md`                                                                                                               | The line is printed.                                                                                                                                                                                                                                                                                                                                            |
| 7    | `test ! -e src/app.py; echo $?`                                                                                                                  | The printed status is `0`. Glucose Log application files are not present.                                                                                                                                                                                                                                                                                       |


### TEST STEPS


| Step | Action                                                             | Expected result                                                                                                      |
| ---- | ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --packs house-policy --json --as-of "$AS_OF_DATE"` | JSON is printed. Ignore `digest`, `timestamp`, and `agent`. Verify the final result fields against Fig. 4. `outcome` is `findings`. `gate_id` is `HOUSE-ANTI-PLACEHOLDER`. |
| 2    | `echo $?`                                                          | The exit status is `1`.                                                                                              |


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

### Requirements

This case does not verify a specified requirement.

Other test basis:

- SDD §5.1 closed evaluator check algebra (`annex_file`, `file_present`, `anti_placeholder`, `npm_dep_ban`, `manifest_dep_ban`, `text_forbid`, `fresh`, `owned`).

EV-007 has eight independently executable variants, one per registered check kind. Each variant starts with `source tmp/verification-run.sh`. Do not keep the previous variant’s working tree. Variants A–C and G–H reuse existing R-states. Variants D–F start from R1 and apply a one-off uncommitted stimulus; they do not invent a new R-id. `fresh` and `owned` are not present in PF-01 production packs; those variants select PF-07 (`fresh-owned-test`).

| Variant | Check kind | Fail gate | Repository preparation |
| ------- | ---------- | --------- | ---------------------- |
| A | `file_present` | `HOUSE-SECURITY-MD` | [R2](../../docs2/testing/procedures/0_controlled_repo_setup.md#r2) |
| B | `annex_file` | `MD-SW-CLASS` | [R3](../../docs2/testing/procedures/0_controlled_repo_setup.md#r3) |
| C | `anti_placeholder` | `HOUSE-ANTI-PLACEHOLDER` | [R4](../../docs2/testing/procedures/0_controlled_repo_setup.md#r4) |
| D | `manifest_dep_ban` | `HOUSE-DEP-AXIOS-PIN` | R1 + axios@1.6.0 in `package.json` |
| E | `npm_dep_ban` | `CRA-DEP-AXIOS-PIN` | R1 + axios@1.6.0 in `package.json` |
| F | `text_forbid` | `HOUSE-SECRET-PATHS` | R1 + PEM marker lines in `SECURITY.md` |
| G | `fresh` | `FIX-FRESH-REVIEW` | [R6](../../docs2/testing/procedures/0_controlled_repo_setup.md#r6) |
| H | `owned` | `FIX-OWNED-POLICY` | [R7](../../docs2/testing/procedures/0_controlled_repo_setup.md#r7) |

### EV-007-A — `file_present`

#### SETUP

- Repository state: [R2](../../docs2/testing/procedures/0_controlled_repo_setup.md#r2) — prepared by `setup.sh` in step 3.
- Pack input: [PF-01](../../docs2/testing/procedures/1_pack_template_instantiation.md#pf-01) — selected by `verification-run.sh` through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-01](../../docs2/testing/procedures/0_controlled_repo_setup.md#ec-01) — established and verified by the setup steps below.

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. Otherwise, stop. |
| 2 | `cd "$REFERENCE_PRODUCT_ROOT"` | Current directory is `$REFERENCE_PRODUCT_ROOT`. |
| 3 | `./external_test/curbpack/setup.sh R2 --commit` | Applies R2. Prints the R2 state description (`SECURITY.md` absent). Otherwise, stop. |
| 4 | `git status --porcelain` | No output. Working tree is clean. |
| 5 | `ls SECURITY.md` | The file should be missing. |

#### TEST STEPS

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | `curbpack check --json --as-of "$AS_OF_DATE"` | JSON is printed. Ignore `digest`, `timestamp`, and `agent`. Verify the final result fields against Fig. 7A. `outcome` is `findings`. The only failure `gate_id` is `HOUSE-SECURITY-MD`. |
| 2 | `echo $?` | The exit status is `1`. |

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

**Fig. 7A.** Last fields after EV-007-A Step 1.

### EV-007-B — `annex_file`

#### SETUP

- Repository state: [R3](../../docs2/testing/procedures/0_controlled_repo_setup.md#r3) — prepared by `setup.sh` in step 3.
- Pack input: [PF-01](../../docs2/testing/procedures/1_pack_template_instantiation.md#pf-01) — selected by `verification-run.sh` through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-01](../../docs2/testing/procedures/0_controlled_repo_setup.md#ec-01) — established and verified by the setup steps below.

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. Otherwise, stop. |
| 2 | `cd "$REFERENCE_PRODUCT_ROOT"` | Current directory is `$REFERENCE_PRODUCT_ROOT`. |
| 3 | `./external_test/curbpack/setup.sh R3 --commit` | Applies R3. Prints the R3 state description (heading `## Classification Rationale` removed). Otherwise, stop. |
| 4 | `git status --porcelain` | No output. Working tree is clean. |
| 5 | `grep -F "## Classification Rationale" docs/medtech/software_safety_class.md` | NO output. |

#### TEST STEPS

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | `curbpack check --json --as-of "$AS_OF_DATE"` | JSON is printed. Ignore `digest`, `timestamp`, and `agent`. Verify against Fig. 7B. `outcome` is `findings`. The only failure `gate_id` is `MD-SW-CLASS`. |
| 2 | `echo $?` | The exit status is `1`. |

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

**Fig. 7B.** Last fields after EV-007-B Step 1.

### EV-007-C — `anti_placeholder`

#### SETUP

- Repository state: [R4](../../docs2/testing/procedures/0_controlled_repo_setup.md#r4) — prepared by `setup.sh` in step 3.
- Pack input: `house-policy` only (`--packs house-policy`). No PF-id.
- Execution configuration: [EC-01](../../docs2/testing/procedures/0_controlled_repo_setup.md#ec-01) — established and verified by the setup steps below.

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. Otherwise, stop. |
| 2 | `cd "$REFERENCE_PRODUCT_ROOT"` | Current directory is `$REFERENCE_PRODUCT_ROOT`. |
| 3 | `./external_test/curbpack/setup.sh R4 --commit` | Applies R4. Prints the R4 state description (token-only `SECURITY.md`, `package.json` name `acme-widget`). Otherwise, stop. |
| 4 | `git status --porcelain` | No output. Working tree is clean. |

#### TEST STEPS

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | `curbpack check --packs house-policy --json --as-of "$AS_OF_DATE"` | JSON is printed. Ignore `digest`, `timestamp`, and `agent`. Verify against Fig. 7C. `outcome` is `findings`. The only failure `gate_id` is `HOUSE-ANTI-PLACEHOLDER`. |
| 2 | `echo $?` | The exit status is `1`. |

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

**Fig. 7C.** Last fields after EV-007-C Step 1.

### EV-007-D — `manifest_dep_ban`

#### SETUP

- Repository state: [R1](../../docs2/testing/procedures/0_controlled_repo_setup.md#r1) — prepared by `setup.sh` in step 3. Step 5 adds a banned axios pin. That edit is stimulus, not a new R-id.
- Pack input: `house-policy` only (`--packs house-policy`). No PF-id.
- Execution configuration: [EC-01](../../docs2/testing/procedures/0_controlled_repo_setup.md#ec-01) for steps 3–4. After step 5 the working tree is dirty ([EC-02](../../docs2/testing/procedures/README.md#execution-configurations)).

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. Otherwise, stop. |
| 2 | `cd "$REFERENCE_PRODUCT_ROOT"` | Current directory is `$REFERENCE_PRODUCT_ROOT`. |
| 3 | `./external_test/curbpack/setup.sh R1 --commit` | Applies R1. Otherwise, stop. |
| 4 | `git status --porcelain` | No output. Working tree is clean. |
| 5 | Set `package.json` `dependencies` to `{ "axios": "1.6.0" }` with a JSON-preserving edit (for example `python3` rewriting the object). Leave the edit uncommitted. | `grep -F '"axios": "1.6.0"' package.json` prints the pin. `git status --porcelain` is non-empty. |

#### TEST STEPS

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | `curbpack check --packs house-policy --json --as-of "$AS_OF_DATE"` | JSON is printed. Ignore `digest`, `timestamp`, and `agent`. Verify against Fig. 7D. `outcome` is `findings`. The only failure `gate_id` is `HOUSE-DEP-AXIOS-PIN`. |
| 2 | `echo $?` | The exit status is `1`. |

```json
{
  "failures": [
    {
      "gate_id": "HOUSE-DEP-AXIOS-PIN",
      "severity": "critical",
      "type": "SYS_TRACE_VIOLATION",
      "sanitized_description": "House policy bans vulnerable axios@1.6.0 pins in package.json. (axios@1.6.0)",
      "ast_coordinates": {
        "target_file": "package.json",
        "node_path": "dependencies.axios",
        "target_symbol": "1.6.0",
        "fallback_lines": ""
      },
      "remediation": {
        "action_required": "Upgrade axios to a patched release and refresh the lockfile.",
        "expected_state": "No banned axios versions in dependencies or devDependencies."
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

**Fig. 7D.** Last fields after EV-007-D Step 1.

### EV-007-E — `npm_dep_ban`

#### SETUP

- Repository state: [R1](../../docs2/testing/procedures/0_controlled_repo_setup.md#r1) — prepared by `setup.sh` in step 3. Step 5 adds a banned axios pin. That edit is stimulus, not a new R-id.
- Pack input: `cra-baseline` only (`--packs cra-baseline`). Uses PF-01 pack files through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-01](../../docs2/testing/procedures/0_controlled_repo_setup.md#ec-01) for steps 3–4. After step 5 the working tree is dirty ([EC-02](../../docs2/testing/procedures/README.md#execution-configurations)).

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. Otherwise, stop. |
| 2 | `cd "$REFERENCE_PRODUCT_ROOT"` | Current directory is `$REFERENCE_PRODUCT_ROOT`. |
| 3 | `./external_test/curbpack/setup.sh R1 --commit` | Applies R1. Otherwise, stop. |
| 4 | `git status --porcelain` | No output. Working tree is clean. |
| 5 | Set `package.json` `dependencies` to `{ "axios": "1.6.0" }` with a JSON-preserving edit. Leave the edit uncommitted. | `grep -F '"axios": "1.6.0"' package.json` prints the pin. `git status --porcelain` is non-empty. |

#### TEST STEPS

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | `curbpack check --packs cra-baseline --json --as-of "$AS_OF_DATE"` | JSON is printed. Ignore `digest`, `timestamp`, and `agent`. Verify against Fig. 7E. `outcome` is `findings`. The only failure `gate_id` is `CRA-DEP-AXIOS-PIN`. |
| 2 | `echo $?` | The exit status is `1`. |

```json
{
  "failures": [
    {
      "gate_id": "CRA-DEP-AXIOS-PIN",
      "severity": "critical",
      "type": "SYS_TRACE_VIOLATION",
      "sanitized_description": "Vulnerable axios@1.6.0 pin detected in package.json. (axios@1.6.0)",
      "ast_coordinates": {
        "target_file": "package.json",
        "node_path": "dependencies.axios",
        "target_symbol": "1.6.0",
        "fallback_lines": ""
      },
      "remediation": {
        "action_required": "Upgrade axios to a patched release (>=1.8.4 recommended) and refresh the lockfile.",
        "expected_state": "Dependency tree free of listed unmitigated axios pins."
      }
    }
  ],
  "pack_id": "cra-baseline",
  "readiness_score": 80,
  "outcome": "findings",
  "failed_rules": 1,
  "evaluated_rules": 6,
  "conformity_claim": "none"
}
```

**Fig. 7E.** Last fields after EV-007-E Step 1.

### EV-007-F — `text_forbid`

#### SETUP

- Repository state: [R1](../../docs2/testing/procedures/0_controlled_repo_setup.md#r1) — prepared by `setup.sh` in step 3. Step 5 appends PEM marker lines to `SECURITY.md`. That edit is stimulus, not a new R-id. The marker is fixture text only.
- Pack input: `house-policy` only (`--packs house-policy`). No PF-id.
- Execution configuration: [EC-01](../../docs2/testing/procedures/0_controlled_repo_setup.md#ec-01) for steps 3–4. After step 5 the working tree is dirty ([EC-02](../../docs2/testing/procedures/README.md#execution-configurations)).

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. Otherwise, stop. |
| 2 | `cd "$REFERENCE_PRODUCT_ROOT"` | Current directory is `$REFERENCE_PRODUCT_ROOT`. |
| 3 | `./external_test/curbpack/setup.sh R1 --commit` | Applies R1. Otherwise, stop. |
| 4 | `git status --porcelain` | No output. Working tree is clean. |
| 5 | `printf '%s\n' '' '-----BEGIN RSA PRIVATE KEY-----' 'fixture-only' '-----END RSA PRIVATE KEY-----' >> SECURITY.md` | `grep -F -- '-----BEGIN RSA PRIVATE KEY-----' SECURITY.md` prints the marker. `git status --porcelain` lists `SECURITY.md`. |

#### TEST STEPS

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | `curbpack check --packs house-policy --json --as-of "$AS_OF_DATE"` | JSON is printed. Ignore `digest`, `timestamp`, and `agent`. Verify against Fig. 7F. `outcome` is `findings`. The only failure `gate_id` is `HOUSE-SECRET-PATHS`. |
| 2 | `echo $?` | The exit status is `1`. |

```json
{
  "failures": [
    {
      "gate_id": "HOUSE-SECRET-PATHS",
      "severity": "critical",
      "type": "POLICY_VIOLATION",
      "sanitized_description": "Likely secrets or private key material found in tracked policy docs or common agent secret paths. (forbidden pattern matched)",
      "ast_coordinates": {
        "target_file": "SECURITY.md",
        "node_path": "",
        "target_symbol": "",
        "fallback_lines": ""
      },
      "remediation": {
        "action_required": "Remove credentials from docs and agent-oops paths; rotate any exposed secrets; use a secret manager.",
        "expected_state": "No secret-like patterns in house policy document paths or common agent secret files."
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

**Fig. 7F.** Last fields after EV-007-F Step 1.

### EV-007-G — `fresh`

#### SETUP

- Repository state: [R6](../../docs2/testing/procedures/0_controlled_repo_setup.md#r6) — prepared by `setup.sh` in step 3.
- Pack input: [PF-07](../../docs2/testing/procedures/1_pack_template_instantiation.md) (`fresh-owned-test`). Selected by SETUP step 7. Not an R-id.
- Execution configuration: [EC-01](../../docs2/testing/procedures/0_controlled_repo_setup.md#ec-01) — established and verified by the setup steps below.

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. Otherwise, stop. |
| 2 | `cd "$REFERENCE_PRODUCT_ROOT"` | Current directory is `$REFERENCE_PRODUCT_ROOT`. |
| 3 | `./external_test/curbpack/setup.sh R6 --commit` | Applies R6. Prints the R6 state description (stale Owner-dated `docs/review-log.md` and `docs/owned-policy.md`). Otherwise, stop. |
| 4 | `git status --porcelain` | No output. Working tree is clean. |
| 5 | `test -f docs/review-log.md && test -f docs/owned-policy.md; echo $?` | The printed status is `0`. |
| 6 | `git log -1 --format='%ae %aI' -- docs/review-log.md` | The line starts with `owner@example.com 2022-01-01T00:00:00`. |
| 7 | `./external_test/curbpack/mutate_pack.sh PF-07` | Prints `mutate_pack.sh: PF-07` and installs `fresh-owned-test/pack.json`. `CURBPACK_PACKS_DIR` stays the verification-run value. Later `curbpack check` loads `fresh-owned-test` with `--packs`. |

#### TEST STEPS

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | `curbpack check --packs fresh-owned-test --json --as-of "$AS_OF_DATE"` | JSON is printed. Ignore `digest`, `timestamp`, and `agent`. Verify against Fig. 7G. `outcome` is `findings`. The only failure `gate_id` is `FIX-FRESH-REVIEW`. |
| 2 | `echo $?` | The exit status is `1`. |

```json
{
  "failures": [
    {
      "gate_id": "FIX-FRESH-REVIEW",
      "severity": "medium",
      "type": "POLICY_VIOLATION",
      "sanitized_description": "Review log must be updated within max_age_days. (fresh: last commit 2022-01-01T00:00:00Z older than 365 days)",
      "ast_coordinates": {
        "target_file": "docs/review-log.md",
        "node_path": "",
        "target_symbol": "",
        "fallback_lines": ""
      },
      "remediation": {
        "action_required": "Commit an updated docs/review-log.md.",
        "expected_state": "Review log commit is within freshness window."
      }
    }
  ],
  "pack_id": "fresh-owned-test",
  "readiness_score": 80,
  "outcome": "findings",
  "failed_rules": 1,
  "evaluated_rules": 2,
  "conformity_claim": "none"
}
```

**Fig. 7G.** Last fields after EV-007-G Step 1. Requires `$AS_OF_DATE` on or after `2023-01-02` so the 2022-01-01 commit is outside `max_age_days: 365`.

### EV-007-H — `owned`

#### SETUP

- Repository state: [R7](../../docs2/testing/procedures/0_controlled_repo_setup.md#r7) — prepared by `setup.sh` in step 3.
- Pack input: [PF-07](../../docs2/testing/procedures/1_pack_template_instantiation.md) (`fresh-owned-test`). Selected by SETUP step 7. Not an R-id.
- Execution configuration: [EC-01](../../docs2/testing/procedures/0_controlled_repo_setup.md#ec-01) — established and verified by the setup steps below.

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. Otherwise, stop. |
| 2 | `cd "$REFERENCE_PRODUCT_ROOT"` | Current directory is `$REFERENCE_PRODUCT_ROOT`. |
| 3 | `./external_test/curbpack/setup.sh R7 --commit` | Applies R7. Prints the R7 state description (Wrong Author-dated `docs/review-log.md` and `docs/owned-policy.md`). Otherwise, stop. |
| 4 | `git status --porcelain` | No output. Working tree is clean. |
| 5 | `test -f docs/review-log.md && test -f docs/owned-policy.md; echo $?` | The printed status is `0`. |
| 6 | `git log -1 --format='%ae %aI' -- docs/owned-policy.md` | The line starts with `wrong@example.com 2026-09-13T12:00:00`. |
| 7 | `./external_test/curbpack/mutate_pack.sh PF-07` | Prints `mutate_pack.sh: PF-07` and installs `fresh-owned-test/pack.json`. `CURBPACK_PACKS_DIR` stays the verification-run value. Later `curbpack check` loads `fresh-owned-test` with `--packs`. |

#### TEST STEPS

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | `curbpack check --packs fresh-owned-test --json --as-of "$AS_OF_DATE"` | JSON is printed. Ignore `digest`, `timestamp`, and `agent`. Verify against Fig. 7H. `outcome` is `findings`. The only failure `gate_id` is `FIX-OWNED-POLICY`. |
| 2 | `echo $?` | The exit status is `1`. |

```json
{
  "failures": [
    {
      "gate_id": "FIX-OWNED-POLICY",
      "severity": "high",
      "type": "POLICY_VIOLATION",
      "sanitized_description": "Owned policy draft must mention repo token and match author email. (owned: last commit author email \"wrong@example.com\" want \"owner@example.com\")",
      "ast_coordinates": {
        "target_file": "docs/owned-policy.md",
        "node_path": "",
        "target_symbol": "",
        "fallback_lines": ""
      },
      "remediation": {
        "action_required": "Edit docs/owned-policy.md with product token; commit as owner@example.com.",
        "expected_state": "Repo-bound draft with expected git author on last commit."
      }
    }
  ],
  "pack_id": "fresh-owned-test",
  "readiness_score": 80,
  "outcome": "findings",
  "failed_rules": 1,
  "evaluated_rules": 2,
  "conformity_claim": "none"
}
```

**Fig. 7H.** Last fields after EV-007-H Step 1.

---

## EV-008 — Verify that outcome does not depend on rule order or file order

### Requirements

This case does not verify a specified requirement.

Other test basis:

- SDD §2.3: outcome must not depend on rule order or file order. This is not MUST-32 (digest field total ordering).
- SDD MUST-31: evaluation input excludes filesystem order; pack bytes remain an explicit input, so a changed pack byte hash or evaluation digest is expected when pack rule order changes and must not fail this case.

EV-008 has two variants. Each starts with `source tmp/verification-run.sh`. Do not keep the previous variant’s working tree.

| Variant | Claim under test | Status |
| ------- | ---------------- | ------ |
| A | Outcome is independent of pack rule order | Executable |
| B | Outcome is independent of filesystem file enumeration order | Blocked — missing test seam |

### EV-008-A — rule order

Two logically equivalent packs declare the same two `file_present` rules with opposite rule-array order:

- [PF-08](../../docs2/testing/procedures/1_pack_template_instantiation.md) (`EV008-ALPHA` then `EV008-BETA`)
- [PF-09](../../docs2/testing/procedures/1_pack_template_instantiation.md) (`EV008-BETA` then `EV008-ALPHA`)

Run each pack against an independently restored R1 checkout. Compare exit status, `outcome`, `conformity_claim`, and the normalized set of finding identities `(gate_id, sanitized_description, target_file)`. Do not require raw JSON byte identity, identical `failures` array order, or identical digests.

#### SETUP (pack A)

- Repository state: [R1](../../docs2/testing/procedures/0_controlled_repo_setup.md#r1) — prepared by `setup.sh` in step 3.
- Pack input: [PF-08](../../docs2/testing/procedures/1_pack_template_instantiation.md). Selected by SETUP step 5. Not an R-id.
- Execution configuration: [EC-01](../../docs2/testing/procedures/0_controlled_repo_setup.md#ec-01) — established and verified by the setup steps below.

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. Otherwise, stop. |
| 2 | `cd "$REFERENCE_PRODUCT_ROOT"` | Current directory is `$REFERENCE_PRODUCT_ROOT`. |
| 3 | `./external_test/curbpack/setup.sh R1 --commit` | Applies R1. Otherwise, stop. |
| 4 | `git status --porcelain` | No output. Working tree is clean. |
| 5 | `./external_test/curbpack/mutate_pack.sh PF-08` | Prints `mutate_pack.sh: PF-08` and installs `ev-008-rule-order-a/pack.json`. `CURBPACK_PACKS_DIR` stays the verification-run value. |
| 6 | `test ! -e docs/ev008-alpha.md && test ! -e docs/ev008-beta.md; echo $?` | The printed status is `0`. Both targets are absent. |

#### TEST STEPS (pack A)

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | `curbpack check --packs ev-008-rule-order-a --json --as-of "$AS_OF_DATE"` | JSON is printed. Ignore `digest`, `timestamp`, `agent`, and `statechart_context`. `outcome` is `findings`. `conformity_claim` is `none`. `failed_rules` is `2`. `evaluated_rules` is `2`. `failures` contains exactly `EV008-ALPHA` and `EV008-BETA`. Save this JSON as observation A. |
| 2 | `echo $?` | The exit status is `1`. |

#### SETUP (pack B)

Repeat SETUP steps 1–4 on a newly sourced restore. Then `./external_test/curbpack/mutate_pack.sh PF-09` and repeat SETUP step 6. Do not reuse the pack-A checkout. Pack input is [PF-09](../../docs2/testing/procedures/1_pack_template_instantiation.md).

#### TEST STEPS (pack B)

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | `curbpack check --packs ev-008-rule-order-b --json --as-of "$AS_OF_DATE"` | JSON is printed. Ignore `digest`, `timestamp`, `agent`, and `statechart_context`. `outcome` is `findings`. `conformity_claim` is `none`. `failed_rules` is `2`. `evaluated_rules` is `2`. `failures` contains exactly `EV008-ALPHA` and `EV008-BETA`. Save this JSON as observation B. |
| 2 | `echo $?` | The exit status is `1`. |
| 3 | Compare observation A with observation B. | Exit statuses are both `1`. `outcome` and `conformity_claim` match. The normalized finding set `(gate_id, sanitized_description, target_file)` is identical. A different `failures` array order is allowed. A different pack id, pack byte hash, or evaluation digest is expected and must not fail this case. |

Controlled observation: pack A emitted findings in order `EV008-ALPHA`, `EV008-BETA`; pack B emitted `EV008-BETA`, `EV008-ALPHA`. The normalized sets matched. Digests differed.

### EV-008-B — file order

#### Status

Blocked. Do not run this variant.

#### Missing test seam

The evaluator walks `composed.Rules` and each rule’s declared `path` / `paths`. Check outcomes are not produced by a controllable filesystem enumeration of the repository tree. `MUST-31` already excludes filesystem order from evaluation input, but the public check API provides no way to present two different pre-normalization filesystem enumeration orders to the evaluator and observe that difference.

Creating files in a different write sequence does not demonstrate different evaluator input order. Marking this variant executable would require a production seam that does not exist. Do not modify Curbpack implementation merely to make this variant runnable.

---

## EV-009 — Verify that thin rule-satisfying text yields a pass without a substance claim

### Requirements

This case does not verify a specified requirement.

Other test basis:

- Documented product claim: Curbpack evaluates declared structural conditions and prepares evidence for human review; it does not establish claim truth or conformity.

### SETUP

- Repository state: [R5](../../docs2/testing/procedures/0_controlled_repo_setup.md#r5) — prepared by `setup.sh` in step 3.
- Pack input: `house-policy` only (`--packs house-policy`). No PF-id.
- Execution configuration: [EC-01](../../docs2/testing/procedures/0_controlled_repo_setup.md#ec-01) — established and verified by the setup steps below.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R5 --commit`                                                                                                  | Applies R5 to the already-restored frozen baseline. Does not restore the baseline. Prints the R5 state description (thin real `SECURITY.md`, original demo-app `package.json`). Otherwise, stop. HEAD is a local `test_*` branch. This step does not create `$CURBPACK_ROOT/tmp/R5`.                                                                            |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `grep -F '"name": "demo-app"' package.json`                                                                                                      | The line is printed.                                                                                                                                                                                                                                                                                                                                            |
| 6    | `grep -F 'warehouse controller firmware' SECURITY.md`                                                                                            | The line is printed.                                                                                                                                                                                                                                                                                                                                            |
| 7    | `test ! -e src/app.py; echo $?`                                                                                                                  | The printed status is `0`. Glucose Log application files are not present.                                                                                                                                                                                                                                                                                       |


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
