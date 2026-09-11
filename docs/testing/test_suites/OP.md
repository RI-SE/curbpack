# OP — Operational failure handling

## Objective

Partial execution, write failure, cache failure, malformed output or process
termination must not be mistaken for a successful complete evaluation.

## Test basis

Requirements:

- MUST-22
- MUST-35
- MUST-46
- MUST-53

Other test basis:

- SDD §7.3 interruption-recovery and complete-record expectations.

## Test case catalogue

| ID | Test case / purpose | Test class | Procedure status |
|---|---|---|---|
| OP-001 | Partial JSON with non-zero operational failure | A | To be specified |
| OP-002 | Empty or malformed output | A | To be specified |
| OP-003 | Unwritable output destination | A | To be specified |
| OP-004 | Storage exhaustion | A | To be specified |
| OP-005 | Process killed during check | A | To be specified |
| OP-006 | Cache failure | C | To be specified |

## OP-003 — Unwritable output destination

**Status: To be specified**

Intended condition: execute a check whose required output destination cannot
be written and verify that it is not reported as a successful complete
evaluation.

Missing prerequisite: a reliable EC-09 unwritable-destination preparation and
verification mechanism has not yet been defined.

## OP-005 — Process killed during check

**Status: To be specified**

Intended condition: terminate a check during execution and verify that partial
output is not treated as a successful complete evaluation.

Missing prerequisite: a repeatable EC-09 execution window and controlled
termination point have not yet been defined.

## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
  this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
  directly contradicts the suite objective. Partial or failed execution
  represented as a successful complete evaluation is a failure.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
  unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.
