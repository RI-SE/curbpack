# VL-03 — Pack view marks “has update”; apply all or one

**Status:** Draft. Not authorization to implement.  
**Epic:** [EP-11 Pack version lifecycle and exchange](../EPIC.md)  
**Depends on:** VL-02.

**As a Pack author**, I want each Requirement row to show when an upstream extract offers an update, so that I can update everything pending or open one Requirement at a time without losing the rest of the queue.

## Pedagogical example (normative shape)

After VL-02 has produced a pending difference set against working copy `cra-baseline/2026-10-01T120000Z/`:

| Id | Mark | Action |
| --- | --- | --- |
| `CRA-A` | has update | Apply one → clears mark for `CRA-A` |
| `CRA-B` | (none) | — |
| `CRA-D` | has update (add) | Apply one or included in Apply all |

**Apply all** applies every still-pending selected difference in that set.  
**Apply one** opens the same compare decision for a single id.  
Unrelated Requirements stay untouched.

## Requirements (Given / When / Then)

### R1 — Marks match the pending set

**Given** a pending difference set from VL-02  
**When** the Pack Requirements list for that working copy is shown  
**Then** every id in the pending set that is an add or change shows a “has update” (or equivalent) mark  
**And** ids not in the set do not show that mark.

### R2 — Apply one

**Given** two ids marked has-update  
**When** the author applies only the first  
**Then** the first Requirement (or add) is written per the author’s keep/take choice  
**And** the second remains marked has-update  
**And** unmarked Requirements are unchanged.

### R3 — Apply all

**Given** a non-empty pending set  
**When** the author chooses update all and confirms  
**Then** every pending difference is applied under the same explicit-apply rules as VL-02  
**And** after success the has-update marks for that set are cleared.

## Out of scope

- Side-by-side editing of two published versions (post-pilot multi-version UI may build on marks but is not this story’s acceptance).  
- Automatic apply without confirmation.

## Open (not decided by this draft)

| Topic | Proposed resolution (not normative) | Status |
| --- | --- | --- |
| Persist pending set across Studio restarts | Prefer yes, as files under the working copy or a sibling proposal dir — not SQLite-required | OPEN |

Do not implement until this story and any required OPEN rows are accepted.
