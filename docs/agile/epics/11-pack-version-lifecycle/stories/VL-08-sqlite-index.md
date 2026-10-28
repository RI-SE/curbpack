# VL-08 — Optional SQLite index over on-disk versions

**Status:** Draft. Not authorization to implement.  
**Epic:** [EP-11 Pack version lifecycle and exchange](../EPIC.md)  
**Depends on:** VL-01; useful after VL-03–VL-06 exist to query.

**As a Studio maintainer**, I want an optional SQLite index of Pack releases and pending update marks rebuilt from disk, so that listing versions / latest / has-update stays fast without making the database the system of record.

## Pedagogical example (normative shape)

Disk has:

```text
published/cra-baseline/1.0.0/
published/cra-baseline/1.1.0/
```

Index tables (illustrative names only) answer:

- `list_versions('cra-baseline')` → `1.0.0`, `1.1.0`  
- `latest('cra-baseline')` → `1.1.0` (order rule documented: semver or directory mtime — OPEN, must be deterministic)  
- `has_update(working_copy)` → ids from the pending VL-03 set

Operator deletes `workspace/.curbpack-index.sqlite` and runs rebuild: answers match the previous index for the same disk state. Export zip (VL-05) still contains **no** database file.

## Requirements (Given / When / Then)

### R1 — Disk wins

**Given** a published tree on disk and a SQLite index that omits that version  
**When** rebuild-index runs  
**Then** the index lists that version  
**And** features that need the version can proceed from disk even if the index was empty before rebuild.

### R2 — Wipe and rebuild

**Given** a populated index that matches disk  
**When** the index file is deleted and rebuilt  
**Then** `list_versions` / `latest` / pending has-update answers equal the pre-wipe answers for that disk state.

### R3 — Not in exchange

**Given** VL-05 export  
**When** an exchange zip is built  
**Then** it does not include the SQLite index file.

### R4 — Optional

**Given** Studio built without enabling the index (or index disabled in config)  
**When** the operator uses pack list / publish / import paths that VL-04–VL-06 require  
**Then** those flows still succeed using filesystem scan  
**And** absence of SQLite is not a hard error for pilot-era paths.

## Out of scope

- Multi-user server SQL.  
- SQLite as the only store of Requirement bodies.  
- Replacing Packs v2 JSON files.

## Open (not decided by this draft)

| Topic | Proposed resolution (not normative) | Status |
| --- | --- | --- |
| How `latest` is ordered | Prefer `pack.version` semver when parseable; else lexicographic version directory name | OPEN |
| Index path under workspace | Prefer one file at workspace root managed by Studio | OPEN |

Do not implement until this story and any required OPEN rows are accepted.
