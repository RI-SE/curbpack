# RL — Release artefact and platform verification

## Objective

Publicly supported release artefacts must be installable and executable
through the documented paths and traceable to the stated release source, tag
and checksums to the degree claimed.

## Test basis

Requirements:

- MUST-80
- MUST-83
- MUST-84

Other test basis:

- SDD §13 required release evidence and supporting-platform boundary.

## Test case catalogue

| ID | Test case / purpose | Test class | Procedure status |
|---|---|---|---|
| RL-001 | Install shipped artefact on each claimed platform | B | To be specified |
| RL-002 | Same small case set on each claimed platform | B | To be specified |
| RL-003 | Cross-platform identity comparison | B | To be specified |
| RL-004 | Source-to-release correspondence | B | Executable |
| RL-005 | Build and release workflow artefacts | B | To be specified |

## RL-004 — Source-to-release correspondence

### Prerequisites / SETUP

- Repository state: no R-id.
- Pack input: no PF-id.
- Execution configuration: no EC-id; platform execution is catalogue scope in
  RL-001 to RL-003.
- Other prerequisite: the verification assignment names a frozen release tag,
  source commit, and shipped artefact.

1. Fill the test record **Run** table, including the release tag if this
   freeze is a shipped artefact.
2. Open the GitHub (or other documented) release for that tag. Download
   the published checksum list if any.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | Compare tag, source commit, manifest, checksums, and the binary you actually ran | The artefact traces to the stated source to the degree claimed |
| 2 | Any gap | Write it on the test record; do not infer a match |

### TEARDOWN

None.

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
