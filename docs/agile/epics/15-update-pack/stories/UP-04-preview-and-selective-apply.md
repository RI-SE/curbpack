# UP-04 — Preview and selectively adopt upstream changes

**Epic:** [EP-15 — Update Pack](../EPIC.md)  
**Status:** Draft  
**Starts when:** UP-02, UP-03 and VL-01/VL-03 accepted.

**As the owner of a locally adapted Pack**, I want to apply chosen upstream fields to the single active copy, so that no second active copy is created.

## Behavior

Reuse existing form Compare/Apply and workspace copy operations; selections are per Requirement and editable field, with explicit decisions for additions, removals and conflicts. The preview identifies exact source and destination version digests, local namespace and chosen fields. APPLY updates the single active copy for that `(namespace, pack_id)` after explicit confirmation and does not create a second active copy. BASE and NEW remain unchanged. Do not rewrite `origin` blindly: after accepting NEW, record a coherent upstream reference to the version actually accepted, while retaining source/local evidence needed for later comparison under the approved existing schema. If the existing `origin` cannot express partial per-Requirement acceptance without misrepresenting lineage, **stop for PO contract decision** rather than stamp all Requirements as updated.

Use atomic staging/rename, fail-safe cleanup, path confinement, and stale-input checks (recheck each chosen source/destination digest before commit). A cancelled/failed Apply leaves no partially selected live working copy. Previous Pack/Requirement signatures never carry over onto changed payloads; unchanged payload bytes are preserved when possible. No Claim, Check Run Result or Review Report is modified. Make removals an explicit approval with visible affected Claims; default to keeping local Requirements.

## Acceptance — Given / When / Then

### GWT-01 — Selective field adoption
**Given** a local field conflicts with NEW and the user selects LOCAL  
**When** Apply completes  
**Then** the field retains LOCAL's value and unrelated accepted upstream changes are applied.

### GWT-02 — No silent deletion
**Given** NEW removes a Requirement with existing Claims  
**When** preview opens  
**Then** default is Keep; removal requires an explicit action and shows affected Claims.

### GWT-03 — Single active copy
**Given** a valid confirmed preview  
**When** Apply succeeds  
**Then** the single active copy for that `(namespace, pack_id)` contains the accepted result, no second active copy is created, and BASE and NEW files remain byte-identical.

### GWT-04 — Changed inputs
**Given** source or local bytes changed after preview  
**When** Apply is requested  
**Then** it is rejected and must be re-previewed, without altering existing artifacts.

### GWT-05 — Signing and origin integrity
**Given** one or more Requirement payloads change  
**When** Apply updates the active copy  
**Then** invalid former signatures are not retained; identity/status/origin are correct under approved contracts, and provenance is never falsely asserted for unaccepted upstream edits.

### GWT-06 — Atomic rollback
**Given** disk/rename error or Cancel  
**When** Apply aborts  
**Then** no partial live update or overwritten prior copy exists.

**Done when:** Users can make a selective, atomic update of the single active copy with unambiguous old/new values and no forged provenance or signature inheritance.
