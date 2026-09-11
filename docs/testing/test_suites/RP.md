# RP — Review Pack, output, and attestation integrity

## Objective

Human-facing output and Review Packs must not omit, reverse or soften material
machine-readable findings or add unsupported assurance. Automation or
generated material must not create, infer or overwrite human approval or be
treated as reviewed evidence without the required deterministic re-check and
human review.

## Test basis

Requirements:

- MUST-02
- MUST-04
- MUST-71
- MUST-72

Other test basis:

- SDD §1 file-based publisher–producer–reviewer exchange model.
- SDD §3.3 independent verification boundary.

## Test case catalogue

| ID | Test case / purpose | Test class | Procedure status |
|---|---|---|---|
| RP-001 | Machine-to-human consistency, clean result | A | Executable |
| RP-002 | Machine-to-human consistency, failed result | A | Executable |
| RP-003 | Tampered machine result or substituted state | A | Executable |
| RP-004 | Edited summary, removed finding, or stale digest | A | Executable |
| RP-005 | Incomplete or truncated Review Pack file | A | Executable |
| RP-006 | Human attestation boundary | C | To be specified |
| RP-007 | Generated proposal or automated edit | C | To be specified |

## RP-001 — Machine-to-human consistency, clean result

### Prerequisites / SETUP

- Repository state: R1
- Pack input: PF-01
- Execution configuration: EC-01

1. `cd <reference-product-root>`.
2. Run `./external_test/curbpack/setup.sh R1 <pin>`.
3. Run
   `export CURBPACK_PACKS_DIR="$(pwd)/external_test/curbpack/packs"`.
4. Run `curbpack check --json --as-of <date>` and retain the JSON output.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | From the reference-product root, run `curbpack share --as-of <date>` | Review Pack is created from the same declared date |
| 2 | Compare JSON statuses, ids, counts, repo identity, pack identity, and boundary sentences to the human-facing Review Pack files | Same facts. Summarisation does not add unsupported assurance |

### TEARDOWN

None. Leave the checkout and the Review Pack folder for RP-002 if you
continue immediately.

## RP-002 — Machine-to-human consistency, failed result

### Prerequisites / SETUP

- Repository state: R2
- Pack input: PF-01
- Execution configuration: EC-01

1. `cd <reference-product-root>`.
2. Run `./external_test/curbpack/setup.sh R2 <pin> --commit`.
3. Confirm `SECURITY.md` is absent.
4. Run
   `export CURBPACK_PACKS_DIR="$(pwd)/external_test/curbpack/packs"`.

A skipped or unavailable operational state has no controlled preparation yet;
that coverage remains To be specified with EV-005.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | Run `curbpack check --json --as-of <date>`, retain its output, then run `curbpack share --as-of <date>` | Both outputs exist for the same declared date |
| 2 | Compare machine `HOUSE-SECURITY-MD` to the human-facing summary | The fail is not omitted, reversed, or softened into pass |

### TEARDOWN

None.

## RP-003 — Tampered Review Pack

### Prerequisites / SETUP

- Repository state: no R-id; use the named frozen Review Pack fixture.
- Pack input: no PF-id.
- Execution configuration: no EC-id.

1. Copy `<curbpack>/testdata/sample-review-pack/` to a throwaway folder.
2. In `01-gate-failures.json` in the copy, replace the
   `expected_parent_commit_sha` value with 40 `b` characters. Record the exact
   edit.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | `curbpack review <throwaway-copy>` | Completes |
| 2 | Read the triage output | Mismatch detected by the product, or you detect it by comparison — write which. Tampering is not trusted as the original pass |

### TEARDOWN

None. Leave the throwaway copy.

## RP-004 — Edited summary or stale digest

### Prerequisites / SETUP

- Repository state: no R-id; use the named frozen Review Pack fixture.
- Pack input: no PF-id.
- Execution configuration: no EC-id.

1. Copy `<curbpack>/testdata/sample-review-pack/` to a throwaway folder.
2. In the copy of `03-executive-summary.md`, delete the complete line
   containing `HOUSE-SECURITY-MD`. Do not edit `01-gate-failures.json`.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | `curbpack review <throwaway-copy>` | Completes |
| 2 | Read the triage output | Material divergence is visible. Write whether the product enforced it or you detected it by hand |

### TEARDOWN

None.

## RP-005 — Truncated Review Pack file

### Prerequisites / SETUP

- Repository state: no R-id; use the named frozen Review Pack fixture.
- Pack input: no PF-id.
- Execution configuration: no EC-id.

1. Copy `<curbpack>/testdata/sample-review-pack/` to a throwaway folder.
2. Replace the copy of `01-gate-failures.json` with the two bytes `{` and a
   newline so the JSON is incomplete.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | `curbpack review <throwaway-copy>` | Completes or refuses |
| 2 | Read the result | Incomplete file is not treated as a valid complete Review Pack |

### TEARDOWN

None.

## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
  this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
  directly contradicts the suite objective. Omitted or softened findings,
  unsupported assurance, or automated human approval are failures.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
  unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.
