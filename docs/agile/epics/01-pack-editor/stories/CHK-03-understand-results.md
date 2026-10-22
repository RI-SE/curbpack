# CHK-03 — Understand Check outcomes

**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md)

**As a reviewer**, I want to see what passed, failed or was skipped and why, so that I can decide what needs attention.

**Accept when:**

- The application shows PASS, FAIL or SKIP for each evaluated Check/Claim as supported by the Check contract.
- A FAIL identifies the failed condition and relevant evidence; it is not hidden behind only an overall status.
- A SKIP has an explicit, visible reason and is used only in permitted situations; it is never displayed as PASS.
- Operational errors and unavailable evidence are distinguishable from successful checks.
- The UI does not present PASS as proof of legal compliance or adequate substantive evidence.
