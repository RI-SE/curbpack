# UP-06 — Check declared origin against a nominated trusted source

**Epic:** [EP-15 — Update Pack](../EPIC.md)  
**Status:** Draft  
**Starts when:** UP-01 and VR-00 accepted.

**As a recipient of a third-party Pack**, I want to nominate a claimed predecessor and test its authenticity and declared relationship, so that `origin` is not mistaken for independently verified history.

## Behavior

Provide a simple read-only **Check origin** action (also callable from Update). The user points to a local/unpacked or imported candidate predecessor snapshot. Read the derivative's declared origin; match asserted namespace, pack id and version (and requirement id per Requirement); verify the candidate predecessor's Pack/Requirement signature **using existing VR-00 verification and locally configured trusted material**. Show separately: identity match; predecessor cryptographic authenticity status; byte/content fingerprint of predecessor; detectable changes against derivative; and whether there is a cryptographically pinned predecessor digest in an approved contract. Today `origin` lacks such an obligatory pin, so output must not claim 'verified derivation' or 'verified complete chain'.

An attacker can create a derivative and type `origin = RISE`, then sign their own Pack. Their signature authenticates the claim, not its truth. Another attack is omitting A from RISE→A→B. Provide clear 'asserted predecessor / source snapshot authenticated / relationship not cryptographically bound' language. No online search, CA service, new signing method, origin rewriting or silent contract extension. Authenticity of the nominated source depends on the receiver's trusted keys; an unknown key is not a success.

If Product Owner requires a strong chained proof, propose a separate contract decision (immutable predecessor digest/attestation and preservation rules) in `packs2.md` before building it; do not imply simple comparing of derivative bytes proves the original derivation event.

## Acceptance — Given / When / Then

### GWT-01 — Authentic predecessor
**Given** a derivative claims RISE/CRA 1.0 and the user supplies an authentic signed RISE/CRA 1.0 plus trusted key  
**When** Check origin runs  
**Then** identity and signature are reported as verified, a read-only diff is available, and the provenance relationship is described as asserted rather than cryptographically proven.

### GWT-02 — Fabricated origin
**Given** the derivative declares `KalleKula/CRA` but the nominated source is RISE/CRA  
**When** Check origin runs  
**Then** the mismatch is explicit and no verified-origin label appears.

### GWT-03 — Missing/untrusted predecessor
**Given** a missing candidate or a valid signature under an unknown key  
**When** Check origin runs  
**Then** result is missing/untrusted respectively, never silently 'verified'.

### GWT-04 — Tampered source
**Given** a signed predecessor whose content changed  
**When** verification runs  
**Then** verification fails distinctly from 'no signature'.

### GWT-05 — Trust laundering
**Given** B claims direct origin RISE while an intermediate A version exists  
**When** the user checks B against RISE  
**Then** the tool does not assert that A never existed or that B derived directly; it shows only the verified facts about the supplied source and the claimed link.

### GWT-06 — No mutation
**Given** any verification outcome  
**When** Check origin completes  
**Then** source, derivative, signature and Claims remain byte-identical.

**Done when:** The UI and API clearly distinguish authenticated predecessor material from unverified derivation and cannot turn an arbitrary `origin` string into trusted provenance.
