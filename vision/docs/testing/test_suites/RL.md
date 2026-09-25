# RL — Release artefact and platform verification

## Objective

Publicly supported release artefacts must be installable and executable
through the documented paths and traceable to the stated release source, tag
and checksums to the degree claimed.

## Test basis

Requirements addressed by this suite:

- MUST-80
- MUST-83
- MUST-84

Other test basis:

- SDD §13 required release evidence and supporting-platform boundary.

A test execution is always part of a test run that starts with [Prepare a verification run](../procedures/README.md).
In short it encompasses cloning the reference product into `<curbpack>/tmp/cyberready-test-product`,
using the recorded `<commit hash>` and `<date>`, and building the CLI. This is done once for a test run.

Each executable case starts the same way: from the Curbpack root, `source tmp/verification-run.sh`. That restore puts the disposable reference product back at the frozen baseline. You can run the cases in any order. Do not keep using the previous case’s directory. RL-004 then inspects the named release tag, source commit, checksums, and the artefact this run actually executed. It does not prepare an R-id and does not create a `tmp/R*` repository. RL-001 to RL-003 are not executable until EC-10 exists. Do not invent that platform-execution procedure here. RL-005 is not executable; do not invent a workflow-artefact procedure here.

## Test suite overview


| ID     | Test case / purpose                                      | Requirements addressed | Test class | Procedure status |
| ------ | -------------------------------------------------------- | ---------------------- | ---------- | ---------------- |
| RL-001 | Install shipped artefact on each claimed platform        | MUST-84                | B          | To be specified  |
| RL-002 | Same small case set on each claimed platform             | MUST-84                | B          | To be specified  |
| RL-003 | Cross-platform identity comparison                       | MUST-84                | B          | To be specified  |
| RL-004 | Source-to-release correspondence                         | MUST-83                | B          | Executable       |
| RL-005 | Build and release workflow artefacts                     | MUST-80, MUST-83       | B          | To be specified  |


---

## RL-001 — Verify that a shipped artefact installs on each claimed platform

### Requirements

- MUST-84

Passing this case does not close MUST-84: representative workflow execution
and Windows promotion are not this case. [EC-10](../procedures/README.md#execution-configurations)
is not yet specified. Do not invent a platform-execution procedure here.
A pass cannot close MUST-84 because the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## RL-002 — Verify that the same small case set runs on each claimed platform

### Requirements

- MUST-84

Passing this case does not close MUST-84: installation and cross-platform
identity are not this case. [EC-10](../procedures/README.md#execution-configurations)
is not yet specified. Do not invent a platform-execution procedure here.
A pass cannot close MUST-84 because the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## RL-003 — Verify cross-platform identity comparison

### Requirements

- MUST-84

Passing this case does not close MUST-84: installation and representative
workflow execution are not this case. [EC-10](../procedures/README.md#execution-configurations)
is not yet specified. Do not invent a platform-execution procedure here.
A pass cannot close MUST-84 because the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## RL-004 — Verify source-to-release correspondence

### Requirements

- MUST-83

SDD MUST-83 requires release binaries to have reproducible build inputs,
checksums, least-privilege workflows, and immutable release references.

This case exercises only the **checksums** and **source correspondence**
clauses of MUST-83:

- **Checksums** — an observed match or gap between published checksum
  evidence and the named shipped artefact; absence of a published checksum
  for that artefact (no list, or a list with no entry for it) is an observed
  gap — do not invent a checksum; when a list includes the named artefact,
  compare that entry to the artefact this run actually executed; and
- **Source correspondence** — an observed trace of the named shipped artefact
  to the stated release tag and source commit recorded in the verification
  assignment.

Reproducible build inputs, least-privilege workflows, and immutable release
references are not this case. RL-005 is not executable; do not invent those
procedures here. A pass does not close MUST-83.

### SETUP

- Repository state: no R-id. This case compares a named release artefact to
  stated source, not a reference-product content state. Do not run `setup.sh`.
  Do not create `tmp/R*`.
- Pack input: no PF-id.
- Execution configuration: no EC-id. Platform execution is catalogue scope in
  RL-001 to RL-003.


| Step | Action                                                                                                                                           | Expected result                                                                                                                                                                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | From the **Curbpack** repository root, run `source tmp/verification-run.sh`. Compare the printed values with the selected verification baseline. | `Verification run configuration: OK` is printed. `Curbpack commit` and `Reference-product commit` exactly match the selected baseline. `As-of date` is the date fixed for this test run. The two repository paths identify the intended local checkouts. The disposable reference-product checkout is restored to `$REFERENCE_PRODUCT_COMMIT`. Otherwise, stop. |
| 2    | Remain at `$CURBPACK_ROOT`. Do not `cd "$REFERENCE_PRODUCT_ROOT"` for this case. Do not prepare an R-state.                                       | Current directory is `$CURBPACK_ROOT`.                                                                                                                                                                                                                                                                                                                          |
| 3    | Confirm the verification assignment names a frozen release tag, source commit, and shipped artefact. Record those three values. If any is missing, stop. | The three named values are recorded. This case does not invent a tag, commit, or artefact. Otherwise, stop: the case cannot be run.                                                                                                                                                                                                                            |
| 4    | Open the GitHub (or other documented) release for that tag. Download the published checksum list if any.                                         | The release page is for the named tag. A checksum list is retained when the release publishes one. If there is no list, or the list has no entry for the named shipped artefact, record absent published checksum evidence; do not fill in or compute a checksum.                                                                                                                                                               |


### TEST STEPS


| Step | Action                                                                                                               | Expected result                                                                                                                                                                                                 |
| ---- | -------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Compare the named tag and source commit to the named shipped artefact this run actually executed. For checksums: if SETUP recorded absent published checksum evidence for that artefact, record an observed checksum gap; otherwise compare the listed checksum to the artefact and record an observed match or gap. | Source correspondence and checksums are observed matches or observed gaps only. A missing checksum list or missing list entry for the named artefact is an observed checksum gap, not a pass. Do not infer a match from a tag name, a nearby commit, or an unpublished checksum. Do not invent a checksum value.                                              |
| 2    | Any gap from Step 1                                                                                                  | Write it on the test record. Do not infer a match.                                                                                                                                                              |


---

## RL-005 — Verify build and release workflow artefacts

### Requirements

- MUST-80
- MUST-83

Passing this case does not close MUST-80: the standard-library and
optional-adapter boundary is not an executable procedure here. Passing this
case does not close MUST-83: source correspondence is RL-004; reproducible
build inputs, least-privilege workflows, and immutable release references
are not specified here. Do not invent those procedures. A pass cannot close
either requirement because the case is not executable.

### SETUP

Not specified yet. Do not run this case.

### TEST STEPS

Not specified yet.

---

## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
directly contradicts the suite objective. A publicly supported artefact that
is not installable, executable, or traceable to the degree claimed is a
failure.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.
