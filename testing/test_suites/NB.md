# NB — Network and data boundary

## Objective

Check behaviour must respect the documented network and data boundary.
Offline behaviour must match the documented claim, and repository content,
secrets or credentials must not leave the intended boundary.

## Test basis

Requirements addressed by this suite:

- MUST-47
- MUST-48
- MUST-81

Other test basis:

- SDD §1 portable offline-evidence product claim.
- SDD §11 no-server and no-telemetry scope boundaries.

A test execution is always part of a test run that starts with [Prepare a verification run](../../docs2/testing/procedures/README.md).
In short it encompasses cloning the reference product into `<curbpack>/tmp/cyberready-test-product`,
using the recorded `<commit hash>` and `<date>`, and building the CLI. This is done once for a test run.

Each executable case starts the same way: from the Curbpack root, `source tmp/verification-run.sh`. That restore puts the disposable reference product back at the frozen baseline. You can run the cases in any order. Do not keep using the previous case’s directory. Then prepare the case’s named R-state via product `setup.sh` on that already-restored baseline. Then apply EC as the case states. NB-001 and NB-002 do not create an R-id or a `tmp/R*` repository. They are not executable until EC-06 and the observation procedure exist. Do not invent those procedures here.

## Test suite overview


| ID     | Test case / purpose                          | Requirements addressed | Test class | Procedure status |
| ------ | -------------------------------------------- | ---------------------- | ---------- | ---------------- |
| NB-001 | Offline check after installation             | MUST-48, MUST-81       | A          | To be specified  |
| NB-002 | Data leaving the documented boundary         | MUST-47, MUST-48       | A          | To be specified  |


---

## NB-001 — Verify that an offline check after installation yields the same semantic result as a connected run

### Requirements

- MUST-48
- MUST-81

Intended later: representative positive and negative `check` runs without
network access, compared with connected runs of the same states.

EC-06 is not yet specified. Do not invent that isolation and observation
procedure here. A pass cannot close MUST-48 because the case is not
executable. A pass cannot close MUST-81: `scan`, evidence production, and
`review` are not this case, and the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## NB-002 — Verify that a representative local check does not send data outside the documented boundary

### Requirements

- MUST-47
- MUST-48

Intended later: observe a representative local `check` and inspect the
corresponding [CR-10](../../docs2/testing/procedures/2_code_review_procedures.md) evidence for
data leaving the documented boundary.

A repeatable observation mechanism and exact controlled data markers have
not yet been defined. Do not invent those markers or an R-id here. A pass
cannot close MUST-47: default-record field coverage is not executable. A
pass cannot close MUST-48 because the case is not executable. CR-10 remains
an independent review activity; a pass on this case would not close it.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
  this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
  directly contradicts the suite objective. Undocumented network dependence or
  data leaving the intended boundary is a failure.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
  unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.
