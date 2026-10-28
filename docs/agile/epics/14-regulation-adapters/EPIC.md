# EP-14 — Regulation adapters

**Status:** Draft. Not authorization to implement.

**Starts when:** Scheduled. Does not block EP-01. Does not wait for EP-13.

## Goal

The CRA text adapter can extract the annexes the CTAM poc already cut and atomized, beyond Annex VII. Studio keeps its own pinned Formex packages for official CRA and NIS2 text. This epic does not invent a regulation the poc does not contain.

## Why this epic exists

On 2026-10-28 danielfl reviewed PE-04 and found available sections extremely thin. The same day's read-only inventory compared `ctam/poc/components/transform/adapters/` with `requirements/extract/adapters/`.

The poc can fill three CRA text annexes. It cannot fill NIS2, medtech, or NIST.

Studio's `nis` adapter is already Formex, with articles `Art.1`–`Art.46` ready. The poc's NIS2 adapter is an empty stub. Annexes I and II stay not ready in Studio because they contain tables. That limit is in Studio's Formex extractor. No poc file closes it.

`docs/ssdf/` is the NIST SP 800-218 evidence map. The poc has no NIST extraction adapter.

EP-13 DOC-05 documents how to add an adapter. It does not add sections. This epic adds the three CRA annexes the poc actually has.

## Stories

| ID | User goal | Source |
| --- | --- | --- |
| [AD-01](stories/AD-01-cra-annex-ii.md) | CRA text adapter extracts Annex II | poc annex cut and atomize oracle |
| [AD-02](stories/AD-02-cra-annex-v.md) | CRA text adapter extracts Annex V | poc annex cut and atomize oracle |
| [AD-03](stories/AD-03-cra-annex-viii.md) | CRA text adapter extracts Annex VIII | poc annex cut and atomize oracle |

Draft stories are not permission to implement. AD-02 and AD-03 do not wait on AD-01.

## Not opened

- CRA annexes I, III, IV, and VI. The poc has cuts and atomize output. III repeats class numbers as `1~19` and the like. IV locus `3` still contains an OJ footnote. VI is one locus for the whole simplified declaration. Both catalogs leave these out of scope.
- CRA articles 1–71. The poc file is an uncut body dump. Nothing atomizes it.
- A CRA Formex story. The poc has no Formex package. Studio `cra-xml` already pins the OJ text and is ready for Annex VII only.
- A NIS2 story taken from the poc. The poc adapter is empty.
- Medtech. Both sides are empty stubs.
- NIST as an extraction adapter.

## Epic acceptance

- `requirements/extract/adapters/cra/` can prepare Annex II, Annex V, and Annex VIII. Each ready section's loci match that annex's poc atomize oracle.
- Annex VII stays as it is.
- No hunt YAML, claim prompt, or `requirements.yml` from the poc is copied in as a Requirement file.
- `requirements/extract/adapters/nis/` and `medtech/` are unchanged.
- Packs v2 files and published bytes are unchanged.

## Out of scope

- Parsing NIS2 annex tables.
- New Packs v2 fields, a plugin registry, or an adapter-editing screen.
- The EP-01 pilot journeys.
