# VL-00 — Introduce namespace, origin and status contracts

**Epic:** EP-11 — Pack Version Lifecycle

**As a developer**, I want namespace, origin and status metadata introduced consistently across Curbpack, while preserving existing workflows, so that cross-namespace ownership can be implemented separately in VL-01.

## Scope

Extend the existing data contracts:

| Object | Fields |
|---|---|
| `curbpack.json` | `namespace_base: string` |
| Pack | `namespace: string`, `origin?`, `status` |
| Requirement | `namespace: string`, `origin?`, `status` |

### Namespace and identity

- `namespace_base` identifies the current publisher's base namespace, e.g. `RISE`.
- A new Pack namespace is `<namespace_base>/<pack.name>`, e.g. `RISE/CRA`.
- Every Requirement explicitly carries the namespace of its containing Pack.
- Pack identity is `namespace + id`; a release additionally has `version`.
- Requirement identity is `namespace + pack_id + id`.
- `origin` is optional and identifies the source object, including namespace, Pack ID, source version and Requirement ID where applicable.
- `origin` is a publisher's provenance claim, not an independently verified history.
- Existing namespace and origin values must not be automatically rewritten.

### Status

Replace Pack `assurance_class` with a simple status field on both Packs and Requirements:

- `draft` — work in progress, not declared reviewed.
- `reviewed` — the signer declares that the object has been reviewed.

Default status is `draft`.

Status describes the publisher's declared review state. It is not derived from signature validity, and signing a draft does not automatically change its status.

Pack status applies to the Pack as a collection. It does not automatically change or imply `reviewed` status for individual Requirements.

### Signing

Preserve the existing signing mechanism.

- Status, namespace and origin are part of each object's signed payload.
- A Requirement signature covers that Requirement's payload.
- A Pack signature covers the complete Pack directory, including signed and unsigned Requirements.
- A Pack may be signed while its Requirements remain unsigned or in `draft` status.
- Signing does not change status.
- Editing any signed payload invalidates the affected signature.
- A valid signature authenticates the signer's declaration and protected content; it does not independently establish legal correctness or the truth of origin.

No Publish approval requirement is introduced.

Update the schemas, validators, serializers and `docs/reference/packs2.md` consistently.

## Reference data

Inspect and update:

- `doc/reference/test-packs/` — determine which fixtures are still used before modifying or removing any.
- `reference-product/external_testing/curbpack/`
- Other affected fixtures identified by the existing tests.

Migrate existing RISE Packs and Requirements to valid RISE namespaces.

Replace existing `assurance_class` values with `status: draft`, unless an existing, explicit review decision justifies another status.

Do not invent origin information or assume historical approval.

Regenerate affected test signatures using the existing mechanism, or retain explicitly unsigned fixtures where permitted.

## Acceptance — Given / When / Then

### GWT-01 — Workspace namespace

**Given** a valid `curbpack.json`  
**When** its configuration is loaded  
**Then** `namespace_base` is available and validated as a non-empty string.

### GWT-02 — Pack identity

**Given** a Pack with namespace, ID and version  
**When** it is validated and loaded  
**Then** its identity is preserved and unambiguous.

### GWT-03 — Requirement identity

**Given** a Requirement belonging to a Pack  
**When** it is validated  
**Then** its namespace matches the containing Pack and its `pack_id` identifies that Pack.

### GWT-04 — Optional origin

**Given** a Pack or Requirement with or without origin  
**When** it is validated and serialized  
**Then** a present origin is validated and preserved, and an absent origin remains absent.

### GWT-05 — Distinct identities

**Given** two Packs with identical IDs but different namespaces  
**When** their identities are resolved  
**Then** they remain distinguishable.

**And given** Requirements with identical IDs in different Packs  
**When** their identities are resolved  
**Then** they remain distinguishable.

### GWT-06 — Status validation

**Given** a Pack or Requirement  
**When** its status is validated  
**Then** only defined status values are accepted, and missing status defaults to `draft`.

### GWT-07 — Independent status and signature

**Given** a Pack with `status: draft` containing unsigned Requirements  
**When** the Pack is signed and verified  
**Then** its signature is valid without requiring individual Requirement signatures or changing any status.

### GWT-08 — Signed status integrity

**Given** a signed Pack or Requirement  
**When** its status, namespace, origin or other signed content is modified  
**Then** its previous signature no longer verifies.

### GWT-09 — Existing reference data

**Given** existing RISE reference Packs and Requirements  
**When** they are loaded using the updated contracts  
**Then** they have valid namespaces and statuses, and retain their functional content.

### GWT-10 — Existing workflows

**Given** existing supported workflows  
**When** they execute against the migrated data  
**Then** their behavior remains unchanged, except for validation and representation required by the new contracts.

### GWT-11 — Regression

**Given** the contracts and reference data have been updated  
**When** the full existing test suite runs  
**Then** all tests pass, including focused tests for GWT-01 through GWT-10.

## Boundaries

- No ownership confirmation or cross-namespace copying; that belongs to VL-01.
- No automatic namespace or origin rewriting.
- No automatic Claim rebinding.
- No new signing mechanism.
- No new Publish workflow or approval gate.
- No unrelated refactoring.
- Preserve existing architecture and test conventions.

**Done when:** Namespace, origin and status contracts are consistent across documentation, code and reference data, existing workflows remain operational, and the full regression suite passes.