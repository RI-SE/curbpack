# AD-03 — CRA text adapter extracts Annex VIII

**Status:** Draft. Not authorization to implement.

**Epic:** [EP-14 Regulation adapters](../EPIC.md)

**Starts when:** Scheduled. Does not block EP-01. Does not wait on AD-01 or AD-02.

**As a Pack author**, I want Annex VIII available on the CRA text adapter, so that the conformity assessment procedures are not only a title in the section list.

The poc cut includes Parts I–IV. The atomize oracle already prefixes those parts. This story checks that the Studio atomizer still does that for this fixture.

### Source files

- `ctam/poc/components/transform/adapters/cra/fixtures/annexes/VIII.txt`
- `ctam/poc/components/transform/work/cra/VIII/01_atomize.yml`

The inventory read 66 loci, from `I-1` through `IV-8`, including dotted points such as `IV-3.2(a)`. The test compares against the oracle file.

### Requirements (Given / When / Then)

#### AD3-R01 — Annex VIII is ready on the text adapter

**Given** the Studio `cra` adapter  
**When** its `adapter.json` is read  
**Then** section `VIII` is `in_scope` and `ready`  
**And** its `fixture` is the poc annex cut, byte for byte, stored under the Studio adapter  
**And** this story does not mark any other section ready.

#### AD3-R02 — Provisions match the oracle, including part prefixes

**Given** the Annex VIII fixture and the poc `01_atomize.yml`  
**When** the Studio text atomizer runs on that fixture  
**Then** the loci and `law_text` match the oracle  
**And** a point inside a Part keeps that Part prefix.

### Do not copy

Claim prompts, hunt maps, and any `02`/`03`/`04` run. The poc atomize file is the oracle. There is no accepted Requirement package for this annex.

### Out of scope

- Annexes other than VIII.
- Formex `cra-xml`.
- Packs v2 field changes.

### Stop if

A locus in the oracle needs a cutting rule the current atomizer does not have. Record the locus. Do not drop the Part prefix to make the test pass.
