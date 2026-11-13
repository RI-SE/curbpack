# VL-04 — Bind Claims to exact Requirements

**Epic:** EP-11 — Pack Version Lifecycle

**Starts when:** VL-00 is accepted.

**As a reviewer**, I want every Claim to reference the exact Requirement version it was assessed against, so that changes to Requirements are detected and clearly reported without interrupting Check execution.

## Behavior

### Claim binding

Extend the Claim contract with:

- Full Requirement identity: `namespace`, `pack_id`, `requirement_id`.
- `requirement_digest`: the canonical Requirement payload digest defined in Packs v2.

These fields form part of the Claim's signed payload.

### Creating and editing Claims

Discovery and Claims Editor use the same backend binding operation to resolve the selected Requirement and record its digest.

Ordinary edits preserve the existing binding. Only explicit rebinding updates the Requirement identity or digest.

A changed binding invalidates the previous Claim signature.

### Curbcheck

Curbcheck resolves the referenced Requirement and compares its current digest with the digest recorded in the Claim.

Report the binding status as:

- `match` — current Requirement matches the recorded digest.
- `stale` — Requirement exists but its digest differs.
- `missing` — referenced Requirement cannot be resolved.

**Binding status never prevents execution of configured Checks.**

Run all configured Checks according to their existing execution semantics, regardless of binding status. Report binding findings independently of Check outcomes.

A passing Check must not conceal a stale or missing Requirement binding.

### Run Result and Review

Record the Requirement identity, expected digest, actual digest when available, binding status, Claim digest and individual Check outcomes in the Run Result.

Review displays these facts separately, including Claim signature validity.

### Architecture

Requirement resolution, digest calculation and binding validation belong to shared backend components.

Discovery, Claims Editor, Curbcheck and Review reuse those components.

The UI only presents backend results and invokes backend operations. It contains no business logic.

## Acceptance — Given / When / Then

### GWT-01 — Create binding

**Given** a Requirement selected through Discovery or Claims Editor  
**When** a Claim is created  
**Then** its full Requirement identity and current digest are recorded.

### GWT-02 — Preserve binding

**Given** an existing Claim binding  
**When** the Claim is edited without explicit rebinding  
**Then** its Requirement identity and digest remain unchanged.

### GWT-03 — Rebind

**Given** a Claim bound to Requirement digest A  
**When** the user explicitly rebinds it to digest B  
**Then** the binding is updated and the previous Claim signature is invalidated.

### GWT-04 — Matching Requirement

**Given** a Claim whose Requirement digest matches the current Requirement  
**When** Curbcheck runs  
**Then** binding status is `match` and all configured Checks execute normally.

### GWT-05 — Stale Requirement

**Given** a Claim bound to digest A and a current Requirement with digest B  
**When** Curbcheck runs  
**Then** binding status is `stale`, both digests are reported, and all configured Checks execute normally.

### GWT-06 — Missing Requirement

**Given** a Claim whose Requirement cannot be resolved  
**When** Curbcheck runs  
**Then** binding status is `missing`, the unresolved identity is reported, and all configured Checks execute normally.

### GWT-07 — Independent results

**Given** a Claim with stale or missing binding and passing Checks  
**When** the Run Result is generated  
**Then** the passing Check outcomes and the binding issue are both recorded without changing either result.

### GWT-08 — Review presentation

**Given** a Run Result containing binding findings and Check outcomes  
**When** Review displays the Claim  
**Then** Requirement binding, Claim signature validity and Check outcomes are shown as separate facts.

### GWT-09 — Shared backend

**Given** a binding created through Discovery or Claims Editor  
**When** Curbcheck and Review process it  
**Then** they use the same backend identity, digest and binding semantics without implementing business rules in the UI.

### GWT-10 — Regression

**Given** VL-04 is implemented  
**When** the full existing test suite runs  
**Then** all tests pass, including focused tests for GWT-01 through GWT-09.

**Done when:** Claims reference exact Requirements, stale and missing bindings are reported consistently, all Checks continue to execute, and Review displays the complete results without conflating binding status with Check outcomes.