# SYS-01 — Demonstrate the complete pilot

**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md)

**As a pilot tester**, I want to complete the workflow from a regulatory Requirement to a signed review report, so that I can verify that the tools form one usable application.

**Accept when:**

- Using a real test product repository, a tester completes: publish or select Requirements → associate Claims with evidence → run Checks → compile a report → review and sign it.
- The test includes a passing case, a failing missing-file case, and a permitted skipped case with an explicit reason.
- Product changes can be checked again without losing or mislabeling the previous signed report.
- The result identifies the source Pack/version, Requirement, Claim, configured Checks, checked product state and review report.
- Execution is recorded with reproducible setup, expected observations, actual observations and failures; successful navigation alone is insufficient.

**Boundary:** This story verifies the integrated pilot. It does not authorize EP-02 refactoring or a new persistence layer.
