# OP — Operational failure handling

## Objective

Partial execution, write failure, cache failure, malformed output or process
termination must not be mistaken for a successful complete evaluation.

## Test basis

Requirements addressed by this suite:

- MUST-22
- MUST-35
- MUST-46
- MUST-53

Other test basis:

- SDD §7.3 interruption-recovery and complete-record expectations.

A test execution is always part of a test run that starts with [Prepare a verification run](../../docs2/testing/procedures/README.md).
In short it encompasses cloning the reference product into `<curbpack>/tmp/cyberready-test-product`,
using the recorded `<commit hash>` and `<date>`, and building the CLI. This is done once for a test run.

Each executable case starts the same way: from the Curbpack root, `source tmp/verification-run.sh`. That restore puts the disposable reference product back at the frozen baseline. You can run the cases in any order. Do not keep using the previous case’s directory. Then prepare the case’s named R-state via product `setup.sh` on that already-restored baseline. Then apply EC as the case states. No OP case is currently executable. Do not invent an R-id or a `tmp/R*` repository. [EC-09](../../docs2/testing/procedures/README.md#execution-configurations) is not yet specified; do not improvise unwritable-destination, storage-exhaustion, or controlled-termination preparation in a case.

## Test suite overview


| ID     | Test case / purpose                                              | Requirements addressed              | Test class | Procedure status |
| ------ | ---------------------------------------------------------------- | ----------------------------------- | ---------- | ---------------- |
| OP-001 | Partial JSON with non-zero operational failure                   | MUST-22, MUST-53                    | A          | To be specified  |
| OP-002 | Empty or malformed output                                        | MUST-22, MUST-53                    | A          | To be specified  |
| OP-003 | Unwritable output destination                                    | MUST-22, MUST-53                    | A          | To be specified  |
| OP-004 | Storage exhaustion                                               | MUST-22, MUST-53                    | A          | To be specified  |
| OP-005 | Process killed during check                                      | MUST-22, MUST-35, MUST-46, MUST-53  | A          | To be specified  |
| OP-006 | Cache failure                                                    | MUST-22, MUST-35, MUST-53           | C          | To be specified  |


---

## OP-001 — Verify that partial JSON is accompanied by a non-zero operational failure

### Requirements

- MUST-22
- MUST-53

Passing this case does not close MUST-22: failed-read, write, parse, subprocess,
and walk paths remain. Passing this case does not close MUST-53: pass, finding,
usage, and environment exit distinctions are not this case.

No specified R-state or EC produces partial JSON. EC-09 is not yet specified.
Do not invent that procedure here. A pass cannot close MUST-22 or MUST-53
because the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## OP-002 — Verify that empty or malformed output is not treated as a successful complete evaluation

### Requirements

- MUST-22
- MUST-53

Passing this case does not close MUST-22: failed-read, write, parse, subprocess,
and walk paths remain. Passing this case does not close MUST-53: pass, finding,
usage, and environment exit distinctions are not this case.

No specified R-state, pack input, or EC produces empty or malformed `check`
output as the SUT response. Do not invent expected JSON. A pass cannot close
MUST-22 or MUST-53 because the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## OP-003 — Verify that an unwritable output destination is not reported as a successful complete evaluation

### Requirements

- MUST-22
- MUST-53

Passing this case does not close MUST-22: other failed-read, parse, subprocess,
and walk paths remain. Passing this case does not close MUST-53: pass, finding,
usage, and environment exit distinctions are not this case.

EC-09 is not yet specified. Do not invent an unwritable-destination preparation
here. A pass cannot close MUST-22 or MUST-53 because the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## OP-004 — Verify that storage exhaustion is not reported as a successful complete evaluation

### Requirements

- MUST-22
- MUST-53

Passing this case does not close MUST-22: other failed-read, write, parse,
subprocess, and walk paths remain. Passing this case does not close MUST-53:
pass, finding, usage, and environment exit distinctions are not this case.

EC-09 is not yet specified. Storage exhaustion has no reliable preparation
procedure. Do not invent one here. A pass cannot close MUST-22 or MUST-53
because the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## OP-005 — Verify that a process killed during check is not treated as a successful complete evaluation

### Requirements

- MUST-22
- MUST-35
- MUST-46
- MUST-53

Passing this case does not close MUST-22: other failed-read, write, parse,
subprocess, and walk paths remain. Passing this case does not close MUST-35:
atomic concurrent writes and cache-failure paths are not this case. Passing
this case does not close MUST-46: the case is not executable. Passing this
case does not close MUST-53: pass, finding, usage, and environment exit
distinctions are not this case.

EC-09 is not yet specified. Do not invent a repeatable execution window or
controlled termination point here. A pass cannot close these requirements
because the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## OP-006 — Verify that a cache failure is not treated as a successful complete evaluation

### Requirements

- MUST-22
- MUST-35
- MUST-53

Passing this case does not close MUST-22: other failed-read, parse, subprocess,
and walk paths remain. Passing this case does not close MUST-35: concurrent
writers and interruption are not this case. Passing this case does not close
MUST-53: pass, finding, usage, and environment exit distinctions are not this
case.

SDD §8 records that direct cache writes are non-atomic and cache-write failure
is warning-only. That open violation is not a named REG-id. A pass on this
case would not close MUST-35.

No specified cache-failure injection exists. EC-09 is not yet specified. Do
not invent that procedure here. A pass cannot close these requirements
because the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
  this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
  directly contradicts the suite objective. Partial or failed execution
  represented as a successful complete evaluation is a failure.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
  unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.
