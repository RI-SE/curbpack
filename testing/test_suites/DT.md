# DT — Determinism and finding identity

## Objective

Equivalent inputs in scope of the selected pack must produce equivalent
semantic results and stable finding identities. Controlled changes should
affect only expected findings or explicitly dependent fields.

## Test basis

Requirements addressed by this suite:

- MUST-30
- MUST-31

Other test basis:

- SDD §7.3 deterministic-behavior and exact-evidence expectations.

A test execution is always part of a test run that starts with [Prepare a verification run](../../docs2/testing/procedures/README.md).
In short it encompasses cloning the reference product into `<curbpack>/tmp/cyberready-test-product`,
using the recorded `<commit hash>` and `<date>`, and building the CLI. This is done once for a test run.

Each executable case starts the same way: from the Curbpack root, `source tmp/verification-run.sh`. That restore puts the disposable reference product back at the frozen baseline. You can run the cases in any order. Do not keep using the previous case’s directory. Then prepare the case’s named R-state: R1 or R2 via product `setup.sh` on that already-restored baseline. Then apply EC as the case states. DT-001, DT-003, and DT-004 write JSON under Curbpack `tmp/dt-001`, `tmp/dt-003`, and `tmp/dt-004`. Those directories are evidence. They are not an R-id and not a `tmp/R*` repository. DT-003 prepares R1, retains one check JSON, then prepares R2 on the same checkout. TEST STEPS consume R2.

## Test suite overview


| ID     | Test case / purpose                                      | Requirements addressed | Test class | Procedure status |
| ------ | -------------------------------------------------------- | ---------------------- | ---------- | ---------------- |
| DT-001 | Repeatability of identical inputs                        | MUST-30                | A          | Executable       |
| DT-002 | Locale and timezone variation                            | MUST-31                | B          | To be specified  |
| DT-003 | Controlled change sensitivity                            | —                      | A          | Executable       |
| DT-004 | Finding identity stability                               | —                      | A          | Executable       |


---

## DT-001 — Verify that identical inputs produce the same semantic result

### Requirements

- MUST-30

This case compares semantic result fields and exit status across 20 identical
R1 / PF-01 / EC-01 runs. It does not compare byte-identical canonical
evaluation bytes. See INV-04 in [SDD §8](../../docs/software-design-document.md)
(Failing; evaluation and receipt not separated). A pass does not close MUST-30.

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
| 5    | `mkdir -p "$CURBPACK_ROOT/tmp/dt-001"`                                                                                                           | The directory exists. It is evidence storage under the verification-run `tmp/`. It is not an R-id and not a Git repository.                                                                                                                                                                                                                                     |


### TEST STEPS


| Step | Action                                                                                                                                                                                                                                                                                                                                                      | Expected result                                                                                                                                                                                                                                                                                                                                 |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `i=1; while [ "$i" -le 20 ]; do curbpack check --json --as-of "$AS_OF_DATE" > "$CURBPACK_ROOT/tmp/dt-001/run-$i.json"; echo $? > "$CURBPACK_ROOT/tmp/dt-001/run-$i.exit"; jq -r '.evaluation_digest' .github/curbpack/cache/latest_receipt.json > "$CURBPACK_ROOT/tmp/dt-001/run-$i.evaluation_digest"; i=$((i+1)); done` | Each of the 20 commands writes JSON to its file. Each `run-*.exit` file contains `0`. Each `run-*.evaluation_digest` file contains the receipt `evaluation_digest` (non-empty, not `null`). The stdout evaluation object has no `digest` field; the current contract binds `evaluation_digest` on the receipt. Ignore `timestamp`, `agent`, and `statechart_context`. Verify the final result fields of each file against Fig. 1. |
| 2    | Compare `failures`, `pack_id`, `outcome`, `readiness_score`, `evaluated_rules`, and `conformity_claim` across the 20 JSON files. Compare the 20 exit files. Compare the 20 `evaluation_digest` files. | Those fields are the same in every JSON file. Every exit status is `0`. `timestamp` and `agent` may differ. That is not a semantic difference. Record whether `evaluation_digest` is identical. A missing or empty `evaluation_digest` fails this case. A difference in `evaluation_digest` alone does not fail this case. |


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

**Fig. 1.** Example of the last fields after each run in Step 1. Same R1 / PF-01 / EC-01 check as EV-001.

Empty lists in this JSON are encoded as `null`, not `[]`. This applies to both `failures` and `failed_orthogonal_regions`. A successful result has `"outcome": "pass"` and no failure objects under `failures`.

---

## DT-002 — Verify that locale and timezone variation does not change the result

### Requirements

- MUST-31

This case is the locale and timezone slice of MUST-31’s exclude clause.
[EC-07](../../docs2/testing/procedures/README.md#execution-configurations) is not yet specified.
Do not invent that procedure here. A pass cannot close MUST-31 because the
case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## DT-003 — Verify that a controlled change affects only expected findings

### Requirements

This case does not verify a specified requirement.

Other test basis:

- SDD §7.3 deterministic-behavior and exact-evidence expectations.

The same R1 / PF-01 / EC-01 check output may support EV-001, and the same R2
check may support EV-002, but DT-003 can be run independently using these
steps.

### SETUP

- Repository state: [R1](../../docs2/testing/procedures/0_controlled_repo_setup.md#r1) then [R2](../../docs2/testing/procedures/0_controlled_repo_setup.md#r2) — R1 prepared by `setup.sh` in step 3; R2 prepared by `setup.sh` in step 7 after the R1 JSON is retained. TEST STEPS consume R2.
- Pack input: [PF-01](../../docs2/testing/procedures/1_pack_template_instantiation.md#pf-01) — selected by `verification-run.sh` through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-01](../../docs2/testing/procedures/0_controlled_repo_setup.md#ec-01) — established and verified by steps 3–4 for R1 and by steps 7–8 for R2.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R1 --commit`                                                                                                  | Applies R1 to the already-restored frozen baseline. Does not restore the baseline. Prints the R1 state description (required files, heading, `package.json` conditions). Otherwise, stop.                                                                                                                                                                       |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `mkdir -p "$CURBPACK_ROOT/tmp/dt-003"`                                                                                                           | The directory exists. It is evidence storage under the verification-run `tmp/`. It is not an R-id and not a Git repository.                                                                                                                                                                                                                                     |
| 6    | `curbpack check --json --as-of "$AS_OF_DATE" > "$CURBPACK_ROOT/tmp/dt-003/r1.json"; echo $? > "$CURBPACK_ROOT/tmp/dt-003/r1.exit"`                 | JSON is written. The exit file contains `0`. Ignore `digest`, `timestamp`, `agent`, and `statechart_context`. Verify the final result fields against Fig. 1. This retained R1 JSON is declared evidence, not the TEST STEPS stimulus. Otherwise, stop.                                                                                                          |
| 7    | `./external_test/curbpack/setup.sh R2 --commit`                                                                                                  | Applies R2. Does not restore the baseline. Prints the R2 state description (`SECURITY.md` absent, not empty). Otherwise, stop. HEAD is a local `test_*` branch.                                                                                                                                                                                                 |
| 8    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 9    | `ls SECURITY.md`                                                                                                                                 | The file should be missing.                                                                                                                                                                                                                                                                                                                                     |


### TEST STEPS


| Step | Action                                                                                                                            | Expected result                                                                                                                                                                                                                                                                                                                                 |
| ---- | --------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --json --as-of "$AS_OF_DATE" > "$CURBPACK_ROOT/tmp/dt-003/r2.json"`                                                | JSON is written. Ignore `digest`, `timestamp`, and `agent`. Verify the final result fields against Fig. 2. `outcome` is `findings`, not `pass`. The `SECURITY.md` check is not represented as passed.                                                                                                                                           |
| 2    | `echo $?`                                                                                                                         | The exit status is `1`.                                                                                                                                                                                                                                                         |
| 3    | Compare `$CURBPACK_ROOT/tmp/dt-003/r1.json` with `$CURBPACK_ROOT/tmp/dt-003/r2.json`                                               | Only the expected finding and fields that depend on it change. `failures`, `outcome`, `readiness_score`, and `failed_rules` differ as Fig. 1 vs Fig. 2. `pack_id`, `evaluated_rules`, and `conformity_claim` are the same. Ignore `digest`, `timestamp`, `agent`, and `statechart_context`.                                                     |


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

**Fig. 2.** Example of the last fields after Step 1. Same R2 / PF-01 / EC-01 check as EV-002.

---

## DT-004 — Verify that finding identity is stable under equivalent runs

### Requirements

This case does not verify a specified requirement.

Other test basis:

- SDD §7.3 deterministic-behavior and exact-evidence expectations.

The retained results may come from DT-001 and DT-003 on this same frozen
baseline. To prepare them without those cases, use the setup steps below.

Finding identity in `check --json` is `failures[].gate_id`. Do not invent a
separate finding-id field.

### SETUP

- Repository state: [R1](../../docs2/testing/procedures/0_controlled_repo_setup.md#r1) then [R2](../../docs2/testing/procedures/0_controlled_repo_setup.md#r2) — R1 prepared by `setup.sh` in step 3; R2 prepared by `setup.sh` in step 7 after the 20 R1 JSON files are retained. TEST STEPS compare retained files.
- Pack input: [PF-01](../../docs2/testing/procedures/1_pack_template_instantiation.md#pf-01) — selected by `verification-run.sh` through `CURBPACK_PACKS_DIR`.
- Execution configuration: [EC-01](../../docs2/testing/procedures/0_controlled_repo_setup.md#ec-01) — established and verified by steps 3–4 for R1 and by steps 7–8 for R2.

If `$CURBPACK_ROOT/tmp/dt-001/run-1.json` through `run-20.json` and
`$CURBPACK_ROOT/tmp/dt-003/r2.json` already exist from this same frozen
baseline (`CURBPACK_COMMIT`, `REFERENCE_PRODUCT_COMMIT`, `AS_OF_DATE`),
copy `run-$i.json` to `$CURBPACK_ROOT/tmp/dt-004/r1-run-$i.json` and copy
`r2.json` to `$CURBPACK_ROOT/tmp/dt-004/r2.json`, then skip steps 6–10.
Otherwise use every step.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R1 --commit`                                                                                                  | Applies R1 to the already-restored frozen baseline. Does not restore the baseline. Prints the R1 state description (required files, heading, `package.json` conditions). Otherwise, stop.                                                                                                                                                                       |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `mkdir -p "$CURBPACK_ROOT/tmp/dt-004"`                                                                                                           | The directory exists. It is evidence storage under the verification-run `tmp/`. It is not an R-id and not a Git repository.                                                                                                                                                                                                                                     |
| 6    | `i=1; while [ "$i" -le 20 ]; do curbpack check --json --as-of "$AS_OF_DATE" > "$CURBPACK_ROOT/tmp/dt-004/r1-run-$i.json"; echo $? > "$CURBPACK_ROOT/tmp/dt-004/r1-run-$i.exit"; i=$((i+1)); done`                               | Each of the 20 commands writes JSON. Each exit file contains `0`. Ignore `digest`, `timestamp`, `agent`, and `statechart_context`. Verify the final result fields of each file against Fig. 1. Otherwise, stop.                                                                                                                                                 |
| 7    | `./external_test/curbpack/setup.sh R2 --commit`                                                                                                  | Applies R2. Does not restore the baseline. Prints the R2 state description (`SECURITY.md` absent, not empty). Otherwise, stop. HEAD is a local `test_*` branch.                                                                                                                                                                                                 |
| 8    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 9    | `ls SECURITY.md`                                                                                                                                 | The file should be missing.                                                                                                                                                                                                                                                                                                                                     |
| 10   | `curbpack check --json --as-of "$AS_OF_DATE" > "$CURBPACK_ROOT/tmp/dt-004/r2.json"; echo $? > "$CURBPACK_ROOT/tmp/dt-004/r2.exit"`                 | JSON is written. The exit file contains `1`. Ignore `digest`, `timestamp`, and `agent`. Verify the final result fields against Fig. 2. Otherwise, stop.                                                                                                                                                                                                         |


### TEST STEPS


| Step | Action                                                                                                                         | Expected result                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Compare `failures[].gate_id` across `$CURBPACK_ROOT/tmp/dt-004/r1-run-1.json` through `r1-run-20.json`                          | The identifier list is the same in every file. On this R1, `failures` is `null`. There is no finding identifier.                                                                                                |
| 2    | Compare those R1 identifiers with `failures[].gate_id` in `$CURBPACK_ROOT/tmp/dt-004/r2.json`                                   | Identifiers change only where a documented identity input changed (`SECURITY.md` missing). R2 has `gate_id` `HOUSE-SECURITY-MD`. R1 does not. No other `gate_id` appears or disappears.                         |


---

## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
  this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
  directly contradicts the suite objective. Unexplained semantic differences
  or unstable finding identities for equivalent inputs are failures.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
  unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.
