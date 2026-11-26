# UP-05 — Worklist for only affected Claims

**Epic:** [EP-15 — Update Pack](../EPIC.md)  
**Status:** Draft  
**Starts when:** UP-03, UP-04 and VL-05/VL-06 accepted.

**As a product reviewer**, I want to see only the Claims that could require work after my accepted update, so that I can reuse valid previous work rather than re-reviewing everything.

## Behavior

Use the existing Claims backend and VL-06 impact logic for the currently open product repo. Compare Claim's qualified Requirement identity and `requirement_digest` with the **resulting** Requirement snapshot. Show separate exact-binding status (`match`, `stale`, `missing`), provenance/signature trust reading, Check outcome from a specified run (if available), and human action recommendation. Keep unchanged Claim files and prior results untouched. One Requirement may have multiple Claims; each is independently displayed. Existing Claims bound to the original source namespace are not silently remapped to a copied local namespace.

Offer **Review**, **Rebind**, **Discovery**, **Later** through existing UI/API. A verified `match` means identical Requirement binding only; it does not mean evidence is adequate or Checks passed. Rebind is user-confirmed and drops changed Claim seals; Check runs remain separate and user-triggered. Worklist for a removed Requirement requires explicit retire/keep/rebind disposition. New Requirements show no Claim yet and may start Discovery. Local-only unchanged Requirements and associated Claims are not added to the actionable subset.

## Acceptance — Given / When / Then

### GWT-01 — Minimal subset
**Given** 40 Claims of which 3 are bound to Requirements changed by accepted updates  
**When** impact is previewed  
**Then** exactly the potentially affected Claim identities are displayed for action, with 37 unaffected Claims not demanded as rework; full counts remain visible.

### GWT-02 — Hints-only stale
**Given** a Claim's Requirement changes only `discovery_hints`  
**When** Update is applied  
**Then** the Claim remains byte-identical and its binding is accurately `stale`; the UI can label review as potentially lightweight but never auto-rebinds.

### GWT-03 — Rebind/Discovery/Later
**Given** a Claim requiring review  
**When** the user selects Review, Rebind, Discovery or Later  
**Then** the existing corresponding workflow opens with workspace/Requirement identity preserved; Later does not mutate artifacts.

### GWT-04 — Removed Requirement
**Given** an accepted deletion with linked Claims  
**When** Update calculates impact  
**Then** those Claims show `missing` for the resulting snapshot and an explicit disposition is offered; deletion never auto-deletes Claim files.

### GWT-05 — Reports unchanged
**Given** historical signed Claims, Run Results and Review Reports  
**When** Update previews/applies  
**Then** those files are not changed and historical exact references remain resolvable under VL-05.

### GWT-06 — Correct isolation
**Given** two packs/namespaces reuse a Requirement ID  
**When** Claim impact is calculated  
**Then** the wrong namespace's Claims are never included as affected solely by ID equality.

**Done when:** Update yields an explainable, reproducible potentially affected Claim subset and reuses the existing user actions without creating any new Claim lifecycle.
