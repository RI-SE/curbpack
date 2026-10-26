# EV — Evaluation semantics

## Objective

Supported checks must report their defined result states correctly. Missing,
unreadable, unsupported or skipped required targets must never be represented
as passed.

## Test basis

Requirements addressed by this suite::

- MUST-22
- MUST-23
- MUST-24
- MUST-53

A test execution is always part of a test run that starts with [Prepare a verification run](../docs/procedures/README.md).
In short it encompasses cloning the reference product into `<curbpack>/tmp/cyberready-test-product`,
using the recorded `<commit hash>` and `<date>`, and building the CLI. This is done once for a test run.

Each executable case starts the same way: from the Curbpack root, `source tmp/verification-run.sh`. That restore puts the disposable reference product back at the frozen baseline. You can run the cases in any order. Do not keep using the previous case’s directory. Then prepare the case’s named R-state through product `setup.sh` on that already-restored baseline. Then apply EC as the case states.

## Test suite overview


| ID     | Test case / purpose                                               | Requirements addressed | Test class | Procedure status |
| ------ | ----------------------------------------------------------------- | ---------------------- | ---------- | ---------------- |
| EV-001 | Good reference product yields a pass                              | MUST-53                | A          | Executable       |
| EV-002 | Missing required file yields a fail                               | MUST-53                | A          | Executable       |
| EV-003 | Missing required section yields a fail                            | —                      | A          | Executable       |
| EV-004 | Unreadable required target is not reported as a pass              | MUST-22, MUST-24       | A          | Executable       |
| EV-005 | Skipped, excluded or unsupported target is not treated as a pass  | MUST-23                | A          | Executable       |
| EV-006 | Token-only text does not yield a pass                             | —                      | A          | Executable       |
| EV-007 | Each supported check type fails when its condition is changed     | —                      | A          | Executable       |
| EV-008 | Outcome does not depend on rule order or file order               | —                      | A          | Partial (A executable; B blocked) |
| EV-009 | Thin rule-satisfying text yields a pass without a substance claim | —                      | A          | Executable       |


---

## EV-001 — Verify that a good reference product yields a pass

### Requirements

- MUST-53

### SETUP

- Repository state: R1 via `SUT=curbpack-studio ./setup.sh R1 --commit` under `external_test/curbpack-studio`.
- Claims: the seven carried claim files from that fixture.
- Packs: `$REFERENCE_PRODUCT_ROOT/external_test/curbpack-studio/packs`.

### TEST STEPS


| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1    | `python3 -m checks --repo "$REFERENCE_PRODUCT_ROOT" --packs "$REFERENCE_PRODUCT_ROOT/external_test/curbpack-studio/packs" --out "$REFERENCE_PRODUCT_ROOT/run-result.json"` (after writing `curbpack.json` and copying the seven claims) | Stdout includes `claims 7 exit 0`. Every claim status in `run-result.json` is `pass`. |
| 2    | Process exit code | `0`. |

When `tmp/suit-runner/EV-001.carried` exists (after `make test-curbcheck` carried run), this row is not re-executed.

---

## EV-002 — Verify that a missing required file yields a fail

### Requirements

- MUST-53

### SETUP

- Repository state: R2 via Studio fixture `setup.sh`.
- Claims: the seven carried claims.

### TEST STEPS


| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1    | `python3 -m checks ... --out run-result.json` | Claim `HOUSE-SECURITY-MD` has status `fail` in `run-result.json`. |
| 2    | Process exit code | Non-zero. |

---

## EV-003 — Verify that a missing required section yields a fail

### TEST STEPS

Note: outside — MD-SW-CLASS claim does not exist in the Studio fixture; the old curbpack observation is not used.

---

## EV-004 — Verify that an unreadable required target is not reported as a pass

### TEST STEPS

Note: outside — unreadable target raises PermissionError; the old curbpack stderr observation is not used.

---

## EV-005 — Verify that a skipped, excluded or unsupported target is not treated as a pass

### TEST STEPS

Note: outside — needs `--diff` / skipped_rules / `.curbpack` cache fields Studio does not write; the old curbpack observation is not used.

---

## EV-006 — Verify that token-only text does not yield a pass

### SETUP

- Repository state: R4 via Studio fixture, then append a `TODO` line to `SECURITY.md` so the current `placeholder` probe fails (R4 token-only alone does not).
- Claims: house-policy exist/contents claims (`HOUSE-ANTI-PLACEHOLDER`, `HOUSE-SECURITY-MD`, `HOUSE-SECURITY-TXT`).

### TEST STEPS


| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1    | `python3 -m checks ... --out run-result.json` | Claim `HOUSE-ANTI-PLACEHOLDER` status is `fail`. |
| 2    | Process exit code | Non-zero. |

---

## EV-007 — Verify that each supported check type fails when its condition is changed

### EV-007-A — exist/contents missing SECURITY.md (R2)


| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1    | `python3 -m checks` after R2 + seven claims | `HOUSE-SECURITY-MD` status `fail`; process exit non-zero. |

### EV-007-B — MD-SW-CLASS (outside)

Note: outside — MD-SW-CLASS claim does not exist; the old curbpack observation is not used.

### EV-007-C — placeholder probe (R4 + TODO)


| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1    | `python3 -m checks` after R4, append TODO to SECURITY.md, house claims | `HOUSE-ANTI-PLACEHOLDER` status `fail`; process exit non-zero. |

### EV-007-D — dep_ban house (outside)

Note: outside — needs `dep_ban` / HOUSE-DEP-AXIOS-PIN; dep_ban is not installed.

### EV-007-E — dep_ban cra (outside)

Note: outside — needs `dep_ban` / CRA-DEP-AXIOS-PIN; dep_ban is not installed.

### EV-007-F — secret paths pattern (outside)

Note: outside — HOUSE-SECRET-PATHS fails on absent paths before pattern; the old curbpack observation is not used.

### EV-007-G — fresh/owned stale (outside)

Note: outside — missing checkers `fresh` / `owned` / `git_signed` / `git_signer`; not implemented for this case.

### EV-007-H — fresh/owned wrong author (outside)

Note: outside — missing checkers `fresh` / `owned` / `git_signed` / `git_signer`; not implemented for this case.

---

## EV-008 — Verify that outcome does not depend on rule order or file order

### EV-008-A — rule order packs (outside)

Note: outside — EV-008 special rule-order packs are not rewritten to Packs v2; the old curbpack observation is not used.

### EV-008-B — file order (blocked)

Note: blocked — missing test seam; the old curbpack observation is not used.

---

## EV-009 — Verify that thin rule-satisfying text yields a pass without a substance claim

### SETUP

- Repository state: R5 via Studio fixture (`CURBPACK_ROOT` = Studio root for `testdata/`).
- Claims: house-policy exist/contents claims only.

### TEST STEPS


| Step | Action | Expected result |
| ---- | ------ | --------------- |
| 1    | `python3 -m checks ... --out run-result.json` | `HOUSE-ANTI-PLACEHOLDER`, `HOUSE-SECURITY-MD`, and `HOUSE-SECURITY-TXT` each have status `pass`. Stdout includes `claims 3 exit 0`. |
| 2    | Process exit code | `0`. |
