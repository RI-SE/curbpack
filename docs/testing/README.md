# Independent verification

Use the verification documents in this order:

1. [Verification Strategy](strategy.md) — how Curbpack is verified in general.
2. [Verification Plan](verification_plan.md) — this campaign: frozen
   baseline, selected coverage, completion evidence, and the requirement
   coverage matrix.
3. [Test Setup](procedures/README.md) — controlled repository state (`R-*`),
   pack input (`PF-*`), and execution configuration (`EC-*`) prerequisites.
4. [Test Suites and Test Cases](test_suites/README.md) — suite objectives, test
   basis, case selection, and executable procedures.
5. [Test Records](generated_test_record_template.md) — one record per case
   execution.

## Reading model

Product requirements and documented claims are **test basis**. They are not a
verification document layer.

- **Product requirements** are the normative `MUST / MUST NOT` statements
  (`MUST-*`) in [Software Design Document v1.2](../software-design-document.md)
  §§1.1 and 2.1–2.9.
- **Other test basis** includes documented product claims, intended-use and
  non-use boundaries, release and platform claims, and human-authority limits,
  but only where a suite names them.

The **Verification Strategy** is the reusable method. The **Verification Plan**
is this campaign: what is frozen, which suites and test classes are required,
and what evidence closes the work. **Test class** A/B/C/D is a selection
property. It is not a requirement, a suite objective, a suite verdict, or an
execution result. Class meanings remain those in Verification Strategy §7.

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

Requirement coverage for this campaign is only in the Verification Plan
matrix. Unmapped requirements are valid findings.

Freeze the Verification Plan before execution. Execute only cases whose
Procedure status is **Executable**, and keep completed records outside this
repository.

Independent code and release review uses the
[code review procedure](procedures/2_code_review_procedures.md) and
[protocol template](generated_code_review_protocol_template.md). `CR-*`
identifies review activities, not a functional test suite.
