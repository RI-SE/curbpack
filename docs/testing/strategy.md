# Curbpack Verification Strategy

This document defines the reusable verification approach for Curbpack. It
describes what is verified, how test inputs are controlled, how test cases are
grouped, and how results are classified.

To **start a verification run**, follow this order: this Verification
Strategy, [test procedures](procedures/README.md), [test-suites](../../testing/test_suites/README.md), then
[generated-test-record-template](generated_test_record_template.md). Create the run
with `make start-verification-run`. Do not start in a suite file.

## 2. System Under Test and Boundary

### 2.1 System Under Test

The system under test (SUT) is Curbpack: the released command-line software,
rule-pack evaluation logic, machine-readable result, and Review Pack workflow
included in the release under review.

The Curbpack source repository is the implementation examined during
independent code and release review.

Repositories, files, rule packs, pack instances, and seeded defects used
during testing are test inputs. They are not additional systems under test.

### 2.2 Intended Use

Curbpack evaluates declared structural conditions in a Git repository against
a selected rule pack. It records findings against the examined repository
state and prepares selected material for human review.

Typical checks include the presence of required files, sections, owners, and
references when the selected pack defines those checks.

### 2.3 Explicit Non-Use

Curbpack does not determine whether repository documentation is true,
sufficient, or technically correct. A structural pass does not by itself
establish security, compliance, certification, legal sufficiency, clinical
adequacy, CE marking, or product acceptance.

### 2.4 Failure Boundary

Verification includes malformed or misleading inputs, path and output
handling, operational failures, provenance, and Review Pack consistency.

It does not treat Curbpack as a vulnerability scanner for the product
represented by the repository under examination.

## 3. Verification Setups

Curbpack inspects other product repositories. Verification therefore uses one
reference product (see 3.1) that holds the files, pack copies, and claims
needed for positive tests. Negative tests use named repository states
(R-states). Curbpack defines what each R-state means. The reference product
holds the scripts (`states/R*.sh`) that create those states on the single
disposable checkout for the run. That checkout is
`$CURBPACK_ROOT/tmp/cyberready-test-product` (`$REFERENCE_PRODUCT_ROOT`).
No R-state uses a separate repository such as `tmp/R4` or `tmp/R5`. We call
this reference product the "controlled repository".

How a run is started, how each testcase is started, and how an R-state is
prepared are in [test procedures](procedures/README.md). Other case
prerequisites are pack input (`PF-*`) and execution configuration (`EC-*`)
as defined there.

### 3.1 Reference Test Product

Use the **reference product** (Glucose Log, repository
`cyberready-test-product`) with the files, pack copies, and claims that
live in that product. Each verification run freezes one reference-product
commit.

Named states `R1` through `R5` are defined in
[controlled-repo-setup](procedures/0_controlled_repo_setup.md). An R-state
is the complete prepared repository state a testcase needs: which files and
text are present, absent, or modified, and the Git repository condition
required as the starting point. Pack input and execution configuration are
separate prerequisite dimensions. An execution configuration may add a
testcase-specific condition after that base R-state, such as a deliberate
dirty-tree edit. It does not replace the R-state.

### 3.2 Other Target Repositories

Future verification may include using real product repositories, but that requires adapting  pack templates and state scripts (`R-*.sh`) to the other repository. This  is not yet specified.

## 4. Frozen Test Baseline

A verification run is executed against one frozen baseline. It comprises:

- the Curbpack commit hash;
- the pack files used in that run;
- the starting Glucose Log commit (assignment hash, else
`tests/cyberready-test-product.pin`, else the product’s `main`);
- one `AS_OF_DATE` for every case in the run;
- the revision of the approved procedures, cases, and expected results.

Those values are selected once for the verification run. R-state scripts
come from that frozen reference-product commit. A later testcase does not
select a different product revision.

The baseline SHALL remain unchanged for a complete verification run.

No release tag or shipped artefact is part of the freeze unless a separate
verification assignment names one before entry.

The SDD's own `Verified baseline` field is its historical current-state
register; it does not replace the product source selected for a verification
run. A changed product, requirement, setup, procedure, or expected result
requires a separately frozen run.

## 5. Verification Activities

Verification consists of:

1. pack-template applicability and pack-instance preparation; (Already done in the reference product)
2. controlled repository preparation;
3. functional and robustness test suites;
4. independent code and release review;
5. claim review and user validation; and
6. test recording, findings, and retest.

Controlled prerequisites, execution, and recording rules are in
[test procedures](procedures/README.md). Repository state implementation details are
[controlled-repo-setup](procedures/0_controlled_repo_setup.md); pack input details are [pack-instantiation](procedures/1_pack_template_instantiation.md).
Independent code and release review is [code-review](procedures/2_code_review_procedures.md). The suite index is
[test-suites](../../testing/test_suites/README.md).

The results of each execution is written on a test record copied from
[generated-test-record-template](generated_test_record_template.md), kept with the
assignment. Filled records are not committed to the public Curbpack
repository. Those records are not the executable test interface.

All 55 normative `MUST-*` requirements in SDD §§1.1 and 2.1–2.9 remain in
scope. Mapping to existing test and review evidence is in
[Requirement traceability](requirements_traceability.md). Coverage state
there is test design, not an execution result.

## 6. Test Suites

How to start a verification run, and the suite files themselves, are in
[test-suites](../../testing/test_suites/README.md).

A **test suite** is a related group of cases with a common verification
objective. The suite prefix forms part of each test-case identifier.


| Suite  | Purpose                                        |
| ------ | ---------------------------------------------- |
| **PK** | Rule-pack input validation                     |
| **EV** | Evaluation semantics                           |
| **FS** | Repository boundary and file handling          |
| **DT** | Determinism and finding identity               |
| **PV** | State and provenance                           |
| **RP** | Review Pack, output, and attestation integrity |
| **OP** | Operational failure handling                   |
| **NB** | Network and data boundary                      |
| **RB** | Resource and concurrency handling              |
| **RL** | Release artefact and platform verification     |
| **CL** | Claim review                                   |
| **UV** | User and organisational-use validation         |


All existing functional and validation suites are available for selection.

`CR` identifies code and release review activities, not a functional suite.
The procedure is [code-review](procedures/2_code_review_procedures.md). A
separate verification assignment controls review effort.

## 7. Test Classes

Each formal case has a **test class**. The class expresses priority and
applicability; it does not change the expected technical behaviour.


| Class | Meaning                                                       |
| ----- | ------------------------------------------------------------- |
| **A** | Core case; normally included when its function is in scope.   |
| **B** | Extended case for assignments that require broader coverage.  |
| **C** | Conditional case; run only when its capability applies.       |
| **D** | Exploratory case; run when selected or prompted by a finding. |


Unless a separate assignment records a narrower selection:

- Class A cases are normally required;
- Class B cases are required when the suite contains them;
- Class C cases are required only when the named capability applies to the
  frozen target; and
- Class D cases are not selected unless a recorded finding requires them.

Suite and procedure references to the verification assignment mean this
default scope, unless a separate assignment records a different selection.

## 8. Results

### 8.1 Case Disposition

Test executions use these dispositions:


| Status             | Meaning                                                        |
| ------------------ | -------------------------------------------------------------- |
| **Pass**           | Observed result on the test record matches expectations.       |
| **Fail**           | Result differs materially or breaches an acceptance criterion. |
| **Blocked**        | A prerequisite is unavailable. Blocked is not Pass.            |
| **Not applicable** | The case does not apply; the reason is recorded.               |
| **Inconclusive**   | Observations are conflicting or insufficient.                  |


### 8.2 Suite Verdict

Each functional or validation suite records one of these verdicts for the
verification run:

- **PASS** — all applicable cases required by the verification assignment for
the suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
directly contradicts the suite objective.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.

The required case set for a suite follows the default scope in §7 unless a
separate assignment records a different selection.

## 9. Findings and Retest

A failed test or review may create a finding. A finding records the affected
baseline, condition, expected and observed behaviour, the test record,
impact, and disposition.

Corrections are verified against a separately frozen corrected baseline using
the original test case and relevant regression cases.

## 10. Entry, Exit, and Records

These rules apply to every verification run unless a separate assignment
records a different selection.

### 10.1 Entry

- The Curbpack commit, reference-product commit, pack input, procedure
  revision, and `AS_OF_DATE` are recorded in `tmp/verification-run.sh` and
  remain unchanged for the run.
- The selected Curbpack source can be built, or the assignment records the
  exact shipped artefact.
- Each case chosen for execution has an **Executable** procedure and
  repeatable prerequisites.
- A record store exists outside the public repository.
- Independent reviewers and any applicable release platforms are identified.

### 10.2 Exit

- Every selected Executable case has a test record with Pass, Fail, Blocked,
  Not applicable, or Inconclusive disposition.
- Every selected non-executable case is explicitly retained as unavailable
  evidence; it is not reported as passed.
- Every selected suite has a PASS, FAIL, INCONCLUSIVE, or NOT ASSESSED verdict
  derived from the required case evidence.
- Selected CR activities have completed review protocols or are recorded as
  unavailable.
- Findings identify the affected baseline and evidence.
- Each requirement is assessed as satisfied, not satisfied, or not verified
  from accumulated evidence. Coverage state in
  [Requirement traceability](requirements_traceability.md) is not an
  execution verdict.

### 10.3 Records

- the generated `tmp/verification-run.sh` values for the run;
- one completed test record per case execution;
- retained raw outputs and evidence references;
- one review protocol per selected CR activity;
- suite verdicts with the required case set identified;
- findings and retest records, where applicable; and
- a final requirement assessment based on the recorded evidence.
