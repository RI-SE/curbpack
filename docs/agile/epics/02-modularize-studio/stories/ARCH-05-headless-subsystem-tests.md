# ARCH-05 — Baseline and test every migration step

**Status:** Draft  
**Epic:** [EP-02](../EPIC.md)  
**Stage:** 0 and continuous verification through stages 1–7.

**As a developer**, I want a verified baseline and a passing gate after each small extraction, move and architecture change, so that a failure points to a single bounded edit.

## Work

- Before changing code, inventory live GET/POST routes, HTML pages, CLI commands, backend operations, persistent side effects and relevant existing tests. Verify `MIGRATION_COVERAGE.md` against the **current working tree**, not a historical ZIP as though it were current.
- Record the baseline revision and tests actually executed, including known failures. Capture representative successful and invalid interactions for the page/operation being moved.
- After **every extraction, move, separation, model replacement, router replacement and TypeScript conversion**, run the focused regression and affected integration tests before proceeding; use direct headless tests once domain operations have been separated.
- Do not suppress failures, convert failing tests to skips, weaken assertions or mark untested PoC-only behavior verified. Update tests only to reflect approved architecture changes, preserving their substantive assertions.
- At stage completion run appropriate end-to-end flows Pack → Claim/Discovery → Check → Compile → Review, direct FastAPI auth/validation, CLI/packaging smoke and negative/security cases.

## Acceptance (Given / When / Then)

1. **Given** the unmodified current pilot, **when** baseline is recorded, **then** the revision, tested commands, outcomes, live page/route inventory and known gaps are saved in `MIGRATION_COVERAGE.md`.
2. **Given** a single page or handler extraction, **when** the same focused tests run, **then** the old server still behaves the same; otherwise no new migration work starts.
3. **Given** a file move or backend separation, **when** tests run, **then** imported modules, actual requests and persisted behavior still work; a mere import check is insufficient.
4. **Given** a migrated FastAPI route, **when** valid, invalid and unauthorized direct requests are sent, **then** expected responses and side effects are verified before the old route is removed.
5. **Given** a TypeScript conversion, **when** a browser drives the page, **then** it reaches the backend through REST and produces the expected result before old rendering is deleted.
6. **Given** the epic claimed complete, **when** coverage and test evidence are reviewed, **then** every required flow is accounted for, no required coverage row remains OPEN, and final CLI, packaging, security and end-to-end checks pass.
