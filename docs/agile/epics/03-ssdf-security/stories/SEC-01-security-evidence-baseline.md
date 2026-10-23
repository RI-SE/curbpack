# SEC-01 — Verify the security baseline

**Epic:** [EP-03 SSDF security baseline and evidence](../EPIC.md)  
**Status:** Draft

**As a maintainer**, I want the current security controls and gaps verified against current HEAD, so that follow-up work is justified by evidence, not names of scripts or policies.

**Accept when:**

- Inspect the current Studio code, CI configuration, existing tests and `docs/ssdf/harness.md`; record commit and commands used.
- Rerun the five proposed security scripts from the separate review ZIP against a disposable workspace, with no alteration to tracked customer or production files. Categorize each case as existing coverage, new regression or invalid/outdated assumption.
- Describe the relevant trust boundaries in a short table: untrusted HTTP/Pack identifiers, filesystem/workspace paths, repo/Claim evidence, Check results, Review/signature content, Git provenance and local secrets. Include only demonstrated threat paths and explicit unknowns.
- Update the **existing** SSDF evidence map with control, test evidence, observed date, gap, owner and status. Cover relevant PO, PS, PW and RV practices; mark unexamined items `Not assessed`.
- Create follow-up defects for reproducible failures. Do not make a failing test pass by changing its expectation.

**Out of scope:** importing all Curbpack test suites, running automatic external attack tools, new policies or implementing the follow-up fixes.
