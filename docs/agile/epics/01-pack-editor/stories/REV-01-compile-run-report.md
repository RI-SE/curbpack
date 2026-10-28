# REV-01 — Compile a Check report

**Status:** Open seam, 2026-10-28. Not implemented. The run that is compiled is the one [SYS-03](SYS-03-one-repo-door.md) wrote for the opened repository.

**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md)

**As a reviewer**, I want to compile a report from a specific Check run, so that I can inspect and share what was actually checked.

### REV1-R01 — The report is the run for the repository just checked

**Given** Check has written a run result for the repository chosen on CHK-01  
**When** Review compiles a report  
**Then** the report is compiled from that run result  
**And** the Claims it reads are the files in that same repository's `claims` directory  
**And** it does not compile the workspace sample `product/` run instead.

Check writes `<repository>/curbpack/run-result.json`. Review reads the workspace `product/` run and `product/claims`. The report file SYS-03 writes is `<repository>/curbpack/reports/review-report.json`.

**Accept when:**

- Compilation uses an identifiable run and includes its outcomes and traceable Pack, Claim, Check and evidence context.
- The report distinguishes PASS, FAIL and justified SKIP without rewriting those outcomes.
- Compilation does not silently modify published Packs or product evidence.
- Any replacement of an existing report requires an explicit user choice; an existing signed report is not silently destroyed by a new Check run.
