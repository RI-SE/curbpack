# VL-05 — Pack-exchange format (zip of Packs v2)

**Status:** Draft. Not authorization to implement.  
**Epic:** [EP-11 Pack version lifecycle and exchange](../EPIC.md)  
**Depends on:** VL-04.

**As a Pack publisher**, I want a defined on-disk exchange file that is just the Packs v2 published tree (zipped), so that “buying” or shipping an update does not invent a second schema.

## Pedagogical example (normative shape)

Exchange file `cra-baseline-1.1.0.curbpack.zip` (final extension OPEN) unpacks to:

```text
pack.json                 # id cra-baseline, version 1.1.0
CRA-ANNEX-VII-RISK.json   # signed publisher Requirements as published
…                         # only files that belong in that published directory
```

Optional top-level folder `cra-baseline/1.1.0/` inside the zip is allowed if documented; consumers must resolve to the same Packs v2 files. No SQLite database inside the zip. No Claim files from a product repo. Digests/signatures are those already on the Requirement / pack seal — not a parallel manifest format unless OPEN decides a thin checksum file.

## Requirements (Given / When / Then)

### R1 — Round-trip bytes

**Given** a valid `published/<id>/<version>/` tree that verifies under Packs v2 seal rules used by Studio  
**When** export builds an exchange zip and that zip is unpacked to an empty directory  
**Then** the unpacked Packs v2 files match the published tree for that id/version (same ids, versions, digests)  
**And** the zip contains no product `claims/` and no SQLite file.

### R2 — Reject garbage

**Given** a zip that lacks `pack.json` or whose `pack.id` / files violate Packs v2 layout rules this story documents  
**When** a consumer validates the exchange before import  
**Then** validation fails with a clear error  
**And** no pack list entry is created.

### R3 — Documentation example is normative shape

**Given** the pedagogical tree above  
**When** an implementer writes the exporter/importer  
**Then** tests use that shape (or an equivalent fixture checked into the suite)  
**And** they do not require a second “exchange JSON” schema beyond Packs v2 plus zip packaging.

## Out of scope

- Import UI and pack-list behaviour (VL-06).  
- Network marketplace or automatic download.

## Open (not decided by this draft)

| Topic | Proposed resolution (not normative) | Status |
| --- | --- | --- |
| File extension / MIME (`.curbpack.zip` vs `.zip`) | Prefer `.curbpack.zip` for clarity | OPEN |
| Thin `SHA256SUMS` or seal file at zip root | Prefer rely on existing pack directory seal; add sums only if seal is insufficient for transport | OPEN |

Do not implement until this story and any required OPEN rows are accepted.
