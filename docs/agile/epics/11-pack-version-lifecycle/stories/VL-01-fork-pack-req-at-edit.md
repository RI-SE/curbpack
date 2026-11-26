# VL-01 — Take ownership on cross-namespace edit

**Epic:** [EP-11 — Pack identity, exchange and traceability](../EPIC.md)

**Starts when:** VL-00 is accepted.

**As a user**, I want to take ownership of an imported Pack when editing one of its Requirements, so that I become responsible for the entire modified Pack while the original remains unchanged.

## Behavior

Determine the target namespace from `curbpack.json`:

`target_namespace = namespace_base + "/" + pack.name`

When editing a Requirement:

- If the Pack already belongs to the target namespace, use normal editing.
- Otherwise, require explicit confirmation before taking ownership of the entire Pack.

**Confirmation dialog:**

> **Take ownership of this Pack?**
>
> You are about to modify a Pack published under another namespace.
>
> By continuing, you take responsibility for maintaining your own copy of the entire Pack, including all its Requirements.
>
> The original Pack remains unchanged. Your copy is unsigned and requires your own review; signing is a separate action, not a condition for export.
>
> **Cancel | Take ownership**

On confirmation, atomically:

1. Copy the entire Pack and all its Requirements.
2. Set the new Pack namespace to `target_namespace` and `pack.origin` to the source Pack's fully qualified identity and version.
3. Set every copied Requirement's namespace to `target_namespace` and its origin to the corresponding source Requirement's fully qualified identity and source Pack version.
4. Apply the requested Requirement edit to the copy.
5. Remove the copied Pack's and Requirements' `signed` blocks.
6. Activate the new unsigned working copy.

Preserve the original Pack and Requirements, including their signatures. Never overwrite an existing target Pack or automatically merge.

## Acceptance — Given / When / Then

### GWT-01 — Edit within current namespace

**Given** a Pack whose namespace matches the target namespace  
**When** a user edits a Requirement  
**Then** normal editing applies, without an ownership confirmation, and existing namespace and origin values remain unchanged.

### GWT-02 — Ownership confirmation

**Given** a Pack whose namespace differs from the target namespace  
**When** a user requests to edit one of its Requirements  
**Then** the ownership confirmation is displayed before any changes are made.

### GWT-03 — Cancel ownership

**Given** the ownership confirmation is displayed  
**When** the user selects Cancel  
**Then** no Pack, Requirement, signature or working-copy state is changed.

### GWT-04 — Confirm ownership

**Given** a foreign Pack containing multiple Requirements  
**When** the user confirms Take ownership  
**Then** the entire Pack is copied to the target namespace, with the correct Pack and Requirement origins, and the requested edit is applied only to the new copy.

### GWT-05 — Preserve original

**Given** ownership has been transferred to a new copy  
**When** the source Pack and Requirements are inspected  
**Then** their content, identity and signatures are unchanged and remain independently verifiable.

### GWT-06 — Signature invalidation

**Given** ownership has been confirmed  
**When** the new working copy is created  
**Then** the copied Pack and all its Requirements have no `signed` blocks and are presented as unsigned drafts.

### GWT-07 — Existing origin

**Given** the source Pack or Requirements already have origin metadata  
**When** ownership is taken  
**Then** the new copy's origin references the immediate source objects, while the source objects and their existing origins remain unchanged.

### GWT-08 — Target collision

**Given** a Pack with the same target namespace and Pack ID already exists  
**When** ownership is requested  
**Then** the operation is rejected without overwriting, merging or modifying either Pack.

### GWT-09 — Atomic failure

**Given** an ownership operation fails at any stage  
**When** the failure is handled  
**Then** no partial target Pack or partially modified Requirements remain, and the original is unchanged.

### GWT-10 — Display identity and origin

**Given** a Pack or Requirement has namespace, origin and signature metadata  
**When** the user opens its view  
**Then** the current identity, claimed origin (if present) and signature status are displayed distinctly.

### GWT-11 — Regression

**Given** the namespace and ownership functionality is implemented  
**When** the full existing test suite runs  
**Then** all tests pass, including focused tests for GWT-01 through GWT-10.

## Boundaries

- Reuse the contracts introduced in VL-00.
- No automatic upstream synchronization, inheritance, merging or provenance verification.
- No automatic Claim rebinding.
- Preserve existing application architecture and UI conventions.
- No unrelated refactoring.

**Done when:** All GWT scenarios pass and the existing application behavior remains intact outside the explicitly defined ownership operation.
