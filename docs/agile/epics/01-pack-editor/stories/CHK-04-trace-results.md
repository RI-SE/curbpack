# CHK-04 — Trace results to evidence

**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md)

**As a reviewer**, I want to trace a Check result back to the precise Requirement, Claim, evidence and checked product revision, so that the result can be examined later.

**Accept when:**

- A result identifies the Requirement and applicable Pack/version, the Claim, and the Checks/arguments evaluated.
- The product repository, checked revision/state and evidence path(s) are identifiable from the result or its traceable run record.
- Where an evidence file is changed or missing, the result does not present earlier evidence as if it were checked in the current run.
- Existing regulatory `source` and `references[]` information remains available by following the Requirement; no source references are silently discarded.
