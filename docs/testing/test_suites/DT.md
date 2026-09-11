# DT — Determinism and finding identity

## Objective

Equivalent inputs in scope of the selected pack must produce equivalent
semantic results and stable finding identities. Controlled changes should
affect only expected findings or explicitly dependent fields.

## Test basis

Requirements:

- MUST-30
- MUST-31

Other test basis:

- SDD §7.3 deterministic-behavior and exact-evidence expectations.

## Test case catalogue

| ID | Test case / purpose | Test class | Procedure status |
|---|---|---|---|
| DT-001 | Repeatability of identical inputs | A | Executable |
| DT-002 | Locale and timezone variation | B | To be specified |
| DT-003 | Controlled change sensitivity | A | Executable |
| DT-004 | Finding identity stability | A | Executable |

## DT-001 — Repeatability of identical inputs

### Prerequisites / SETUP

- Repository state: R1
- Pack input: PF-01
- Execution configuration: EC-01

1. `cd <reference-product-root>`.
2. Run `./external_test/curbpack/setup.sh R1 <pin>`.
3. Run
   `export CURBPACK_PACKS_DIR="$(pwd)/external_test/curbpack/packs"`.
4. Create an empty evidence directory outside the Curbpack and reference
   product repositories for the 20 JSON files.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | From the **reference-product root**, run the same `curbpack check --json --as-of <date>` 20 times | Exit 0 every time |
| 2 | Compare `failures`, `pack_id`, exit status, and any stable digest fields across the 20 JSON files | No unexplained semantic difference |

### TEARDOWN

None. Leave the checkout.

## DT-003 — Controlled change sensitivity

### Prerequisites / SETUP

- Repository states: R1 followed by R2
- Pack input: PF-01
- Execution configuration: EC-01
- Other prerequisite: retain one R1 JSON result as declared evidence.

1. `cd <reference-product-root>`.
2. Run `./external_test/curbpack/setup.sh R1 <pin>`.
3. Run
   `export CURBPACK_PACKS_DIR="$(pwd)/external_test/curbpack/packs"`.
4. Run `curbpack check --json --as-of <date>` and save the JSON as the R1
   result.
5. Run `./external_test/curbpack/setup.sh R2 <pin> --commit`.
6. Confirm `SECURITY.md` is absent and `git status --porcelain` is empty.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | `curbpack check --json --as-of <date>` on R2 | Exit ≠ 0; `HOUSE-SECURITY-MD` present |
| 2 | Diff R1 JSON against R2 JSON | Only the expected finding (and fields that depend on it) change |

### TEARDOWN

None. Leave the checkout.

## DT-004 — Finding identity stability

### Prerequisites / SETUP

- Repository states: R1 followed by R2
- Pack input: PF-01
- Execution configuration: EC-01
- Other prerequisite: 20 retained R1 JSON results and one retained R2 JSON
  result from the same frozen baseline.

The retained results may come from DT-001 and DT-003. To prepare them without
running those cases, prepare R1 with
`./external_test/curbpack/setup.sh R1 <pin>`, select PF-01 with
`export CURBPACK_PACKS_DIR="$(pwd)/external_test/curbpack/packs"`, and save 20
executions of `curbpack check --json --as-of <date>`. Then prepare R2 with
`./external_test/curbpack/setup.sh R2 <pin> --commit` and save one execution of
the same command.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | Compare finding identifiers across the 20 identical R1 runs | Same ids |
| 2 | Compare R1 ids to R2 | Ids change only where a documented identity input changed (`SECURITY.md` missing) |

### TEARDOWN

None.

## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
  this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
  directly contradicts the suite objective. Unexplained semantic differences
  or unstable finding identities for equivalent inputs are failures.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
  unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.
