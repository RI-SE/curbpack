# UV — User and organisational-use validation

## Objective

Representative users must be able to perform the defined handoff and
correctly interpret what a Curbpack pass means and does not mean. Where
organisational-use validation is in scope, an authorised security or risk
representative must be able to state permitted and prohibited use and residual
risk from the evidence.

## Test basis

Requirements:

- MUST-60

Other test basis:

- SDD §1 publisher, producer, reviewer, and agent responsibilities.
- SDD §10 no-code operation and human-review interpretation boundary.

## Test case catalogue

| ID | Test case / purpose | Test class | Procedure status |
|---|---|---|---|
| UV-001 | Builder installs or uses the frozen binary | A | Executable |
| UV-002 | Builder interprets seeded results | A | Executable |
| UV-003 | Builder corrects one structural gap | A | Executable |
| UV-004 | Builder creates a Review Pack | A | To be specified |
| UV-005 | Reviewer reads identity from the handoff | A | To be specified |
| UV-006 | Reviewer compares machine JSON to summary | A | To be specified |
| UV-007 | Organisational permitted-use decision | A | To be specified |
| UV-008 | Buyer/reviewer comparison of two Review Packs | B | To be specified |

## UV-001 — Builder installs or uses the frozen binary

### Prerequisites / SETUP

- Repository state: no R-id.
- Pack input: no PF-id.
- Execution configuration: no EC-id; record the clean platform/environment.
- Other prerequisite: a representative builder selected by the assignment and
  the frozen release’s documented installation path.

1. Fill the test record **Run** table (include the tag if a shipped
   binary is in scope).
2. Give the builder only the documented install path
   ([install](../../getting-started/install.md) or the freeze’s release
   notes). Clean machine or clean PATH. No live author coaching.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | Builder installs or runs the frozen `curbpack` | Task completes without live product-author support |
| 2 | Assistance given | Written on the test record |

### TEARDOWN

None.

## UV-002 — Builder interprets seeded results

### Prerequisites / SETUP

- Repository state: R2
- Pack input: PF-01
- Execution configuration: EC-01
- Other prerequisite: the builder has completed UV-001 or already has the
  frozen binary available.

1. The facilitator runs
   `./external_test/curbpack/setup.sh R2 <pin> --commit` from the
   reference-product root.
2. The facilitator runs
   `export CURBPACK_PACKS_DIR="$(pwd)/external_test/curbpack/packs"` in the
   builder’s shell and confirms `SECURITY.md` is absent.
3. Do not tell the builder the expected gate ID or interpretation.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | Builder runs `curbpack check` and explains the first results, including the failure | Interpretation matches documented semantics; no coaching |

### TEARDOWN

None. Leave the R2 checkout for UV-003 if that case is next.

## UV-003 — Builder corrects one structural gap

### Prerequisites / SETUP

- Repository state: R2 at the start of the case
- Pack input: PF-01
- Execution configuration: EC-02 after the builder restores the file
- Other prerequisite: the builder has the frozen binary available.

1. The facilitator independently prepares R2 with
   `./external_test/curbpack/setup.sh R2 <pin> --commit`, selects PF-01, and
   confirms `SECURITY.md` is absent.
2. Tell the builder only that the reported missing-file finding should be
   corrected using the product baseline.
3. If the builder asks for the exact Git operation, record that assistance;
   the deterministic restoration command is
   `git show <pin>:SECURITY.md > SECURITY.md`.

### STIMULI / RESPONSE

| Step | Stimuli | Response |
|---|---|---|
| 1 | Builder restores `SECURITY.md` from `<pin>` and reruns `curbpack check` | `HOUSE-SECURITY-MD` gone; unrelated results stay |

### TEARDOWN

None. Next `setup.sh` resets the reference product.

## Suite verdict

- **PASS** — all applicable cases required by the verification assignment for
  this suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
  directly contradicts the suite objective. Inability to perform the selected
  handoff or material misinterpretation of a Curbpack pass is a failure.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
  unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.
