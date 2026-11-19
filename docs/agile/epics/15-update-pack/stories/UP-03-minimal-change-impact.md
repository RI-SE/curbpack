# UP-03 — Compute minimal defensible Requirement impact

**Epic:** [EP-15 — Update Pack](../EPIC.md)  
**Status:** Draft  
**Starts when:** UP-02 and VL-04 accepted.

**As a product maintainer**, I want a precise change and impact overview, so that I do not repeat review for Requirements whose effective bytes have not changed.

## Behavior

Calculate deterministic impact against the **proposed result of accepted field choices** (initially the default preview, recomputed after selection), not against every change anywhere in NEW. Report separately: unchanged final payload, changed exact version digest, upstream add/remove, unresolved mapping, local-only changes, and fields changed. Suggested review reasons distinguish changes to normative source/references/obligations, discovery-only hints, descriptive metadata, identity/provenance/signature/status, or mixed/unknown fields. These are **labels to organize human review**, not an automated legal finding or guarantee of semantic equivalence.

Digest invariants matter: every change to a Requirement payload changes its exact digest; its existing Claim binding may therefore become `stale` even when only `discovery_hints` changed. An informational label must never turn that stale binding into `match`. Conversely, if the selected update yields byte-equivalent payload, do not generate a work item just because the upstream Pack version changed. Changes to Pack-level metadata without Requirement payload changes do not force Claim rebinding.

## Acceptance — Given / When / Then

### GWT-01 — No change, no work
**Given** the user's selected choices yield unchanged Requirement payloads  
**When** impact is calculated  
**Then** none of their Claims is labeled as requiring a new rebind solely because the Pack release number changed.

### GWT-02 — Normative changes
**Given** accepted `references[].law_text` or other meaning-bearing fields change  
**When** impact is calculated  
**Then** the affected Requirements are marked for human review, not automatically judged compliant/noncompliant.

### GWT-03 — Hints-only change
**Given** accepted `discovery_hints` changes but normative text does not  
**When** impact is calculated  
**Then** the digest difference and resulting stale Claim bindings are shown accurately, with 'hints-only' as a separate review hint; the tool does not silently rebind.

### GWT-04 — Addition and removal
**Given** a Requirement is added or removed  
**When** impact is calculated  
**Then** additions are identified for Claim coverage assessment and removals identify existing Claims requiring explicit disposition.

### GWT-05 — Uncertainty
**Given** field semantics or Requirement identity mapping cannot be established  
**When** impact is calculated  
**Then** the item remains review-required/ambiguous and is never quietly classified as safe.

### GWT-06 — Changing choices
**Given** a user deselects an upstream field change  
**When** impact recomputes  
**Then** the affected set reflects the new proposed result, not the original upstream diff.

**Done when:** The same inputs and choices yield a stable set of exactly changed Requirement digests plus an explicit, conservative human review classification.
