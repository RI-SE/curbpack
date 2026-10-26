# DT — Determinism and finding identity

## Objective

Equivalent inputs in scope of the selected pack must produce equivalent
semantic results and stable finding identities. Controlled changes should
affect only expected findings or explicitly dependent fields.

## Test basis

Requirements addressed by this suite:

- MUST-30
- MUST-31

Other test basis:

- SDD §7.3 deterministic-behavior and exact-evidence expectations.

A test execution is always part of a test run that starts with [Prepare a verification run](../docs/procedures/README.md).
In short it encompasses cloning the reference product into `<curbpack>/tmp/cyberready-test-product`,
using the recorded `<commit hash>` and `<date>`, and building the CLI. This is done once for a test run.

Each executable case starts the same way: from the Curbpack root, `source tmp/verification-run.sh`. That restore puts the disposable reference product back at the frozen baseline. You can run the cases in any order. Do not keep using the previous case’s directory. Then prepare the case’s named R-state: R1 or R2 via product `setup.sh` on that already-restored baseline. Then apply EC as the case states. DT-001, DT-003, and DT-004 write JSON under Curbpack `tmp/dt-001`, `tmp/dt-003`, and `tmp/dt-004`. Those directories are evidence. They are not an R-id and not a `tmp/R*` repository. DT-003 prepares R1, retains one check JSON, then prepares R2 on the same checkout. TEST STEPS consume R2.

## Test suite overview


| ID     | Test case / purpose                                      | Requirements addressed | Test class | Procedure status |
| ------ | -------------------------------------------------------- | ---------------------- | ---------- | ---------------- |
| DT-001 | Repeatability of identical inputs                        | MUST-30                | A          | Executable       |
| DT-002 | Locale and timezone variation                            | MUST-31                | B          | To be specified  |
| DT-003 | Controlled change sensitivity                            | —                      | A          | Executable       |
| DT-004 | Finding identity stability                               | —                      | A          | Executable       |


---

## DT-001 — Verify that identical inputs produce the same semantic result

### SETUP

- R1 via Studio fixture; seven claims; packs from `external_test/curbpack-studio/packs`.

### TEST STEPS


| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1    | Run `python3 -m checks ... --out tmp/dt-001/run-$i.json` twenty times | Each exit is `0`. Every claim status is `pass`. |
| 2    | Compare `[.claims[] | {id, status}]` across the 20 files | The claim-status maps are identical. |

Observation is claim status in run-result JSON, not old `outcome` / `readiness_score` / `.curbpack` digests.

---

## DT-002 — Verify that locale and timezone variation does not change the result

### TEST STEPS

Note: not specified yet. Do not run this case. The old curbpack observation is not used.

---

## DT-003 — Verify that a controlled change affects only expected findings

### SETUP

- R1 then R2 via Studio fixture; seven claims each time.

### TEST STEPS


| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1    | After R2, `python3 -m checks ... --out tmp/dt-003/r2.json` | `HOUSE-SECURITY-MD` status is `fail`. |
| 2    | Process exit code | Non-zero. |
| 3    | Compare retained R1 run-result with R2 | R1 has `HOUSE-SECURITY-MD` `pass`; R2 has `fail`; claim-status maps differ. |

---

## DT-004 — Verify that finding identity is stable under equivalent runs

### SETUP

- Twenty R1 runs, then R2; seven claims.

### TEST STEPS


| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1    | Across 20 R1 run-result files | Each has `HOUSE-SECURITY-MD` status `pass`. |
| 2    | Compare R1 to R2 run-result | R2 has `HOUSE-SECURITY-MD` status `fail`. |
