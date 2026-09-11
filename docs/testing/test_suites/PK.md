# PK — Rule-pack input validation

## Objective

Invalid, ambiguous, conflicting or unsupported rule-pack input must not
silently produce a pass result or silently change defined semantics.

## Test basis

Requirements:

- MUST-22
- MUST-40

Other test basis:

- SDD §5.1 closed evaluator check algebra and unsupported-check boundary.

## Test case catalogue

| ID | Test case / purpose | Test class | Procedure status |
|---|---|---|---|
| PK-001 | Valid pack baseline (PF-01, reference product R1) | A | Executable |
| PK-002 | Malformed or truncated pack input | A | To be specified |
| PK-003 | Duplicate or conflicting rules and pack versions | A | To be specified |
| PK-004 | Unsupported check type | A | Executable |
| PK-005 | Invalid regular expression | A | Executable |

## PK-001 — Valid pack baseline

### Prerequisites / SETUP

- Repository state: R1
- Pack input: PF-01
- Execution configuration: EC-01

1. `cd <reference-product-root>`.
2. Run `./external_test/curbpack/setup.sh R1 <pin>`.
3. Run
   `export CURBPACK_PACKS_DIR="$(pwd)/external_test/curbpack/packs"`.
4. Open `external_test/curbpack/packs/house-policy/pack.json`,
   `external_test/curbpack/packs/medtech-iec62304/pack.json`, and
   `external_test/curbpack/packs/SOURCE.txt`. Note the pack IDs and versions
   from the `pack.json` files, and separately note the source repository and
   commit recorded by `SOURCE.txt`.

The same R1 check output may support EV-001, but PK-001 can be run
independently using these steps.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | From the **reference-product root**: `curbpack check --json --as-of <date>` | Exit 0 |
| 2 | Read JSON `failures` | Empty |
| 3 | Read JSON `pack_id` | Contains `house-policy` and `medtech-iec62304` |
| 4 | Compare the JSON pack IDs with the selected `pack.json` files; retain the separate `SOURCE.txt` provenance | Same selected pack IDs. Do not claim that `SOURCE.txt` contains pack IDs or versions |

### TEARDOWN

None. Leave the checkout. The next `setup.sh` hard-resets first.

## PK-004 — Unsupported check type

### Prerequisites / SETUP

- Repository state: no R-id; use a clean throwaway repository.
- Pack input: PF-03 (`unknown-check`)
- Execution configuration: EC-01

1. Fill the test record **Run** table so `<curbpack>` is known.
2. Create a **throwaway repo**: empty folder, `git init`, one empty commit.
   Do not invent a pack file. Do not use the reference product.
3. `export CURBPACK_PACKS_DIR=<curbpack>/testdata/adversarial/packs`
4. Confirm `<curbpack>/testdata/adversarial/packs/unknown-check/pack.json`
   exists (`check` is `llm_judge`).

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | In the throwaway repo: `curbpack check --packs unknown-check` (or `curbpack init --packs unknown-check`) | Exit ≠ 0 |
| 2 | Read stderr or JSON | Unsupported check refused at load or evaluation |
| 3 | Same run | Not a complete pass. No panic |

### TEARDOWN

None. Leave the throwaway folder.

## PK-005 — Invalid regular expression

### Prerequisites / SETUP

- Repository state: no R-id; use a clean throwaway repository.
- Pack input: PF-03 (`bad-regex`)
- Execution configuration: EC-01

1. Fill the test record Run section so `<curbpack>` is known.
2. Create a new empty throwaway folder and run `git init`,
   `git commit --allow-empty -m fixture`.
3. Run
   `export CURBPACK_PACKS_DIR=<curbpack>/testdata/adversarial/packs`.
4. Confirm
   `<curbpack>/testdata/adversarial/packs/bad-regex/pack.json` exists and
   contains the deliberately unterminated `pattern`.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | In the throwaway repo: `curbpack check --packs bad-regex` | Exit ≠ 0, or an explicit pack-load error |
| 2 | Read the error or JSON | Mentions the pattern or otherwise refuses the pack |
| 3 | Same run | No panic. Not a pass |

### TEARDOWN

None. Leave the throwaway folder.

## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
  this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
  directly contradicts the suite objective. Silent acceptance that produces a
  pass or changes defined semantics is a failure.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
  unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.
