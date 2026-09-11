# PV — State and provenance

## Objective

The result must identify the examined repository state, Curbpack version,
selected pack identity and other required method information sufficiently for
independent review and reproduction.

## Test basis

Requirements:

- MUST-31

Other test basis:

- SDD §1 portable-evidence and independent-inspection product claim.
- SDD §7.3 frozen, independently authored evidence expectations.

## Test case catalogue

| ID | Test case / purpose | Test class | Procedure status |
|---|---|---|---|
| PV-001 | Clean committed repository state (EC-01) | A | Executable |
| PV-002 | Dirty working tree (EC-02) | A | Executable |
| PV-003 | Detached HEAD (EC-03) | A | Executable |
| PV-004 | Shallow clone / other Git-state variants (EC-04, EC-05) | C | To be specified |
| PV-005 | Pack identity on the output | A | Executable |
| PV-006 | Pack substitution after freeze | A | Executable |
| PV-007 | Tool version, method/schema, platform identity | A | Executable |

## PV-001 — Clean committed repository state

### Prerequisites / SETUP

- Repository state: R1
- Pack input: PF-01
- Execution configuration: EC-01

1. `cd <reference-product-root>`.
2. Run `./external_test/curbpack/setup.sh R1 <pin> --commit`.
3. Run
   `export CURBPACK_PACKS_DIR="$(pwd)/external_test/curbpack/packs"`.
4. Note `git rev-parse HEAD` and `git status --porcelain` (must be empty).

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | `curbpack check --json --as-of <date>` | Exit 0 |
| 2 | Compare reported repository state in JSON to `git rev-parse HEAD` | The committed state is identified well enough to reproduce the run |
| 3 | `git status --porcelain` | Still empty |

### TEARDOWN

None. Leave the checkout.

## PV-002 — Dirty working tree

### Prerequisites / SETUP

- Repository state: R1 plus the exact uncommitted edit below
- Pack input: PF-01
- Execution configuration: EC-02

1. `cd <reference-product-root>`.
2. Run `./external_test/curbpack/setup.sh R1 <pin>`.
3. Run
   `export CURBPACK_PACKS_DIR="$(pwd)/external_test/curbpack/packs"`.
4. Run `printf '\nPV-002 uncommitted marker\n' >> SECURITY.md`.
5. Verify `git status --porcelain` shows `SECURITY.md` as changed.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | `curbpack check --json --as-of <date>` | Completes |
| 2 | Read how the output describes repository state | Dirty state is visible, or Curbpack refuses to claim a single committed state |

### TEARDOWN

None. The next `setup.sh` discards the dirty tree.

## PV-003 — Detached HEAD

### Prerequisites / SETUP

- Repository state: R1
- Pack input: PF-01
- Execution configuration: EC-03

1. `cd <reference-product-root>`.
2. Run `./external_test/curbpack/setup.sh R1 <pin> --commit`.
3. Run
   `export CURBPACK_PACKS_DIR="$(pwd)/external_test/curbpack/packs"`.
4. Run `git checkout --detach HEAD` and verify
   `git symbolic-ref -q HEAD` exits non-zero.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | `curbpack check --json --as-of <date>` | Completes or explicit unsupported |
| 2 | Read reported state | Correct detached state, or explicit unsupported — not a false committed branch |

### TEARDOWN

None. Leave the checkout.

## PV-005 — Pack identity on the output

### Prerequisites / SETUP

- Repository state: R1
- Pack input: PF-01
- Execution configuration: EC-01

1. `cd <reference-product-root>`.
2. Run `./external_test/curbpack/setup.sh R1 <pin>`.
3. Run
   `export CURBPACK_PACKS_DIR="$(pwd)/external_test/curbpack/packs"`.
4. Note the pack IDs and versions in each selected `pack.json`. Separately
   note the source repository and commit in
   `external_test/curbpack/packs/SOURCE.txt`; that file does not contain pack
   IDs or versions.

PF-02 does not exist yet; do not invent a second instance.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | `curbpack check --json --as-of <date>` | Exit 0 |
| 2 | Read `pack_id` and any version/digest fields Curbpack actually prints | Matches the PF-01 copies you noted |
| 3 | Same JSON | Does not claim Curbpack inferred a source commit unless the product documents that field |

### TEARDOWN

None.

## PV-006 — Pack substitution after freeze

### Prerequisites / SETUP

- Repository state: R1
- Pack inputs: PF-01 baseline followed by PF-03, an exact modified copy
- Execution configuration: EC-01

1. `cd <reference-product-root>`.
2. Run `./external_test/curbpack/setup.sh R1 <pin>`.
3. Run
   `export CURBPACK_PACKS_DIR="$(pwd)/external_test/curbpack/packs"`.
4. Run `curbpack check --json --as-of <date>` and save the PF-01 JSON.
5. Copy `external_test/curbpack/packs` to a new throwaway folder.
6. Run `printf ' ' >> <throwaway-packs>/house-policy/pack.json` to make one
   controlled byte addition without changing the JSON value.
7. Run `export CURBPACK_PACKS_DIR=<throwaway-packs>` and remain at the
   reference-product root.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | `curbpack check --json --as-of <date>` | Completes or refuses |
| 2 | Compare to the PV-005 JSON | The change is visible, or the run is rejected — not silently the original freeze |

### TEARDOWN

None. Discard the throwaway packs copy. Restore
`CURBPACK_PACKS_DIR` to PF-01 before the next case.

## PV-007 — Tool version, method/schema, platform identity

### Prerequisites / SETUP

- Repository state: R1
- Pack input: PF-01
- Execution configuration: EC-01

1. `cd <reference-product-root>`.
2. Run `./external_test/curbpack/setup.sh R1 <pin>`.
3. Run
   `export CURBPACK_PACKS_DIR="$(pwd)/external_test/curbpack/packs"`.
4. Run `curbpack check --json --as-of <date>` and retain the machine JSON.
5. If Review Pack identity fields are also assessed, generate it using the
   command documented by the frozen Curbpack release and record that exact
   command.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | Read tool, method/schema, and platform fields that are actually present | An independent reviewer can tell which Curbpack version produced the result |
| 2 | Missing required identity | Finding — do not invent the value |

### TEARDOWN

None.

## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
  this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
  directly contradicts the suite objective. Output that silently misidentifies
  repository state, tool version, pack identity, or required method
  information is a failure.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
  unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.
