# Independent Verification

Use the verification documents in this order:

1. [Verification Strategy](strategy.md) — how Curbpack is verified in general,
   including default suite and test-class scope.
2. [Requirement traceability](requirements_traceability.md) — maps normative
   requirements to existing test and review evidence. Coverage state is test
   design, not an execution result.
3. [Test Setup](procedures/README.md) — controlled repository state (`R-*`),
   pack input (`PF-*`), and execution configuration (`EC-*`) prerequisites.
   Create a verification run with `make start-verification-run`.
4. [Test Suites and Test Cases](../../testing/test_suites/README.md) — suite objectives, test
   basis, case selection, and executable procedures.
5. [Test Records](generated_test_record_template.md) — one record per case
   execution.

## Reading Model

Product requirements and documented claims are **test basis**. They are not a
verification document layer.

- **Product requirements** are the normative `MUST / MUST NOT` statements
  (`MUST-*`) in [Software Design Document v1.2](../../vision/docs/software-design-document.md)
  §§1.1 and 2.1–2.9.
- **Other test basis** includes documented product claims, intended-use and
  non-use boundaries, release and platform claims, and human-authority limits,
  but only where a suite names them.

The **Verification Strategy** is the reusable method, including the default
suites and test classes. This repository does not maintain a static
verification plan. A verification run is created with
`make start-verification-run`; the resolved Curbpack revision,
reference-product revision, and `AS_OF_DATE` are recorded in
`tmp/verification-run.sh` and in the test records. A generated verification
plan may be added later if an assignment requires one.

**Test class** A/B/C/D is a selection property. It is not a requirement, a
suite objective, a suite verdict, or an execution result. Class meanings and
the default required classes remain those in Verification Strategy §§6–7.

**R / PF / EC** are test-setup dimensions (repository content, pack input,
execution configuration). They are not requirements.

A **test suite** is one verification area. It owns one objective, its test
basis, its case catalogue, and a suite verdict rule. The suite ID is the
identifier.

A **test case** is the executable specification. When written, it states
objective, test basis, prerequisites/setup, steps with expected results,
teardown, and Pass/Fail criteria. A catalogue row marked **To be specified**
is not executable.

A **test record** is evidence from one execution. Pass/Fail belongs there.

Requirement-to-evidence mapping is only in
[Requirement traceability](requirements_traceability.md). Unmapped
requirements are valid findings. Coverage state is not Pass/Fail.

Create the verification run before execution. Execute only cases whose
Procedure status is **Executable**, and keep completed records outside this
repository.

Independent code and release review uses the
[code review procedure](procedures/2_code_review_procedures.md) and
[protocol template](generated_code_review_protocol_template.md). `CR-*`
identifies review activities, not a functional test suite.
