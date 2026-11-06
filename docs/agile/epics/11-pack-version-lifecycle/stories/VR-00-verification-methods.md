# VR-00 — Unified signature verification and non-blocking export

**Epic:** [EP-11 — Pack identity, exchange and traceability](../EPIC.md)

**Starts when:** Immediately. Must be accepted before VL-00 and VL-01.

**As a user**, I want Curbpack to recognize either an object signature or a verified signed Git commit, report the actual signature status, and allow export regardless of that status, so that I can exchange work-in-progress Packs without artificial approval gates.

## Scope

### Signature verification

Use one consistent verification model for Packs and Requirements.

An object may be authenticated by:

- Its own valid `signed` block.
- A verified signed Git commit covering the object's current content.

Git verification must establish that the signature is trusted and that the committed content matches the current object. A signed commit on a different version, an uncommitted modification or a dirty working tree affecting the object must not count as valid verification.

Verification must not require network access.

Report the actual result:

| Status | Meaning |
|---|---|
| `valid` | A supported signature verifies the current content |
| `invalid` | A signature exists but cannot be verified against the current content or trust configuration |
| `unsigned` | No applicable signature exists |

Include the verification method (`object`, `git` or `none`), signer, version identity and reason where applicable. Do not present a Git author or committer name as a verified signer.

A failed object signature must remain visible. Git verification must not silently conceal an invalid object signature.

### Remove `unsigned_requirements`

Remove the `unsigned_requirements` policy and its values (`reject`, `report`, `signed_commit`) from the current configuration contract, validators, defaults, UI and tests.

Do not replace it with another blocking signature policy.

Update `docs/reference/packs2.md`, `docs/reference/workspace.md` and other affected documentation so that the contract has one authoritative meaning.

### Pack signing

Preserve the existing Pack signing mechanism.

- A Pack signature covers the complete Pack directory, including every Requirement and its current contents.
- Requirements may be individually signed or unsigned.
- Signing a Pack must not require individual Requirement signatures.
- Signing does not imply that the Requirements have been reviewed or approved.
- Any change to the signed Pack directory, including adding a Requirement signature, invalidates the previous Pack signature.

### Export

Export must remain available regardless of signature status.

Before export, show or provide a report containing:

- Pack signature status.
- Each Requirement's signature status and verification method.
- Missing or invalid signatures and their reasons.

Do not silently sign, repair, modify or approve anything during export.

Export the existing Pack content without changing its payload. Preserve the current export format; introducing ZIP packaging is outside this story.

### Publish

Inspect existing Publish entry points and callers to establish whether the functionality is still used.

Do not remove, redesign or extend Publish in this story. Record whether it is reachable and whether its existing signature requirements conflict with the new verification contract.

## Acceptance — Given / When / Then

### GWT-01 — Valid object signature

**Given** a Pack or Requirement with a valid `signed` block  
**When** its signature is verified  
**Then** the result is `valid`, the method is `object`, and the verified signer and content identity are reported.

### GWT-02 — Valid Git signature

**Given** an object without a `signed` block, whose current content is covered by a trusted signed Git commit  
**When** its signature is verified  
**Then** the result is `valid`, the method is `git`, and the verified Git signer and commit identity are reported.

### GWT-03 — Changed Git content

**Given** an object whose last relevant Git commit is signed  
**When** its current content differs from the committed version  
**Then** the object is not reported as validly signed, and the reason identifies the content mismatch.

### GWT-04 — Invalid object signature

**Given** an object with an invalid or unverifiable `signed` block  
**When** verification runs  
**Then** the result is `invalid`, with an actionable reason, and a Git signature does not silently conceal the failure.

### GWT-05 — Unsigned object

**Given** an object with neither an object signature nor an applicable signed Git commit  
**When** verification runs  
**Then** the result is `unsigned`, with method `none`.

### GWT-06 — Sign Pack with unsigned Requirements

**Given** a Pack containing unsigned Requirements  
**When** the user signs the Pack  
**Then** Pack signing succeeds without signing or modifying the individual Requirements.

**And when** the Pack signature is verified  
**Then** it verifies the complete Pack directory.

### GWT-07 — Pack integrity

**Given** a validly signed Pack  
**When** a Requirement is added, removed, edited or individually signed  
**Then** the previous Pack signature no longer verifies.

### GWT-08 — Non-blocking export

**Given** a Pack containing validly signed, invalidly signed and unsigned Requirements  
**When** the user exports it  
**Then** the export succeeds, the signature report identifies each condition, and no source object is modified.

### GWT-09 — Remove obsolete policy

**Given** a Curbpack configuration or UI  
**When** it is validated or displayed  
**Then** `unsigned_requirements` is no longer an available policy, and no hidden `reject` default governs verification or export.

### GWT-10 — Consistent verification

**Given** the same Pack or Requirement and trust configuration  
**When** verification is requested through different supported CLI, API or UI paths  
**Then** they report consistent signature results and reasons.

### GWT-11 — Publish inventory

**Given** the existing Publish implementation  
**When** its entry points, references and callers are inspected  
**Then** its actual usage and any conflicting signature requirements are documented, without changing Publish behavior.

### GWT-12 — Regression

**Given** the signature and export contracts have been updated  
**When** the full existing test suite runs  
**Then** all tests pass, including focused tests for GWT-01 through GWT-11.

## Boundaries
Implement only the behavior specified in this story and its acceptance criteria. Preserve existing behavior otherwise.

**Done when:** Object and Git signatures are evaluated consistently, Pack signing permits unsigned Requirements, export never blocks on signature status, obsolete policy assumptions are removed, Publish usage is documented, and the full regression suite passes.
