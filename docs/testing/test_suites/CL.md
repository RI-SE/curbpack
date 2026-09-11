# CL — Claim review

## Objective

Documentation and generated outputs must not convert structural observations
into unsupported claims of security, compliance, certification, legal
sufficiency, clinical adequacy, CE marking or approval.

## Test basis

Requirements:

- MUST-01
- MUST-02
- MUST-04

Other test basis:

- SDD opening product claim and SDD §1.1 claim boundary.
- SDD §11 prohibition on model-decided compliance or trust.

## Test case catalogue

| ID | Test case / purpose | Test class | Procedure status |
|---|---|---|---|
| CL-001 | Public and generated claim review | A | Executable |
| CL-002 | Boundary statement consistency | A | Executable |
| CL-003 | User interpretation of pass | A | To be specified |
| CL-004 | Time/cost benefit claim | C | To be specified |

## CL-001 — Public and generated claim review

### Prerequisites / SETUP

- Repository state: no R-id is required for source-document review.
- Pack input: no PF-id is required unless generated output is included.
- Execution configuration: no EC-id.
- Other prerequisite: frozen Curbpack source/release plus any generated output
  included in the verification assignment.

1. Fill the test record **Run** table.
2. Work in `<curbpack>` plus any JSON / Review Pack you already produced
   (EV-001, RP-001). Search shipped docs, site text, examples, CLI output,
   issue/install material.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | Search for language that implies security, compliance, certification, CE marking, legal sufficiency, clinical adequacy, regulator acceptance, or RISE approval | Absent, clearly denied, or clearly attributed to an authorised external party |
| 2 | Material overclaim | Fail this case (release-blocking for the assignment) |

### TEARDOWN

None.

## CL-002 — Boundary statement consistency

### Prerequisites / SETUP

- Repository state: R1 or R2, recorded on the test record
- Pack input: PF-01
- Execution configuration: EC-01
- Other prerequisite: matching machine JSON and human-facing output from the
  same prepared state and frozen baseline.

If matching evidence does not already exist, `cd <reference-product-root>`,
run `./external_test/curbpack/setup.sh <R-id> <pin>` (add `--commit` for R2),
select PF-01 with
`export CURBPACK_PACKS_DIR="$(pwd)/external_test/curbpack/packs"`, retain
`curbpack check --json --as-of <date>`, then run
`curbpack share --as-of <date>` and retain the generated human-facing files.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | Compare disclaimers and explanatory sentences across JSON and human text | No derivative weakens the structural-only boundary or turns a non-pass into assurance |

### TEARDOWN

None.

## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
  this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
  directly contradicts the suite objective. Unsupported assurance or
  conformity language is a failure.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
  unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.
