# NB — Network and data boundary

## Objective

Check behaviour must respect the documented network and data boundary.
Offline behaviour must match the documented claim, and repository content,
secrets or credentials must not leave the intended boundary.

## Test basis

Requirements:

- MUST-47
- MUST-48
- MUST-81

Other test basis:

- SDD §1 portable offline-evidence product claim.
- SDD §11 no-server and no-telemetry scope boundaries.

## Test case catalogue

| ID | Test case / purpose | Test class | Procedure status |
|---|---|---|---|
| NB-001 | Offline check after installation | A | To be specified |
| NB-002 | Data leaving the documented boundary | A | To be specified |

## NB-001 — Offline check after installation

**Status: To be specified**

Intended condition: run representative positive and negative checks without
network access and compare their semantic results with the connected runs.

Missing prerequisite: a repeatable EC-06 network-isolation and observation
procedure has not yet been defined.

## NB-002 — Data leaving the documented boundary

**Status: To be specified**

Intended condition: observe a representative local check and inspect the
corresponding CR-10 evidence for data leaving the documented boundary.

Missing prerequisite: a repeatable observation mechanism and exact controlled
data markers have not yet been defined.

## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
  this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
  directly contradicts the suite objective. Undocumented network dependence or
  data leaving the intended boundary is a failure.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
  unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.
