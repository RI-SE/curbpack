# VL-05 — Resolve historical Requirement and Claim chain

**Epic:** EP-11 — Pack Version Lifecycle

**Starts when:** VL-04 is accepted.

**As a reviewer**, I want Curbpack to locate the exact Requirements and Claims referenced by a Run Result, including historical versions in Git, so that I can inspect what was actually evaluated and identify any missing or changed evidence.

## Behavior

### Resolver

Implement a reusable backend resolver that reconstructs the relationship:

`Requirement → Claim → Run Result → Check results`

Use the identities and digests established in VL-04.

For each referenced Requirement and Claim:

1. Check whether the current object matches the recorded identity and digest.
2. If it does not match, search the local Git history for an object with the exact identity and digest.
3. Verify that any recovered content actually matches the recorded digest.
4. Return the matching object and its location, including Git commit when recovered from history.
5. Report objects that cannot be found or whose digests do not match.

A Git match identifies historical content. Git signature verification, when available, uses the existing verification mechanism. Finding a matching digest does not itself establish that the historical content was signed.

The resolver must distinguish a historical match from the current version. It must not substitute a different object or silently update any binding.

### Chain verification

The resolver verifies that:

- The Claim references the expected Requirement identity and digest.
- The resolved Claim digest matches the digest recorded in the Run Result.
- The Run Result's Check outcomes correspond to the recorded Claim and Check configuration.

Report each relationship separately so that a missing or mismatched object does not conceal the remaining findings.

### Review

Review uses the resolver to display the reconstructed chain.

For each object, show:

- Identity and recorded digest.
- Current or historical version found.
- Matching or mismatching digest.
- Git commit when applicable.
- Signature verification status.
- Missing objects or broken relationships.

Where current and historical versions are both available, let the reviewer inspect their differences using the existing comparison functionality.

The resolver performs all Git access, digest calculations and chain validation. The Review UI only presents its results and invokes backend operations.

### Execution

Resolution is read-only and does not modify Requirements, Claims, Run Results or repository history.

Missing Git history or unresolved objects are reported explicitly. They do not prevent resolution of the remaining chain or block Review.

## Acceptance — Given / When / Then

### GWT-01 — Current Requirement

**Given** a Run Result referencing a Requirement digest that matches the current Requirement  
**When** the resolver runs  
**Then** it identifies the current Requirement and reports a matching digest.

### GWT-02 — Historical Requirement

**Given** the current Requirement differs from the digest referenced by a Claim, and a matching version exists in local Git history  
**When** the resolver runs  
**Then** it identifies the historical Requirement, verifies its digest and reports the Git commit.

### GWT-03 — Historical Claim

**Given** the current Claim differs from the Claim digest recorded in the Run Result, and a matching version exists in Git history  
**When** the resolver runs  
**Then** it identifies the historical Claim and its Git commit.

### GWT-04 — Chain verification

**Given** a Run Result with resolvable Requirement and Claim references  
**When** the resolver reconstructs the chain  
**Then** it verifies the recorded identities, digests and Check configuration against the resolved objects.

### GWT-05 — Missing history

**Given** an object whose recorded digest cannot be found among current files or in local Git history  
**When** the resolver runs  
**Then** it reports the object as unresolved with its identity and expected digest, without substituting another version.

### GWT-06 — Changed current objects

**Given** historical Requirement and Claim versions match a Run Result, but their current versions differ  
**When** Review displays the chain  
**Then** the historical matches and current differences are clearly distinguished.

### GWT-07 — Signature information

**Given** a resolved object with an object signature or an applicable signed Git commit  
**When** its signature status is requested  
**Then** Review displays the verification result and method provided by the existing signature verification component.

### GWT-08 — Partial resolution

**Given** a chain in which one object cannot be resolved  
**When** the resolver runs  
**Then** it reports the missing link and continues resolving and reporting the remaining objects.

### GWT-09 — Compare versions

**Given** both historical and current versions of a Requirement are available  
**When** the reviewer requests a comparison  
**Then** the existing Requirement comparison functionality displays their differences without modifying either version.

### GWT-10 — Read-only resolution

**Given** a repository containing current and historical Requirements, Claims and Run Results  
**When** the resolver executes  
**Then** no source files, bindings, signatures or Git history are modified.

### GWT-11 — Backend separation

**Given** Review requests historical chain information  
**When** it displays the results  
**Then** Git lookup, digest verification and chain resolution are performed by the backend resolver, with no corresponding business logic in the UI.

### GWT-12 — Regression

**Given** VL-05 is implemented  
**When** the full existing test suite runs  
**Then** all tests pass, including focused tests for GWT-01 through GWT-11.

**Done when:** Review can reconstruct the exact Requirement–Claim–Check chain from a Run Result, recover matching historical versions from Git where available, and clearly report every verified, changed or missing link without altering the underlying evidence.