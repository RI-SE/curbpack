# FS — Repository boundary and file handling

## Objective

Repository traversal and output handling must remain within documented
boundaries. Out-of-scope content must not influence a valid result or exported
Review Pack.

## Test basis

Requirements addressed by this suite:

- MUST-40
- MUST-42

A test execution is always part of a test run that starts with [Prepare a verification run](../../docs2/testing/procedures/README.md).
In short it encompasses cloning the reference product into `<curbpack>/tmp/cyberready-test-product`,
using the recorded `<commit hash>` and `<date>`, and building the CLI. This is done once for a test run.

Each executable case starts the same way: from the Curbpack root, `source tmp/verification-run.sh`. That restore puts the disposable reference product back at the frozen baseline. You can run the cases in any order. Do not keep using the previous case’s directory. Then prepare the case’s named R-state through product `setup.sh` on that already-restored baseline. Then apply EC and pack input as the case states. FS-001 keeps that R1 checkout and selects [PF-05](../../docs2/testing/procedures/1_pack_template_instantiation.md#pf-05) with `mutate_pack.sh`. It does not create an R-id or a `tmp/R*` repository.

## Test suite overview


| ID     | Test case / purpose                                              | Requirements addressed | Test class | Procedure status |
| ------ | ---------------------------------------------------------------- | ---------------------- | ---------- | ---------------- |
| FS-001 | Relative path escape (`../../../etc/passwd`)                     | MUST-40, MUST-42       | A          | Executable       |
| FS-002 | Absolute, drive-qualified, mixed-separator and reserved paths    | MUST-42                | A          | To be specified  |
| FS-003 | Symbolic link to content outside the repository                  | MUST-42                | A          | To be specified  |
| FS-004 | Nested symbolic links and symbolic-link loop                     | MUST-42                | A          | To be specified  |
| FS-005 | Access to `.git` or aliases into `.git`                          | MUST-40                | A          | To be specified  |
| FS-006 | Output destination outside the allowed destination               | MUST-40                | A          | To be specified  |
| FS-007 | Unusual filenames and file types                                 | MUST-40                | B          | To be specified  |


---

## FS-001 — Verify that relative path escape in pack paths is refused

### Requirements

- MUST-40
- MUST-42

Passing this case does not close MUST-40: the complete untrusted-input set
is not this case. Passing this case does not close MUST-42: absolute paths,
intermediate symlinks, output destinations, and other path forms remain.

The pack is the stimulus. R1 is only the git root required to run `check`.
This case does not invent a new R-id.

### SETUP

- Repository state: [R1](../../docs2/testing/procedures/0_controlled_repo_setup.md#r1) — prepared by `setup.sh` in step 3.
- Pack input: [PF-05](../../docs2/testing/procedures/1_pack_template_instantiation.md#pf-05) (`path-traversal`) — selected by SETUP step 5.
- Execution configuration: [EC-01](../../docs2/testing/procedures/0_controlled_repo_setup.md#ec-01) — established and verified by steps 3–4.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | `cd "$REFERENCE_PRODUCT_ROOT"`                                                                                                                   | Current directory is `$REFERENCE_PRODUCT_ROOT`. E.g. tmp/cyberready-test-product.                                                                                                                                                                                                                                                                               |
| 3    | `./external_test/curbpack/setup.sh R1 --commit`                                                                                                  | Applies R1 to the already-restored frozen baseline. Does not restore the baseline. Prints the R1 state description (required files, heading, `package.json` conditions). Otherwise, stop.                                                                                                                                                                       |
| 4    | `git status --porcelain`                                                                                                                         | No output. Working tree is clean.                                                                                                                                                                                                                                                                                                                               |
| 5    | `./external_test/curbpack/mutate_pack.sh PF-05`                                                                                                  | Prints `mutate_pack.sh: PF-05` and installs `path-traversal/pack.json` under `external_test/curbpack/packs/`. `CURBPACK_PACKS_DIR` stays the verification-run value. Remain at `$REFERENCE_PRODUCT_ROOT`.                                                                                                                                                      |
| 6    | `grep -F '../../../etc/passwd' "$CURBPACK_PACKS_DIR/path-traversal/pack.json"`                                                                   | The traversal path is present in the installed pack. Otherwise, stop.                                                                                                                                                                                                                                                                                           |


### TEST STEPS


| Step | Action                                        | Expected result                                                                                                                                                                                          |
| ---- | --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `curbpack check --packs path-traversal`       | Exit status is non-zero. stderr contains `ADV-TRAVERSAL` and `path traversal refused`. Fail if the command reports a pass or if traversal is not refused. On the verification baseline, stderr is exactly the line `pack "path-traversal" rule "ADV-TRAVERSAL": path traversal refused` and stdout is a blank line followed by `=== CURBPACK CHECK ===`. |


---

## FS-002 — Absolute, drive-qualified, mixed-separator and reserved paths

### Requirements

- MUST-42

Passing this case does not close MUST-42: relative traversal is covered by
FS-001 only; intermediate symlinks and other path forms remain. A pass cannot
close MUST-42 because the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## FS-003 — Symbolic link to content outside the repository

### Requirements

- MUST-42

Passing this case does not close MUST-42: relative pack-path traversal and
nested or cyclic symlink conditions are not this case. A pass cannot close
MUST-42 because the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## FS-004 — Nested symbolic links and symbolic-link loop

### Requirements

- MUST-42

Passing this case does not close MUST-42: relative pack-path traversal and
single-hop symlink escape are not this case. A pass cannot close MUST-42
because the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## FS-005 — Access to `.git` or aliases into `.git`

### Requirements

- MUST-40

Passing this case does not close MUST-40: the complete untrusted-input set
is not this case. A pass cannot close MUST-40 because the case is not
executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## FS-006 — Output destination outside the allowed destination

### Requirements

- MUST-40

Passing this case does not close MUST-40: pack-path traversal, symlink forms,
and other untrusted-input shapes are not this case. A pass cannot close
MUST-40 because the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## FS-007 — Unusual filenames and file types

### Requirements

- MUST-40

Passing this case does not close MUST-40: the complete untrusted-input set
is not this case. A pass cannot close MUST-40 because the case is not
executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
  this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
  directly contradicts the suite objective. Out-of-scope content influencing a
  valid result or exported Review Pack is a failure.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
  unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.
