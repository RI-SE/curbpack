# AD-01 — CRA text adapter extracts Annex II

**Status:** Draft. Not authorization to implement.

**Epic:** [EP-14 Regulation adapters](../EPIC.md)

**Starts when:** Scheduled. Does not block EP-01.

**As a Pack author**, I want Annex II available on the CRA text adapter, so that Information and instructions to the user is not only a title in the section list.

The source text and the locus oracle already exist in the CTAM poc. This story brings those two files into the Studio `cra` adapter and checks the atomizer against the oracle. It does not bring the poc's later claim run.

### Source files

- `ctam/poc/components/transform/adapters/cra/fixtures/annexes/II.txt`
- `ctam/poc/components/transform/work/cra/II/01_atomize.yml`

The inventory read 14 loci in that oracle: `1`–`7`, `8(a)`–`8(f)`, and `9`. The test compares against the oracle file. The count in this paragraph is not a second contract.

### Do not copy

`work/cra/II/02_claims.yml`, `03_search.yml`, `04_assemble.yml`, and `poc/data/step1_extract/results/cra-ii/requirements.yml`. That run was not accepted. Its claim ids are `vii-1` and the like, and the package header still says `annex: VII`. `prompts/02_claims.txt`, `prompts/03_search.txt`, and `maps/*.yml` are hunt YAML, not Packs v2 Requirement files.

### Requirements (Given / When / Then)

#### AD1-R01 — Annex II is ready on the text adapter

**Given** the Studio `cra` adapter  
**When** its `adapter.json` is read  
**Then** section `II` is `in_scope` and `ready`  
**And** its `fixture` is the poc annex cut, byte for byte, stored under the Studio adapter  
**And** sections `VII`, `V`, `VIII`, `I`, `III`, `IV`, and `VI` keep the ready and in-scope flags they had before this story. This story does not mark V or VIII ready.

#### AD1-R02 — Provisions match the oracle

**Given** the Annex II fixture and the poc `01_atomize.yml`  
**When** the Studio text atomizer runs on that fixture  
**Then** the loci and `law_text` match the oracle  
**And** the test fails if a locus is missing, added, or renamed.

#### AD1-R03 — The unaccepted claim package stays out

**Given** the repository after this story  
**When** the CRA adapter tree and Requirement fixtures are listed  
**Then** none of them is a copy of the poc Annex II `02`, `03`, or `04` YAML, or of `cra-ii/requirements.yml`.

### Out of scope

- Annexes other than II.
- Formex `cra-xml`.
- Packs v2 field changes.
- Publishing a Pack.

### Stop if

The oracle's loci cannot be produced by the current text atomizer without a new cutting rule. Record the mismatch. Do not accept the poc claim YAML in its place.
