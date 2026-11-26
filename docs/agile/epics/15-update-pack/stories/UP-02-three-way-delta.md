# UP-02 — Three-way upstream/local Requirement comparison

**Epic:** [EP-15 — Update Pack](../EPIC.md)  
**Status:** Draft  
**Starts when:** UP-01 and VL-03 accepted.

**As a local Pack maintainer**, I want to distinguish what RISE changed from what I changed, so that incoming upstream changes do not overwrite local interpretation or hints.

## Behavior

Implement a **headless, read-only** three-way comparison per unambiguously mapped Requirement: BASE→LOCAL, BASE→NEW, and resulting conflict analysis. Reuse the existing field-level Compare and stable `version_digest`; do not build a second generic diff engine. Match normal Requirements only through source-qualified IDs and accepted origin relationships; renames, split/merge and reused IDs that lack a unique mapping become **ambiguous, manual review**. Distinguish unchanged, upstream-only edit, local-only edit, same-value edit, divergent edit (conflict), upstream addition, upstream removal, local-only addition and uncertain restructure. Show changes at field level; array/object subfield merge is not automatic unless already supported by Compare and unambiguous.

`origin`, `namespace`, `status` and `signed` are provenance/approval metadata, not naive merge targets. A copy taken into a new namespace is not itself an upstream change to `law_text`. No file writes and no implicit version bump.

## Acceptance — Given / When / Then

### GWT-01 — Upstream-only edit
**Given** BASE and LOCAL agree on a field while NEW changes it  
**When** comparison runs  
**Then** that field is an upstream-only proposal, not a local conflict.

### GWT-02 — Local-only edit
**Given** LOCAL differs from BASE and NEW equals BASE  
**When** comparison runs  
**Then** LOCAL is preserved as the default and shown as local-only.

### GWT-03 — Divergent conflict
**Given** LOCAL and NEW differ from BASE and from each other on the same field  
**When** comparison runs  
**Then** a conflict is shown and no default silently overwrites LOCAL.

### GWT-04 — Same-value concurrent change
**Given** LOCAL and NEW independently have the identical new value  
**When** comparison runs  
**Then** the field needs no conflict resolution; namespace/origin provenance remains distinct.

### GWT-05 — Added, removed and ambiguous
**Given** upstream adds or removes a Requirement, or changes IDs in a way that could represent a split/merge  
**When** comparison runs  
**Then** categories are explicit, with split/merge/manual mapping never guessed from similar text alone.

### GWT-06 — Determinism and safety
**Given** the same three snapshots  
**When** comparison runs twice  
**Then** identical categorized output is returned; all files and signatures are byte-identical before and after.

**Done when:** A developer can call the three-way operation without HTTP/UI and demonstrate all conflict and ambiguity categories with fixtures.
