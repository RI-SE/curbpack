# AD-02 — CRA text adapter extracts Annex V

**Status:** Draft. Not authorization to implement.

**Epic:** [EP-14 Regulation adapters](../EPIC.md)

**Starts when:** Scheduled. Does not block EP-01. Does not wait on AD-01.

**As a Pack author**, I want Annex V available on the CRA text adapter, so that the EU declaration of conformity is not only a title in the section list.

The poc has a text cut and an atomize oracle. It has no accepted Requirement package for this annex.

### Source files

- `ctam/poc/components/transform/adapters/cra/fixtures/annexes/V.txt`
- `ctam/poc/components/transform/work/cra/V/01_atomize.yml`

The inventory read 8 loci, `1`–`8`. The test compares against the oracle file.

### Requirements (Given / When / Then)

#### AD2-R01 — Annex V is ready on the text adapter

**Given** the Studio `cra` adapter  
**When** its `adapter.json` is read  
**Then** section `V` is `in_scope` and `ready`  
**And** its `fixture` is the poc annex cut, byte for byte, stored under the Studio adapter  
**And** this story does not mark any other section ready.

#### AD2-R02 — Provisions match the oracle

**Given** the Annex V fixture and the poc `01_atomize.yml`  
**When** the Studio text atomizer runs on that fixture  
**Then** the loci and `law_text` match the oracle.

### Do not copy

Claim prompts, hunt maps, and any `02`/`03`/`04` run. The poc does not have an accepted one for Annex V.

### Out of scope

- Annexes other than V.
- Formex `cra-xml`.
- Packs v2 field changes.

### Stop if

The oracle's loci cannot be produced by the current text atomizer without a new cutting rule. Record the mismatch.
