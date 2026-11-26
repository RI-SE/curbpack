# VL-06 — Review affected Claims after Requirement changes

**Epic:** EP-11 — Pack identity, exchange and traceability  
**Status:** Draft  
**Depends on:** VL-03, VL-04 and VL-01 for cross-namespace ownership.

## Story

**As a Requirement editor**, I want to see which existing Claims are affected when I change a Requirement, so that I can review their bindings, explicitly rebind them or run Discovery to find suitable evidence.

## Behaviour

When a Requirement is saved or changes are applied through Compare, Studio checks the Claims in the currently open product workspace.

If the Requirement payload digest changed, Studio identifies Claims bound to its previous identity and digest.

The Requirement save completes independently of Claim review. Studio then presents the affected Claims with their binding information and offers:

- **Review Claim:** Open the existing Claims Editor, showing the old and current Requirement bindings. The user may explicitly rebind after reviewing the evidence and configured Checks.
- **Discovery:** Open the existing Discovery workflow for the updated Requirement. Candidates do not automatically create, replace or delete Claims.
- **Later:** Leave all Claims unchanged.

The same affected-Claims information is available when reopening the Requirement, not only immediately after Save.

When Take Ownership creates a new namespace-qualified Pack, Studio distinguishes existing Claims bound to the source Pack from Claims bound to the new Pack. It may offer explicit rebinding to the new identity, but must not automatically classify the source binding as stale merely because a copy was created.

Only Claims accessible through the currently open workspace are inspected. Studio does not assume knowledge of Claims maintained in other repositories or organizations.

Claim discovery, binding validation and rebinding are backend operations owned by Claims. Requirements invokes these operations; the UI only presents their results and the available actions.

## Acceptance criteria

### VL06-01 — Changed Requirement with existing Claims

**Given** a Requirement has Claims bound to its current identity and digest  
**When** the user changes and saves its payload  
**Then** the Requirement is saved  
**And** Studio shows the affected Claims and their previous/current Requirement information  
**And** no Claim is modified automatically.

### VL06-02 — Unchanged digest

**Given** a Requirement is saved without changing its payload digest  
**When** Studio evaluates Claim impact  
**Then** no newly stale Claims are reported.

### VL06-03 — Review and rebind

**Given** an affected Claim is shown  
**When** the user opens it in the Claims Editor  
**Then** the previous binding and proposed target are visible  
**And** the user can explicitly rebind using VL-04  
**And** a changed Claim payload loses its previous embedded signature  
**And** its configured Checks and evidence are preserved unless explicitly edited.

### VL06-04 — Discovery

**Given** an affected Requirement  
**When** the user chooses Discovery  
**Then** the existing Discovery workflow opens for that Requirement  
**And** no Claim is created, replaced or deleted without an explicit user action.

### VL06-05 — Review later

**Given** the user leaves affected Claims unchanged  
**When** the Requirement is reopened  
**Then** Studio can show the unresolved bindings again  
**And** no separate persistent update queue is required.

### VL06-06 — Cross-namespace ownership

**Given** a foreign Pack is copied through VL-01  
**When** Studio examines existing Claims referencing the source Pack  
**Then** the source identity and the new local identity remain distinct  
**And** any move to the new Requirement requires explicit rebind.

### VL06-07 — Historical integrity

**Given** earlier Run Results or Review Reports refer to the previous Requirement  
**When** a Requirement is saved or a Claim is rebound  
**Then** those historical records remain unchanged.

### VL06-08 — Existing Check execution

**Given** Claims have unchanged, stale or missing Requirement bindings  
**When** Curbcheck runs  
**Then** all configured Checks execute according to VL-04  
**And** binding status and technical Check outcomes remain separate.

### VL06-09 — Component boundaries

**Given** Claim-impact information is requested from Requirements or Compare  
**When** the operation executes  
**Then** it uses the shared Claims backend functionality  
**And** neither Requirements UI nor TypeScript implements digest comparison, Claim mutation or binding decisions.

### VL06-10 — Regression

Existing Requirement editing, Compare/Apply, Claims Editor, Discovery, signing, Curbcheck, Run Results and Review workflows continue to pass their regression tests.

## Done when

Requirement edits reliably expose affected Claims and offer explicit Review, Rebind or Discovery without changing existing Claims, historical records or Check execution automatically.