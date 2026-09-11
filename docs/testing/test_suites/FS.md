# FS — Repository boundary and file handling

## Objective

Repository traversal and output handling must remain within documented
boundaries. Out-of-scope content must not influence a valid result or exported
Review Pack.

## Test basis

Requirements:

- MUST-40
- MUST-42

## Test case catalogue

| ID | Test case / purpose | Test class | Procedure status |
|---|---|---|---|
| FS-001 | Relative path escape (`../../../etc/passwd`) | A | Executable |
| FS-002 | Absolute, drive-qualified, mixed-separator and reserved paths | A | To be specified |
| FS-003 | Symbolic link to content outside the repository | A | To be specified |
| FS-004 | Nested symbolic links and symbolic-link loop | A | To be specified |
| FS-005 | Access to `.git` or aliases into `.git` | A | To be specified |
| FS-006 | Output destination outside the allowed destination | A | To be specified |
| FS-007 | Unusual filenames and file types | B | To be specified |

## FS-001 — Relative path escape

### Prerequisites / SETUP

- Repository state: no R-id; use a clean throwaway repository.
- Pack input: PF-03 (`path-traversal`)
- Execution configuration: EC-01

1. Fill the test record **Run** table so `<curbpack>` is known.
2. Create a **throwaway repo**: empty folder, `git init`, one empty commit.
   Do not invent a pack file. Do not use the reference product.
3. `export CURBPACK_PACKS_DIR=<curbpack>/testdata/adversarial/packs`
4. Confirm `<curbpack>/testdata/adversarial/packs/path-traversal/pack.json`
   exists (`path` is `../../../etc/passwd`).

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | In the throwaway repo: `curbpack check --packs path-traversal` | Exit ≠ 0 |
| 2 | Read stderr or JSON | Traversal refused at load, or finding `ADV-TRAVERSAL` |
| 3 | Same run | Out-of-repo content does not become a pass. No panic |

### TEARDOWN

None. Leave the throwaway folder.

## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
  this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
  directly contradicts the suite objective. Out-of-scope content influencing a
  valid result or exported Review Pack is a failure.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
  unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.
