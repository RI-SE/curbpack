# Curbpack Verification Strategy

This document defines the reusable verification approach for Curbpack. It
describes what is verified, how test inputs are controlled, how test cases are
grouped, and how results are classified.

To **start a verification run**, follow this order: this Verification  
Strategy, the [verification plan](verification_plan.md), [test procedures](procedures/README.md), [test-suites](test_suites/README.md), then  
[generated-test-record-template](generated_test_record_template.md). Do not start in a suite file.

## 2. System under test and boundary

### 2.1 System under test

The system under test (SUT) is Curbpack: the released command-line software,
rule-pack evaluation logic, machine-readable result, and Review Pack workflow
included in the release under review.

The Curbpack source repository is the implementation examined during
independent code and release review.

Repositories, files, rule packs, pack instances, and seeded defects used
during testing are test inputs. They are not additional systems under test.

### 2.2 Intended use

Curbpack evaluates declared structural conditions in a Git repository against
a selected rule pack. It records findings against the examined repository
state and prepares selected material for human review.

Typical checks include the presence of required files, sections, owners, and
references when the selected pack defines those checks.

### 2.3 Explicit non-use

Curbpack does not determine whether repository documentation is true,
sufficient, or technically correct. A structural pass does not by itself
establish security, compliance, certification, legal sufficiency, clinical
adequacy, CE marking, or product acceptance.

### 2.4 Failure boundary

Verification includes malformed or misleading inputs, path and output
handling, operational failures, provenance, and Review Pack consistency.

It does not treat Curbpack as a vulnerability scanner for the product
represented by the repository under examination.

## 3. Verification setups

Since curbpack inspects other product repositories, we need to have a reference product repository (see 3.1)  that contains everything curbpack is looking for to make our positive tests.  For negative testing, e.g. when things are missing or malformed, we have defined a set of repository states. Curbpack defines what each R-state means. The reference product holds the scripts (`states/R*.sh`) that create those states. Some scripts mutate a copy of the reference product. R4 and R5 instead build disposable trees from Curbpack testdata. We call this reference product repository the "controlled repository".  

Other prefequisites for the cases are pack-input `(PF-*)`, and execution-configuration (EC-*)  as defined in [test procedures](procedures/README.md).

### 3.1 Reference test product

Use the **reference product** (Glucose Log, repository
`cyberready-test-product`) with the files, pack copies, and claims that
live in that product. Each verification run freezes one reference-product
commit.

Named states `R1` through `R5` are defined in [controlled-repo-setup](procedures/0_controlled_repo_setup.md). A
state is repository content: which files and text are present or absent. The
pack input and execution configuration are separate prerequisite dimensions.

### 3.2 Other target repositories

Future verification may include using real product repositories, but that requires adapting  pack templates and state scripts (`R-*.sh`) to the other repository. This  is not yet specified.

## 4. Frozen test baseline

A verification run is executed against one frozen baseline. It comprises:

- the Curbpack commit hash;
- the pack files used in that run;
- the starting Glucose Log commit (assignment hash, else
`tests/cyberready-test-product.pin`, else the product’s `main`);
- the revision of the approved procedures, cases, and expected results.

R-state scripts come from that starting commit. Local `test_*`
branches are not product history.

The baseline SHALL remain unchanged for a complete verification run.

## 5. Verification activities

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
[test-suites](test_suites/README.md).

The results of each execution is written on a test record copied from
[generated-test-record-template](generated_test_record_template.md), kept with the
assignment. Filled records are not committed to the public Curbpack
repository. Those records are not the executable test interface.  

## 6. Test suites

How to start a verification run, and the suite files themselves, are in
[test-suites](test_suites/README.md).

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


`CR` identifies code and release review activities, not a functional suite.
The procedure is [code-review](procedures/2_code_review_procedures.md).

## 7. Test classes

Each formal case has a **test class**. The class expresses priority and
applicability; it does not change the expected technical behaviour.


| Class | Meaning                                                       |
| ----- | ------------------------------------------------------------- |
| **A** | Core case; normally included when its function is in scope.   |
| **B** | Extended case for assignments that require broader coverage.  |
| **C** | Conditional case; run only when its capability applies.       |
| **D** | Exploratory case; run when selected or prompted by a finding. |


The Verification Plan determines which Test classes are required
for the verification campaign.

## 8. Results

### 8.1 Case disposition

Test executions use these dispositions:


| Status             | Meaning                                                        |
| ------------------ | -------------------------------------------------------------- |
| **Pass**           | Observed result on the test record matches expectations.       |
| **Fail**           | Result differs materially or breaches an acceptance criterion. |
| **Blocked**        | A prerequisite is unavailable. Blocked is not Pass.            |
| **Not applicable** | The case does not apply; the reason is recorded.               |
| **Inconclusive**   | Observations are conflicting or insufficient.                  |


### 8.2 Suite verdict

Each functional or validation suite records one of these verdicts for the
verification run:

- **PASS** — all applicable cases required by the verification assignment for
the suite have passed, and no open finding contradicts the suite objective.
- **FAIL** — at least one required case has failed, or other verified evidence
directly contradicts the suite objective.
- **INCONCLUSIVE** — evidence needed for the required suite coverage is
unavailable, blocked, or not yet executable.
- **NOT ASSESSED** — the suite was not selected for this verification run.

The Verification Plan determines which Test classes are required
for the verification campaign.

## 9. Findings and retest

A failed test or review may create a finding. A finding records the affected
baseline, condition, expected and observed behaviour, the test record,
impact, and disposition.

Corrections are verified against a separately frozen corrected baseline using
the original test case and relevant regression cases.