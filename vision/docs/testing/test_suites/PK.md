# PK — Rule-pack input validation

## Objective

Invalid, ambiguous, conflicting or unsupported rule-pack input must not
silently produce a pass result or silently change defined semantics.

## Test basis

Requirements addressed by this suite:

- MUST-22
- MUST-40

Other test basis:

- SDD §5.1 closed evaluator check algebra and unsupported-check boundary.

A test execution is always part of a test run that starts with [Prepare a verification run](../procedures/README.md).
In short it encompasses cloning the reference product into `<curbpack>/tmp/cyberready-test-product`,
using the recorded `<commit hash>` and `<date>`, and building the CLI. This is done once for a test run.

Each executable case starts the same way: from the Curbpack root, `source tmp/verification-run.sh`. That restore puts the disposable reference product back at the frozen baseline. You can run the cases in any order. Do not keep using the previous case’s directory. Then prepare R1 via product `setup.sh` on that already-restored baseline. Then apply EC as the case states. PK-002, PK-003, PK-004, and PK-005 keep that same R1 checkout and select the named PF with `mutate_pack.sh`. They do not create an R-id or a `tmp/R*` repository.

## Test suite overview


| ID     | Test case / purpose                                                      | Requirements addressed | Test class | Procedure status |
| ------ | ------------------------------------------------------------------------ | ---------------------- | ---------- | ---------------- |
| PK-001 | Valid pack baseline yields a pass                                        | —                      | A          | Covered by EV-001|
| PK-002 | Malformed or truncated pack input                                        | MUST-22, MUST-40       | A          | Executable       |
| PK-003 | Duplicate or conflicting rules and pack versions                         | MUST-40                | A          | Partial          |
| PK-004 | Unsupported check type is not treated as a pass                          | MUST-22, MUST-40       | A          | Executable       |
| PK-005 | Invalid regular expression is not treated as a pass                      | MUST-22, MUST-40       | A          | Executable       |


---

## PK-001 — Valid-pack positive control

### Requirements

This case does not verify a specified requirement.

Other test basis:

- SDD §5.1 closed evaluator check algebra: PF-01 uses only registered
  check kinds and is accepted for evaluation.

### Test evidence

[EV-001](EV.md#ev-001--verify-that-a-good-reference-product-yields-a-pass)
provides the positive control for this suite. It executes the same
R1 / PF-01 / EC-01 combination and demonstrates that PF-01 is accepted
for evaluation and produces the expected passing outcome.

PK-001 defines no separate execution procedure and reuses the EV-001
execution record. It must not be counted as an additional executed
testcase.

## PK-002 — Verify that malformed or truncated pack input does not silently produce a pass

### Requirements

- MUST-22
- MUST-40

Passing this case does not close MUST-22: other failed-read, write, subprocess,
and walk paths remain. Passing this case does not close MUST-40: the complete
untrusted-input set is not this case.

The pack is the stimulus. R1 is only the git root required to run `check`.
This case does not invent a new R-id.

PK-002 has two independently executable variants. Each starts with
`source tmp/verification-run.sh`. Do not keep the previous variant’s working
tree. Both overwrite `house-policy/pack.json` from the identified PF-01
valid control. The operator does not edit JSON.

| Variant | Prepared input | Difference from PF-01 `house-policy/pack.json` |
| ------- | -------------- | ---------------------------------------------- |
| A | [PF-13](../procedures/1_pack_template_instantiation.md) | Same bytes except the comma after `"version": "0.1.0"` is removed (malformed JSON, not a prefix) |
| B | [PF-14](../procedures/1_pack_template_instantiation.md) | First 120 bytes of that same valid file (truncated JSON) |

### PK-002-A — malformed JSON

#### SETUP

- Repository state: [R1](../procedures/0_controlled_repo_setup.md#r1) — prepared by `setup.sh` in step 3.
- Pack input: [PF-13](../procedures/1_pack_template_instantiation.md) — selected by SETUP step 5.
- Execution configuration: [EC-01](../procedures/0_controlled_repo_setup.md#ec-01) — established and verified by steps 3–4.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R1 --commit`                                                                                                  | Applies R1 to the already-restored frozen baseline. Does not restore the baseline. Prints the R1 state description (required files, heading, `package.json` conditions). Otherwise, stop.                                                                                                                                                                       |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `./external_test/curbpack/mutate_pack.sh PF-13`                                                                                                  | Prints `mutate_pack.sh: PF-13` and installs `pf-fixtures/PF-13/house-policy/pack.json` onto `external_test/curbpack/packs/house-policy/pack.json`. Remain at `$REFERENCE_PRODUCT_ROOT`.                                                                                                                                                                          |
| 6    | `grep -F '"version": "0.1.0"' "$CURBPACK_PACKS_DIR/house-policy/pack.json"`                                                                       | The version line is present and is not followed by a comma. The installed file is the malformed fixture, not a missing path. Otherwise, stop.                                                                                                                                                                                                                   |


#### TEST STEPS


| Step | Action                                        | Expected result                                                                                                                                                                                                 |
| ---- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --json --as-of "$AS_OF_DATE"` | The command does not print JSON. stdout is empty. stderr reports a JSON parse failure for pack `house-policy`. The failure is not a missing-path or missing-file error. The result is not a pass. Failed parsing is not omitted or reported as success (MUST-22). |
| 2    | `echo $?`                                     | The exit status is not `0`.                                                                                                                                                                                     |


### PK-002-B — truncated JSON

#### SETUP

- Repository state: [R1](../procedures/0_controlled_repo_setup.md#r1) — prepared by `setup.sh` in step 3.
- Pack input: [PF-14](../procedures/1_pack_template_instantiation.md) — selected by SETUP step 5.
- Execution configuration: [EC-01](../procedures/0_controlled_repo_setup.md#ec-01) — established and verified by steps 3–4.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R1 --commit`                                                                                                  | Applies R1 to the already-restored frozen baseline. Does not restore the baseline. Prints the R1 state description (required files, heading, `package.json` conditions). Otherwise, stop.                                                                                                                                                                       |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `./external_test/curbpack/mutate_pack.sh PF-14`                                                                                                  | Prints `mutate_pack.sh: PF-14` and installs `pf-fixtures/PF-14/house-policy/pack.json` onto `external_test/curbpack/packs/house-policy/pack.json`. Remain at `$REFERENCE_PRODUCT_ROOT`.                                                                                                                                                                          |
| 6    | `wc -c "$CURBPACK_PACKS_DIR/house-policy/pack.json"`                                                                                              | The printed byte count is `120`. The installed file is the truncated fixture, not a missing path. Otherwise, stop.                                                                                                                                                                                                                                              |


#### TEST STEPS


| Step | Action                                        | Expected result                                                                                                                                                                                                 |
| ---- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --json --as-of "$AS_OF_DATE"` | The command does not print JSON. stdout is empty. stderr reports a JSON parse failure for pack `house-policy`. The failure is not a missing-path or missing-file error. The result is not a pass. Failed parsing is not omitted or reported as success (MUST-22). |
| 2    | `echo $?`                                     | The exit status is not `0`.                                                                                                                                                                                     |


---

## PK-003 — Verify that duplicate or conflicting rules and pack versions do not silently change defined semantics

### Requirements

- MUST-40

Passing this case does not close MUST-40: the complete untrusted-input set is
not this case.

The pack is the stimulus. R1 is only the git root required to run `check`.
This case does not invent a new R-id.

PK-003 has three independently executable variants plus one retained oracle
gap. Each executable variant starts with `source tmp/verification-run.sh`.
Do not keep the previous variant’s working tree. Valid control: PF-01
`house-policy/pack.json` (one `HOUSE-SECURITY-MD` rule).

| Variant | Prepared input | Difference from PF-01 `house-policy/pack.json` | Status |
| ------- | -------------- | ---------------------------------------------- | ------ |
| A | [PF-15](../procedures/1_pack_template_instantiation.md) | Identical duplicated `HOUSE-SECURITY-MD` rule object | Executable; oracle: not a silent PF-01 pass |
| B | [PF-16](../procedures/1_pack_template_instantiation.md) | Conflicting `HOUSE-SECURITY-MD` definitions, original then `docs/pk003-absent.md` | Executable; oracle: not a silent PF-01 pass |
| C | [PF-17](../procedures/1_pack_template_instantiation.md) | Same conflicting definitions as PF-16, reverse order | Executable; oracle: not a silent PF-01 pass |
| D | Conflicting versions of the same pack identity | — | Not specified. No version-selection syntax exists. Do not invent one. Observed `extends` later-wins behaviour is not a PASS criterion. |

A specified duplicate-resolution or version-selection rule is absent.
Do not treat a particular error string, last-wins merge, or first-wins
merge as a PASS criterion. The specified expected result is only that
the command does not silently produce the PF-01 pass.

### PK-003-A — identical duplicated rule

#### SETUP

- Repository state: [R1](../procedures/0_controlled_repo_setup.md#r1) — prepared by `setup.sh` in step 3.
- Pack input: [PF-15](../procedures/1_pack_template_instantiation.md) — selected by SETUP step 5.
- Execution configuration: [EC-01](../procedures/0_controlled_repo_setup.md#ec-01) — established and verified by steps 3–4.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R1 --commit`                                                                                                  | Applies R1 to the already-restored frozen baseline. Does not restore the baseline. Prints the R1 state description (required files, heading, `package.json` conditions). Otherwise, stop.                                                                                                                                                                       |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `./external_test/curbpack/mutate_pack.sh PF-15`                                                                                                  | Prints `mutate_pack.sh: PF-15` and installs `pf-fixtures/PF-15/house-policy/pack.json` onto `external_test/curbpack/packs/house-policy/pack.json`. Remain at `$REFERENCE_PRODUCT_ROOT`.                                                                                                                                                                          |
| 6    | `grep -c '"id": "HOUSE-SECURITY-MD"' "$CURBPACK_PACKS_DIR/house-policy/pack.json"`                                                                | The printed count is `2`. Otherwise, stop.                                                                                                                                                                                                                                                                                                                      |


#### TEST STEPS


| Step | Action                                        | Expected result |
| ---- | --------------------------------------------- | --------------- |
| 1    | `curbpack check --json --as-of "$AS_OF_DATE"` | The result is not the PF-01 pass (`outcome` `pass`, exit `0`, Fig. 1 of EV-001). Record the actual stdout, stderr, and exit status. A particular error string is not a PASS criterion. |
| 2    | `echo $?`                                     | Record the exit status. Do not treat `0` as a pass of this variant. |


### PK-003-B — conflicting definitions, order A then B

#### SETUP

Repeat PK-003-A SETUP steps 1–4, then:

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 5 | `./external_test/curbpack/mutate_pack.sh PF-16` | Prints `mutate_pack.sh: PF-16` and installs the conflicting A-then-B `house-policy` file. |
| 6 | `grep -n 'docs/pk003-absent.md' "$CURBPACK_PACKS_DIR/house-policy/pack.json"` | A match exists. The first `HOUSE-SECURITY-MD` `path` in the file is `SECURITY.md`. Otherwise, stop. |


#### TEST STEPS


| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | `curbpack check --json --as-of "$AS_OF_DATE"` | The result is not the PF-01 pass. Record the actual stdout, stderr, and exit status. A particular winner between the two definitions is not a PASS criterion. |
| 2 | `echo $?` | Record the exit status. Do not treat `0` as a pass of this variant. |


### PK-003-C — conflicting definitions, order B then A

#### SETUP

Repeat PK-003-A SETUP steps 1–4, then:

| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 5 | `./external_test/curbpack/mutate_pack.sh PF-17` | Prints `mutate_pack.sh: PF-17` and installs the conflicting B-then-A `house-policy` file. |
| 6 | `grep -n 'docs/pk003-absent.md' "$CURBPACK_PACKS_DIR/house-policy/pack.json"` | A match exists. The first `HOUSE-SECURITY-MD` `path` in the file is `docs/pk003-absent.md`. Otherwise, stop. |


#### TEST STEPS


| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1 | `curbpack check --json --as-of "$AS_OF_DATE"` | The result is not the PF-01 pass. Record the actual stdout, stderr, and exit status. A particular winner between the two definitions is not a PASS criterion. |
| 2 | `echo $?` | Record the exit status. Do not treat `0` as a pass of this variant. |


### PK-003-D — conflicting pack versions

Not specified. Do not run this variant. There is no documented
version-selection syntax or duplicate-resolution requirement for two
versions of the same pack identity. Do not invent one.

---

## PK-004 — Verify that an unsupported check type is not treated as a pass

### Requirements

- MUST-22
- MUST-40

Passing this case does not close MUST-22: other failed-read, write, subprocess,
and walk paths remain. Passing this case does not close MUST-40: the complete
untrusted-input set is not this case.

The pack is the stimulus. R1 is only the git root required to run `check`.
This case does not invent a new R-id.

### SETUP

- Repository state: [R1](../procedures/0_controlled_repo_setup.md#r1) — prepared by `setup.sh` in step 3.
- Pack input: [PF-03](../procedures/1_pack_template_instantiation.md) (`unknown-check`). Selected by SETUP step 5. This is not an R-id and not a `tmp/R*` repository.
- Execution configuration: [EC-01](../procedures/0_controlled_repo_setup.md#ec-01) — established and verified by steps 3–4.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R1 --commit`                                                                                                  | Applies R1 to the already-restored frozen baseline. Does not restore the baseline. Prints the R1 state description (required files, heading, `package.json` conditions). Otherwise, stop.                                                                                                                                                                       |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `./external_test/curbpack/mutate_pack.sh PF-03`                                                                                                  | Prints `mutate_pack.sh: PF-03` and installs `pf-fixtures/PF-03/unknown-check/pack.json` onto `external_test/curbpack/packs/unknown-check/pack.json`. Remain at `$REFERENCE_PRODUCT_ROOT`. `CURBPACK_PACKS_DIR` stays the verification-run value. |
| 6    | `grep -F '"check": "llm_judge"' "$CURBPACK_PACKS_DIR/unknown-check/pack.json"`                                                                    | The line is present. The fixture exists and declares the unsupported check. Otherwise, stop.                                                                                                                                                                                                                                                                    |


### TEST STEPS


| Step | Action                                                             | Expected result                                                                                                                                                                                                |
| ---- | ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --packs unknown-check --json --as-of "$AS_OF_DATE"` | The command does not print JSON. stdout is empty. stderr is the line in the example below (`unsupported check` and `llm_judge`). The result is not a pass.                                                     |
| 2    | `echo $?`                                                          | The exit status is `1`.                                                                                                                                                                                        |


```text
pack "unknown-check" rule "ADV-UNKNOWN": unsupported check "llm_judge"
```

**Example.** stderr after Step 1. stdout is empty. Compare the words `unsupported check` and `llm_judge`. The check kind `llm_judge` is refused at pack load. The command does not print a pass JSON payload.

---

## PK-005 — Verify that an invalid regular expression is not treated as a pass

### Requirements

- MUST-22
- MUST-40

Passing this case does not close MUST-22: other failed-read, write, subprocess,
and walk paths remain. Passing this case does not close MUST-40: the complete
untrusted-input set is not this case.

The pack is the stimulus. R1 is only the git root required to run `check`.
This case does not invent a new R-id.

### SETUP

- Repository state: [R1](../procedures/0_controlled_repo_setup.md#r1) — prepared by `setup.sh` in step 3.
- Pack input: [PF-04](../procedures/1_pack_template_instantiation.md) (`bad-regex`). Selected by SETUP step 5. This is not an R-id and not a `tmp/R*` repository.
- Execution configuration: [EC-01](../procedures/0_controlled_repo_setup.md#ec-01) — established and verified by steps 3–4.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R1 --commit`                                                                                                  | Applies R1 to the already-restored frozen baseline. Does not restore the baseline. Prints the R1 state description (required files, heading, `package.json` conditions). Otherwise, stop.                                                                                                                                                                       |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `./external_test/curbpack/mutate_pack.sh PF-04`                                                                                                  | Prints `mutate_pack.sh: PF-04` and installs `pf-fixtures/PF-04/bad-regex/pack.json` onto `external_test/curbpack/packs/bad-regex/pack.json`. Remain at `$REFERENCE_PRODUCT_ROOT`. `CURBPACK_PACKS_DIR` stays the verification-run value. |
| 6    | `grep -F '(?P<unterminated' "$CURBPACK_PACKS_DIR/bad-regex/pack.json"`                                                                            | The unterminated `pattern` is present. The fixture exists. Otherwise, stop.                                                                                                                                                                                                                                                                                     |


### TEST STEPS


| Step | Action                                                          | Expected result                                                                                                                                                                                                 |
| ---- | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --packs bad-regex --json --as-of "$AS_OF_DATE"` | The command does not print JSON. stdout is empty. stderr is the line in the example below (`invalid pattern` and `invalid named capture`). The result is not a pass.                                            |
| 2    | `echo $?`                                                       | The exit status is `1`.                                                                                                                                                                                         |


```text
pack "bad-regex" rule "ADV-BAD-RE": invalid pattern: error parsing regexp: invalid named capture: `(?P<unterminated`
```

**Example.** stderr after Step 1. stdout is empty. Compare the words `invalid pattern` and `invalid named capture`. The pack is refused at load. The command does not print a pass JSON payload.

---

## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
directly contradicts the suite objective. Silent acceptance that produces a
pass or changes defined semantics is a failure.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.
