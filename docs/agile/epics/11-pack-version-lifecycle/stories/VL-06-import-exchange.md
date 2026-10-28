# VL-06 — Import pack-exchange into the pack list

**Status:** Draft. Not authorization to implement.  
**Epic:** [EP-11 Pack version lifecycle and exchange](../EPIC.md)  
**Depends on:** VL-05.

**As a product or Pack consumer**, I want to import a pack-exchange zip into my organisation workspace pack list, so that a “bought” or received update lands as a published release without mutating earlier versions I already have.

## Pedagogical example (normative shape)

Workspace already has `published/cra-baseline/1.0.0/`.  
User imports `cra-baseline-1.1.0.curbpack.zip`.

Result:

```text
published/cra-baseline/1.0.0/   # unchanged
published/cra-baseline/1.1.0/   # created from zip
```

Pack list shows `cra-baseline` with version `1.1.0` available. Creating a local working copy from `1.1.0` sets Requirement `origin` per Packs v2 (`pack` + `version` `1.1.0`) and does not rewrite the published tree. Import of the same `1.1.0` again is refused (no overwrite), matching release immutability.

## Requirements (Given / When / Then)

### R1 — Install beside existing releases

**Given** a valid exchange zip for `cra-baseline` `1.1.0` and an existing `published/cra-baseline/1.0.0/`  
**When** import succeeds  
**Then** `published/cra-baseline/1.1.0/` exists and verifies  
**And** `1.0.0` is byte-unchanged.

### R2 — No overwrite on re-import

**Given** `published/cra-baseline/1.1.0/` already exists  
**When** the same version is imported again  
**Then** import fails without modifying that directory.

### R3 — Pack list visibility

**Given** a successful import  
**When** the Packs list is opened  
**Then** that pack id is listed (or refreshed) so the operator can open / copy / select it per existing Pack Editor navigation  
**And** import does not by itself change product `curbpack.json`.

## Out of scope

- Automatically switching product selection to the new version.  
- Claim rebind UI (VL-07).  
- Paying / licensing / entitlement (“bought” is a human metaphor only).

## Open (not decided by this draft)

| Topic | Proposed resolution (not normative) | Status |
| --- | --- | --- |
| After import, default the next working copy to the new version | Prefer explicit user action “create working copy from 1.1.0” | OPEN |

Do not implement until this story and any required OPEN rows are accepted.
