# TL-02 — Use Claims and Discovery operations from CLI

**Status:** Draft; after relevant EP-02 Claims migration.
**Epic:** [EP-09](../EPIC.md)

**As an engineer**, I want to invoke supported Claims and Discovery operations headlessly, so that I can automate or test them without a browser.

## Acceptance — Given / When / Then

**Given** an implemented `studio/claim/impl/` operation **when** called by the CLI **then** the CLI uses that operation, as does the owning REST router; there is no duplicate search, Claim-binding or signing logic.

**Given** Discovery output **when** presented by CLI **then** candidates remain proposals and no Claim is written without an explicit binding operation.

**Given** a Claim edit **when** persisted through CLI **then** the same validation, signature invalidation and preservation rules as the backend apply.

**Given** a headless environment **when** this CLI runs **then** it does not require FastAPI, TypeScript pages or the Studio server.

New namespace/digest binding behavior comes from VL-04 after its acceptance. No standalone Claims GUI process is required.
