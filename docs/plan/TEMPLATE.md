# <STORY-ID> — <Story title>

## Summary

<!-- Based on the existing PoC2 resumable execution plan in doc/PLAN/REQUIREMENTS_IMPLEMENTATION_PLAN.md.
     Execution rules remain in AGENTS.md and the existing story-workflow Skill. -->

- **Story:** `docs/agile/epics/.../stories/<STORY-ID>-...md`
- **Goal:** <observable user result>
- **Scope / exclusions:** <minimal scope, no EP-02 unless explicitly selected>
- **Baseline:** <test command, actual result and known failures>

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | DRAFT |
| Approved by | Pending human approval of requirements and plan |
| Current task | Task 0 — derive requirements and get plan approval |
| Last completed task | None |
| Last verified tests | Not run; baseline to be established |
| Last checkpoint commit | Resolve: `git log -1 --format=%H -- docs/plan/<STORY-ID>.md` (none if uncommitted) |
| Requirements | `docs/req/<area>.md` — draft IDs / approved IDs |
| Packs v2 | Local verified path and Git commit; or `not applicable` with reason |
| Blockers | <specific missing decision, or None> |
| **Exact next action** | <one concrete action for a fresh agent> |

## Requirements and acceptance mapping

| Requirement ID | Story | Test / observed evidence | Status |
| --- | --- | --- | --- |
| REQ-... | <ID> | <test path / acceptance action> | DRAFT |

## Tasks

### Task 0 — derive and approve requirements and plan

**Inputs / contracts:** <source files and revision>
**Change files:** `docs/req/...`, `docs/plan/<STORY-ID>.md`
**Acceptance / stop:** human approval recorded; conflicts resolved.

- [ ] Requirements derived, traceable, reviewed and approved.
- [ ] Baseline observed; risk/contract conflicts recorded.
- [ ] Plan approved in Cursor Plan Mode (record approver).

### Task 1 — <one small independently verifiable behavior>

**Requirements:** REQ-...
**Files:** <expected code and tests>
**Test first:** <exact test command and expected RED; or already-implemented PASS>
**Validation:** <focused and impacted regressions; security and traceability checks>
**Stop if:** <condition that would require decision>

- [ ] RED observed for the intended behavior (or existing PASS demonstrated).
- [ ] Minimal implementation and GREEN verified.
- [ ] Relevant regressions and review complete.
- [ ] Checkpoint saved and verified local commit created.

## Work log

- **<date> / Task 0:** <actual commands, results, decisions, tests, review findings>. No invented evidence.

<!-- After each verified task update the TOP checkpoint and append one dated log entry
     BEFORE committing them alongside code and tests. The commit hash is resolved
     from Git on resumption; a commit cannot record its own hash. -->
