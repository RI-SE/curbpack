# UP-01 — Select and identify three Pack snapshots

**Epic:** [EP-15 — Update Pack](../EPIC.md)  
**Status:** Draft  
**Starts when:** Pilot 2 checkpoint and EP-11 VL-00–VL-02 accepted.

**As a product maintainer**, I want to select an existing local working copy, the exact original upstream release it is based on, and a newer upstream Pack, so that an update never guesses which files or publisher I mean.

## Behavior

Select immutable **BASE** (publisher release previously adopted), **LOCAL** (current owned working copy), and **NEW** (explicitly imported or local newer publisher release). Identify Pack `(namespace,id,version)` and each Requirement `(namespace,pack_id,id)`; display the selected paths, origin declarations, and signature readings independently. `origin` is an asserted hint, not proof. Validate pack memberships, identifiers and safe filesystem confinement; fail ambiguous or missing source lookup. Do not use the latest local directory implicitly when an exact BASE is required. Import ZIP reuses VL-02; it does not auto-apply. The service returns a read-only transient selection context, not a new persistent update record.

Current `curbpack.json` packs and filesystem paths are unqualified; ambiguity from two namespaces with the same pack ID must be detected and **blocked explicitly**, never resolved by choosing first. A new selection/path contract, if required, needs PO approval in `workspace.md` before implementation.

## Acceptance — Given / When / Then

### GWT-01 — Three exact inputs
**Given** an identifiable upstream RISE 1.0, local A copy and upstream RISE 1.1  
**When** the user selects them  
**Then** the backend reports the exact paths, namespace-qualified identities, versions and declared origin without modifying any files.

### GWT-02 — Missing predecessor
**Given** the local Pack declares upstream 1.0 but that snapshot is unavailable  
**When** Update starts  
**Then** three-way Apply is disabled and the missing BASE is clearly reported; the user may supply it manually.

### GWT-03 — Foreign or unrelated update
**Given** NEW is not the selected upstream namespace and Pack identity  
**When** the user attempts to treat it as an update  
**Then** the operation fails with a meaningful mismatch instead of silently comparing unrelated Packs.

### GWT-04 — Collision and confinement
**Given** duplicate `pack_id` values across namespaces, traversal/absolute path inputs, or symlink escape  
**When** selection resolves a snapshot  
**Then** ambiguity or unsafe location is rejected; valid locations still work.

### GWT-05 — Read-only and regression
**Given** valid source and local files  
**When** the user previews selection or imports the new ZIP  
**Then** original source, local Requirements/Claims and reports retain their bytes; existing Import behavior remains intact.

**Done when:** Every subsequent Update operation receives explicit, confined and unambiguous BASE/LOCAL/NEW snapshot identities.
