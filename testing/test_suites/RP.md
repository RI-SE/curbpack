# RP — Review Pack, output, and attestation integrity

## Objective

Human-facing output and Review Packs must not omit, reverse or soften material
machine-readable findings or add unsupported assurance. Automation or
generated material must not create, infer or overwrite human approval or be
treated as reviewed evidence without the required deterministic re-check and
human review.

## Test basis

Requirements addressed by this suite:

- MUST-02
- MUST-04
- MUST-71
- MUST-72

Other test basis:

- SDD §1 file-based publisher–producer–reviewer exchange model.
- SDD §3.3 independent verification boundary.

A test execution is always part of a test run that starts with [Prepare a verification run](../../docs2/testing/procedures/README.md).
In short it encompasses cloning the reference product into `<curbpack>/tmp/cyberready-test-product`,
using the recorded `<commit hash>` and `<date>`, and building the CLI. This is done once for a test run.

Each executable case starts the same way: from the Curbpack root, `source tmp/verification-run.sh`. That restore puts the disposable reference product back at the frozen baseline. You can run the cases in any order. Do not keep using the previous case’s directory. RP-001 and RP-002 then prepare R1 or R2 via product `setup.sh` on that already-restored baseline. RP-003 to RP-005 select PF-10, PF-11, or PF-12 with `mutate_pack.sh` and review the installed files under `external_test/curbpack/review-pack-input/`. They do not create an R-id or a `tmp/R*` repository.

## Test suite overview


| ID     | Test case / purpose                                          | Requirements addressed | Test class | Procedure status |
| ------ | ------------------------------------------------------------ | ---------------------- | ---------- | ---------------- |
| RP-001 | Machine-to-human consistency, clean result                   | MUST-02, MUST-04       | A          | Executable       |
| RP-002 | Machine-to-human consistency, failed result                  | MUST-02, MUST-04       | A          | Executable       |
| RP-003 | Tampered machine result or substituted state                 | —                      | A          | Executable       |
| RP-004 | Removed finding from executive summary                       | —                      | A          | Executable       |
| RP-005 | Incomplete or truncated Review Pack file                     | —                      | A          | Executable       |
| RP-006 | Human attestation boundary                                   | MUST-72                | C          | To be specified  |
| RP-007 | Generated proposal or automated edit                         | MUST-71                | C          | To be specified  |


---

## RP-001 — Verify that a clean machine result is represented consistently in the Review Pack

### Requirements

- MUST-02
- MUST-04

Passing this case does not close MUST-02: the exact boundary sentence is not
required on every buyer/reviewer artefact. Passing this case does not close
MUST-04: signatures and every scoped score or status are not covered.

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


| Step | Action                                         | Expected result                                                                                                                                                                                                                                                                                                                                 |
| ---- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --json --as-of "$AS_OF_DATE"`  | The command completes successfully. Ignore `digest`, `timestamp`, `agent`, and `statechart_context`. Verify the final result fields against the expected values shown in Fig. 1.                                                                                                                                                                |
| 2    | `echo $?`                                      | The exit status is `0`.                                                                                                                                                                                                                                                                                                                         |
| 3    | `curbpack share --as-of "$AS_OF_DATE"`         | The command completes. `review-pack/` is created under `$REFERENCE_PRODUCT_ROOT`. At least `01-gate-failures.json`, `02-action-report.md`, `03-executive-summary.md`, and `buyer-onepager.html` are present.                                                                                                                                   |
| 4    | `echo $?`                                      | The exit status is `0`.                                                                                                                                                                                                                                                                                                                         |
| 5    | Compare `review-pack/01-gate-failures.json` to Fig. 1 | Same `pack_id`, `outcome`, `readiness_score`, `evaluated_rules`, and `failures`. Ignore `digest`, `timestamp`, and `agent`. The Review Pack does not turn this pass into a fail.                                                                                                                                                               |
| 6    | Read `review-pack/03-executive-summary.md` and `review-pack/buyer-onepager.html` | Pack identity matches Fig. 1. Open-findings count is `0` or the text states that selected checks passed. The files do not add CE marking, certification, notified-body approval, or a broader product verdict. Summarisation does not add unsupported assurance. Automated pack-identity and open-findings checks remain. Claim-language assessment is MANUAL: a `certification` keyword check matches the disclaimer “not certification” and is not treated as a product fail. |


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

**Fig. 1.** Example of the last fields after Step 1. Same R1 / PF-01 / EC-01 check as EV-001.

Empty lists in this JSON are encoded as `null`, not `[]`. This applies to both `failures` and `failed_orthogonal_regions`. A successful result has `"outcome": "pass"` and no failure objects under `failures`.

---

## RP-002 — Verify that a failed machine result is not omitted, reversed, or softened in the Review Pack

### Requirements

- MUST-02
- MUST-04

Passing this case does not close MUST-02: the exact boundary sentence is not
required on every buyer/reviewer artefact. Passing this case does not close
MUST-04: signatures and every scoped score or status are not covered.

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
| 3    | `curbpack share --as-of "$AS_OF_DATE"`        | `review-pack/` is created under `$REFERENCE_PRODUCT_ROOT` from the same declared date. The fail is still written.                                                                                      |
| 4    | `echo $?`                                     | The exit status is `1`. Share exits non-zero because check is red. That is expected. Do not treat it as a missing Review Pack.                                                                        |
| 5    | Compare `HOUSE-SECURITY-MD` in Fig. 2 with `review-pack/01-gate-failures.json`, `review-pack/02-action-report.md`, and `review-pack/03-executive-summary.md` | The gate id is present in the JSON and in the human-facing files. The fail is not omitted, reversed, or softened into a pass. |


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

## RP-003 — Verify that a tampered machine result is not trusted as the original pass

### Requirements

This case does not verify a specified requirement.

Other test basis:

- SDD §3.3 independent verification boundary.

Observed: `curbpack review` does not contradict when `expected_parent_commit_sha`
in `01-gate-failures.json` is replaced. The substitution is visible by comparing
JSON `subject_commit` with the one-pager `Commit` line. A pass on this case
means that comparison is made. It does not mean the product enforced the
mismatch.

### SETUP

- Repository state: no R-id. Disposable reference-product checkout after `verification-run.sh`.
- Pack input: [PF-10](../../docs2/testing/procedures/1_pack_template_instantiation.md) — selected by SETUP step 2.
- Execution configuration: no EC-id.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"` && `./external_test/curbpack/mutate_pack.sh PF-10`                                                                 | Prints `mutate_pack.sh: PF-10` and installs the prepared Review Pack under `external_test/curbpack/review-pack-input/`. It is not a Git repository and not an R-id.                                                                                                                                                                                            |
| 3    | `grep expected_parent_commit_sha "$REFERENCE_PRODUCT_ROOT/external_test/curbpack/review-pack-input/01-gate-failures.json"`                        | The JSON field is `"expected_parent_commit_sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"`.                                                                                                                                                                                                                                                                 |
| 4    | `grep Commit "$REFERENCE_PRODUCT_ROOT/external_test/curbpack/review-pack-input/buyer-onepager.html"`                                              | The one-pager still shows `aaaaaaaaaaaa…`. Do not edit this file.                                                                                                                                                                                                                                                                                               |


### TEST STEPS


| Step | Action                                                      | Expected result                                                                                                                                                                                                                                                                                                                                 |
| ---- | ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack review --json "$REFERENCE_PRODUCT_ROOT/external_test/curbpack/review-pack-input"`   | JSON is printed. stderr contains `Offline document triage — not a product verdict.` Ignore `record_digest`. Verify the stable fields against Fig. 3. `contradicted_count` is `0`. `subject_commit` is 40 `b` characters. The product does not flag the SHA substitution.                                                                        |
| 2    | `echo $?`                                                   | The exit status is `0`.                                                                                                                                                                                                                                                                                                                         |
| 3    | Compare JSON `subject_commit` from Step 1 with the `Commit` line in `$REFERENCE_PRODUCT_ROOT/external_test/curbpack/review-pack-input/buyer-onepager.html` | They do not match (`bbbbbbbb…` vs `aaaaaaaaaaaa…`). Do not treat this folder as the original sample pass. |


```json
{
  "schema": "curbpack-review-report:2",
  "subject_commit": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "confirmed_count": 9,
  "unconfirmed_count": 10,
  "contradicted_count": 0
}
```

**Fig. 3.** Example of stable fields after Step 1. `contradicted_count` is `0`. The mismatch is in `subject_commit` versus the one-pager, not in a contradicted finding.

---

## RP-004 — Verify that a removed finding in the summary is visible against the machine result

### Requirements

This case does not verify a specified requirement.

Other test basis:

- SDD §1 file-based publisher–producer–reviewer exchange model.

Observed: `curbpack review` does not contradict when the `HOUSE-SECURITY-MD`
line is deleted from `03-executive-summary.md`. The claim id remains confirmed
from `02-action-report.md`. A pass on this case means the omitted line is
detected by comparing the three Review Pack files. It does not mean the
product enforced the omission.

### SETUP

- Repository state: no R-id. Disposable reference-product checkout after `verification-run.sh`.
- Pack input: [PF-11](../../docs2/testing/procedures/1_pack_template_instantiation.md) — selected by SETUP step 2.
- Execution configuration: no EC-id.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"` && `./external_test/curbpack/mutate_pack.sh PF-11`                                                                 | Prints `mutate_pack.sh: PF-11` and installs the prepared Review Pack under `external_test/curbpack/review-pack-input/`. It is not a Git repository and not an R-id.                                                                                                                                                                                            |
| 3    | `grep HOUSE-SECURITY-MD "$REFERENCE_PRODUCT_ROOT/external_test/curbpack/review-pack-input/03-executive-summary.md"`                               | Prints nothing. The same grep on `01-gate-failures.json` and `02-action-report.md` in that folder still matches.                                                                                                                                                                                                                                               |


### TEST STEPS


| Step | Action                                                      | Expected result                                                                                                                                                                                                                                                                                          |
| ---- | ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack review --json "$REFERENCE_PRODUCT_ROOT/external_test/curbpack/review-pack-input"`   | JSON is printed. Ignore `record_digest`. Verify the stable fields against Fig. 4. `contradicted_count` is `0`. `reference:claim:HOUSE-SECURITY-MD` is still confirmed from another file. The product does not flag the deleted summary line.                                                             |
| 2    | `echo $?`                                                   | The exit status is `0`.                                                                                                                                                                                                                                                                                  |
| 3    | Compare `HOUSE-SECURITY-MD` in `01-gate-failures.json` and `02-action-report.md` with `03-executive-summary.md` | The gate id is still in the JSON and the action report. It is absent from the executive summary. Do not treat the summary as a complete account of the machine result.                                                                                                                                    |


```json
{
  "schema": "curbpack-review-report:2",
  "confirmed_count": 9,
  "unconfirmed_count": 10,
  "contradicted_count": 0
}
```

**Fig. 4.** Example of stable fields after Step 1. The omitted finding is visible by file comparison, not by a contradicted review finding.

---

## RP-005 — Verify that a truncated Review Pack file is not treated as a valid complete pack

### Requirements

This case does not verify a specified requirement.

Other test basis:

- SDD §3.3 independent verification boundary.

### SETUP

- Repository state: no R-id. Disposable reference-product checkout after `verification-run.sh`.
- Pack input: [PF-12](../../docs2/testing/procedures/1_pack_template_instantiation.md) — selected by SETUP step 2.
- Execution configuration: no EC-id.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"` && `./external_test/curbpack/mutate_pack.sh PF-12`                                                                 | Prints `mutate_pack.sh: PF-12` and installs the prepared Review Pack under `external_test/curbpack/review-pack-input/`. It is not a Git repository and not an R-id.                                                                                                                                                                                            |
| 3    | `cat "$REFERENCE_PRODUCT_ROOT/external_test/curbpack/review-pack-input/01-gate-failures.json"`                                                     | Prints `{` and a newline. The file is still present.                                                                                                                                                                                                                                                                                                           |


### TEST STEPS


| Step | Action                                                      | Expected result                                                                                                                                                                                                                          |
| ---- | ----------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack review --json "$REFERENCE_PRODUCT_ROOT/external_test/curbpack/review-pack-input"`   | JSON is printed. stderr contains `Contradicted findings present`. Ignore `record_digest`. Verify the stable fields against Fig. 5. `digest:gate-json-parse` is contradicted. The incomplete file is not treated as a valid complete pack. |
| 2    | `echo $?`                                                   | The exit status is `1`.                                                                                                                                                                                                                  |


```json
{
  "schema": "curbpack-review-report:2",
  "confirmed_count": 5,
  "unconfirmed_count": 10,
  "contradicted_count": 1,
  "contradicted_self_disagree": 1
}
```

**Fig. 5.** Example of stable fields after Step 1.

```text
· **[contradicted]** `digest:gate-json-parse` — 01-gate-failures.json is not valid GateFailurePayload JSON: unexpected end of JSON input
```

**Example.** The contradicted finding in the human triage note after Step 1. `structure:01-gate-failures.json` can still be confirmed because the file is present and non-empty. The parse failure is what refuses the pack.

---

## RP-006 — Verify the human attestation boundary

### Requirements

- MUST-72

Passing this case does not close MUST-72: the complete enumerated
human-authority act set is not exercised. A pass cannot close MUST-72
because the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## RP-007 — Verify that a generated proposal or automated edit is not treated as human approval

### Requirements

- MUST-71

Passing this case does not close MUST-71: not every prohibited agent act
in MUST-71 is covered. A pass cannot close MUST-71 because the case is
not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
directly contradicts the suite objective. Omitted or softened findings,
unsupported assurance, or automated human approval are failures.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.
