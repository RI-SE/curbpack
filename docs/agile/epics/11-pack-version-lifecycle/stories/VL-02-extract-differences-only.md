# VL-02 — Extract again; persist only differences

**Status:** Draft. Not authorization to implement.  
**Epic:** [EP-11 Pack version lifecycle and exchange](../EPIC.md)  
**Depends on:** VL-01, [PE-08](../../01-pack-editor/stories/PE-08-re-extract-and-compare.md).

**As a Pack author**, I want a re-extract from the source URL to propose only Requirements that differ from what I already have, so that unchanged signed work is not rewritten and I can see what the upstream change actually touched.

## Pedagogical example (normative shape)

Working copy has three Requirements: `CRA-A`, `CRA-B`, `CRA-C`.  
New extract yields `CRA-A'` (law_text changed), `CRA-B` (identical payload fields that define equality for this story), and new `CRA-D`.

Persisted proposal / compare set contains:

- `CRA-A` → update candidate  
- `CRA-C` → missing in new extract (visible, not silent delete)  
- `CRA-D` → add candidate  
- `CRA-B` → **not** listed as a change to apply (no write of identical bytes)

Equality for “≠” is defined on the Requirement payload that enters the version digest (see Packs v2), not on file mtime.

## Requirements (Given / When / Then)

### R1 — Unchanged rows are not rewritten

**Given** a working copy Requirement whose digest-relevant payload equals the new extract candidate with the same `id`  
**When** the author runs extract-and-apply under this story’s rules  
**Then** that Requirement file’s digest-relevant bytes are unchanged  
**And** a previously valid `signed` block on that file is not cleared by that no-op.

### R2 — Differences are visible before apply

**Given** at least one add, change, or missing id between current working copy and new extract  
**When** the compare view opens  
**Then** each difference is shown as keep-old / take-new (or equivalent) per PE-08  
**And** missing-in-new ids are visible rather than deleted silently.

### R3 — Apply is explicit

**Given** a compare set with mixed decisions  
**When** the author cancels  
**Then** the working copy is unchanged  
**When** the author applies  
**Then** only the selected differences are written.

## Out of scope

- Pack-list import/export zip (VL-05/06).  
- Claim rebind (VL-07).  
- Polling EUR-Lex automatically without a user-started extract.

## Open (not decided by this draft)

| Topic | Proposed resolution (not normative) | Status |
| --- | --- | --- |
| Whether “identical” ignores `discovery_hints` for the ≠ filter | Prefer: hints are part of digest → hint-only change is a difference | OPEN |

Do not implement until this story and any required OPEN rows are accepted.
