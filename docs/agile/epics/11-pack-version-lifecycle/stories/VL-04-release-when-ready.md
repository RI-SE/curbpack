# VL-04 — Release when the set is ready

**Status:** Draft. Not authorization to implement.  
**Epic:** [EP-11 Pack version lifecycle and exchange](../EPIC.md)  
**Depends on:** VL-01, [PE-11](../../01-pack-editor/stories/PE-11-publish-pack.md).

**As a Pack publisher**, I want to release the working copy I have finished (no pending has-update marks I still intend to apply) as an immutable `published/<id>/<version>/`, so that consumers can pin that release and earlier releases stay on disk.

## Pedagogical example (normative shape)

Working copy `cra-baseline/…Z/` has `pack.json` `"version": "1.1.0"`, Requirements signed as required by PE-11, no pending VL-03 marks the publisher still intends to apply.

Publisher runs **Release**:

```text
published/cra-baseline/1.1.0/   # created
published/cra-baseline/1.0.0/   # unchanged
```

Directory seal verifies. A second Release to `1.1.0` is refused. Export to zip is VL-05 (may be offered from the same screen later; not required here).

Pilot note: during EP-01 it is enough that publish works for the version in focus. This story adds the “ready / no leftover intended updates” gate and multi-release coexistence clarity.

## Requirements (Given / When / Then)

### R1 — Immutable new directory

**Given** a ready working copy whose `pack.version` is `1.1.0` and `published/…/1.1.0/` does not exist  
**When** Release succeeds  
**Then** `published/<pack-id>/1.1.0/` contains that Pack’s intended Requirement set and `pack.json`  
**And** any pre-existing `published/<pack-id>/1.0.0/` is byte-unchanged.

### R2 — No overwrite

**Given** `published/<pack-id>/1.1.0/` already exists  
**When** Release targets `1.1.0` again  
**Then** the operation fails without modifying that directory.

### R3 — Ready gate

**Given** a non-empty pending has-update set the UI still tracks for that working copy  
**When** the publisher attempts Release without dismissing or applying it  
**Then** Release is blocked or requires an explicit “release anyway” confirmation recorded in the UI  
**And** a successful Release without that confirmation does not occur while marks remain (choose one behaviour in OPEN; tests must match the chosen one).

## Out of scope

- Pack-exchange zip bytes (VL-05).  
- Choosing `pack.version` interactively if PE-11 still treats it as read-only — follow PE-11 until a separate decision changes it.

## Open (not decided by this draft)

| Topic | Proposed resolution (not normative) | Status |
| --- | --- | --- |
| Block vs confirm when pending updates remain | Prefer block by default; optional explicit confirm | OPEN |
| Publisher picks `pack.version` on Release | Align with PE-11; if PE-11 gains a picker, VL-04 uses it | OPEN |

Do not implement until this story and any required OPEN rows are accepted.
