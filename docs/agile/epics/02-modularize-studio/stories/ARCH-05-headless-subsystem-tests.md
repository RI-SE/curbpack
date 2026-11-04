# ARCH-05 — Verify behavior and headless interfaces

**Status:** Draft; after pilot baseline.  
**Epic:** [EP-02](../EPIC.md)

**As a developer**, I want repeatable tests of subsystem behavior and migrated user journeys, so that structural changes cannot silently remove functionality.

**Accept when:**
- Before each bounded migration, record the relevant pilot behavior, existing tests and known gaps compared with the working PoC. Do not describe untested behavior as verified.
- Domain operations are directly testable without FastAPI or a browser. Curbcheck is testable through its public Python API and CLI.
- Separate API tests verify routing, Pydantic validation and access enforcement; targeted browser/user-journey checks verify UI-to-REST wiring where applicable.
- Existing tests continue to run from their updated paths; a passing import/syntax check alone is not considered functional parity.
- Every migration ends with relevant regression results and an explicit list of remaining failures or known parity gaps. Do not mark a feature migrated while its verified behavior has regressed.
- Make `MIGRATION_COVERAGE.md` a required completion checklist: link **passing** current test evidence to each row; add API-boundary and UI-to-REST tests when existing tests only cover old server-rendered paths. Test Pack→Claim/Discovery→Check→Compile→Review, CLI, packaging, and negative/security cases. No blanket PASS for missing PoC baseline or untested flow.
