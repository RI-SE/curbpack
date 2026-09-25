# RB — Resource and concurrency handling

## Objective

Representative or large inputs and concurrent execution must not produce
silent truncation, corruption, cross-run mixing or false pass results.

## Test basis

Requirements addressed by this suite:

- MUST-35
- MUST-44

Other test basis:

- SDD §7.3 interruption-recovery expectations.
- SDD §7.4 required concurrent-writer case.

A test execution is always part of a test run that starts with [Prepare a verification run](../../docs/testing/procedures/README.md).
In short it encompasses cloning the reference product into `<curbpack>/tmp/cyberready-test-product`,
using the recorded `<commit hash>` and `<date>`, and building the CLI. This is done once for a test run.

Each executable case starts the same way: from the Curbpack root, `source tmp/verification-run.sh`. That restore puts the disposable reference product back at the frozen baseline. You can run the cases in any order. Do not keep using the previous case’s directory. Then prepare the case’s named R-state via product `setup.sh` on that already-restored baseline. Then apply EC as the case states. No RB case is currently executable. Do not invent an R-id or a `tmp/R*` repository. [EC-08](../../docs/testing/procedures/README.md#execution-configurations) is not yet specified; do not improvise overlapping-execution preparation in a case.

## Test suite overview


| ID     | Test case / purpose                                      | Requirements addressed | Test class | Procedure status |
| ------ | -------------------------------------------------------- | ---------------------- | ---------- | ---------------- |
| RB-001 | Representative-large input                               | MUST-44                | B          | To be specified  |
| RB-002 | Unusually large input                                    | MUST-44                | B          | To be specified  |
| RB-003 | Long/cyclic traversal and large malformed content        | MUST-44                | A          | To be specified  |
| RB-004 | Concurrent local output/cache use                        | MUST-35                | B          | To be specified  |


---

## RB-001 — Verify that representative-large input does not produce silent truncation, corruption, or a false pass

### Requirements

- MUST-44

Passing this case does not close MUST-44: unusually large input, long/cyclic
traversal, large malformed content, and the complete set of explicit per-file,
total-byte, file-count, subprocess-time, and captured-output limits are not
this case. See INV-06 in [SDD §8](../../docs/software-design-document.md)
(Partial; review caps exist, evaluator-wide budgets do not). [CR-11](../../docs/testing/procedures/2_code_review_procedures.md)
remains an independent review activity; a pass on this case would not close it.

No specified R-state is a representative-large tree. R1–R5 are not this
condition. MUST-44’s explicit limits are not recorded as executable values.
Do not invent those limits, an R-id, or expected JSON here. A pass cannot
close MUST-44 because the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## RB-002 — Verify that unusually large input does not produce silent truncation, corruption, or a false pass

### Requirements

- MUST-44

Passing this case does not close MUST-44: representative-large input,
long/cyclic traversal, large malformed content, and the complete set of
explicit limits are not this case. See INV-06 in
[SDD §8](../../docs/software-design-document.md) (Partial; review caps exist,
evaluator-wide budgets do not). [CR-11](../../docs/testing/procedures/2_code_review_procedures.md)
remains an independent review activity; a pass on this case would not close it.

No specified R-state is an unusually large tree. R1–R5 are not this
condition. MUST-44’s explicit limits are not recorded as executable values.
Do not invent those limits, an R-id, or expected JSON here. A pass cannot
close MUST-44 because the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## RB-003 — Verify that long/cyclic traversal and large malformed content do not produce silent truncation, corruption, or a false pass

### Requirements

- MUST-44

Passing this case does not close MUST-44: representative-large and unusually
large input, and the complete set of explicit limits, are not this case. See
INV-06 in [SDD §8](../../docs/software-design-document.md) (Partial; review caps
exist, evaluator-wide budgets do not). [CR-11](../../docs/testing/procedures/2_code_review_procedures.md)
remains an independent review activity; a pass on this case would not close it.

No specified R-state is a long/cyclic or large-malformed tree. R1–R5 are not
this condition. MUST-44’s explicit limits are not recorded as executable
values. Do not invent those limits, an R-id, a traversal fixture, or expected
JSON here. A pass cannot close MUST-44 because the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## RB-004 — Verify that concurrent local output/cache use does not mix or corrupt results

### Requirements

- MUST-35

Passing this case does not close MUST-35: interruption and cache-failure
paths are OP-005 and OP-006, not this case. See INV-08 in
[SDD §8](../../docs/software-design-document.md) (Failing). SDD §8 records that
direct cache writes are non-atomic and cache-write failure is warning-only.
That open violation is not a named REG-id. A pass on this case would not
close MUST-35.

Intended later: overlap local checks against the same controlled output/cache
location and inspect both results for mixing or corruption. That is the
SDD §7.4 required concurrent-writer case.

[EC-08](../../docs/testing/procedures/README.md#execution-configurations) is not yet specified.
A repeatable synchronization mechanism and exact shared output/cache target
have not yet been defined. Do not invent that procedure, an R-id, or expected
JSON here. A pass cannot close MUST-35 because the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
  this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
  directly contradicts the suite objective. Silent truncation, corruption,
  cross-run mixing, or a false pass is a failure.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
  unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.
