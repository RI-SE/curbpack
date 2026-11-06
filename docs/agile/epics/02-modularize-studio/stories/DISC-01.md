# DISC-01 — Pluggable Discovery providers

**Status:** Draft. Not authorization to implement.  
**Epic:** TBD — Discovery extensibility  
**Depends on:** Existing Discovery, Human Review and Packs v2 contracts.

## Story

**As a Curbpack developer**, I want Discovery to load interchangeable evidence providers through a common interface, so that new search methods, scanners and AI agents can contribute evidence candidates without changing the Discovery workflow.

## Current state

Discovery already separates candidate retrieval (`search`) from AI assessment (`assess`) through callable interfaces in `discovery/jobs.py`.

However:

- The default retrieval searches Markdown files only.
- Candidate handling assumes file paths and text excerpts.
- The job runner invokes assessment for every retrieved candidate.
- Candidate normalization discards provider-specific information.
- AI assessment influences which candidates appear for human inspection.

Adding sources such as Trivy reports or external agents therefore requires changes to the current Discovery pipeline.

## Desired state

Discovery discovers providers from a fixed package location, using a small common Python contract.

Each provider:

- Accepts the selected repository and Requirement, including its existing `discovery_hints`.
- Returns zero or more structured evidence candidates.
- Identifies the evidence source and a resolvable locator.
- May include a rationale or assessment, but does not have to use AI.
- Never creates or modifies Requirements, Claims or Checks.

The existing Markdown retrieval becomes the first provider.

The existing Qwen assessment remains available as an optional assessment step. It must not be required for evidence to reach human inspection.

Providers may use deterministic searches, structured reports or AI agents, but **all candidates pass through the same human-controlled workflow**.

## Requirements (Given / When / Then)

### R1 — Discover providers

**Given** a valid Discovery provider module under the declared package root  
**When** Discovery enumerates available providers  
**Then** the provider is available without modifying a central handler table  
**And** modules outside the declared root are not loaded.

### R2 — Common candidate contract

**Given** different providers return evidence candidates  
**When** Discovery collects their results  
**Then** candidates retain their provider identity, evidence locator and rationale  
**And** provider-specific metadata required for inspection is not silently discarded  
**And** malformed candidates are reported rather than accepted as valid evidence.

### R3 — AI is optional

**Given** a provider returns a valid candidate without AI assessment  
**When** Discovery processes the result  
**Then** the candidate remains available for human inspection  
**And** the absence or failure of an AI service does not silently discard it  
**And** an unassessed candidate is not presented as AI-validated.

### R4 — Existing behavior is preserved

**Given** the existing Markdown provider and current Discovery fixtures  
**When** Discovery executes through the new provider interface  
**Then** existing retrieval, feedback and human selection behavior is preserved  
**And** existing Discovery entry points continue to work.

### R5 — Structured evidence

**Given** a provider that recognizes a Trivy JSON report in the selected repository  
**When** Discovery executes for a relevant Requirement  
**Then** it can return the report as an inspectable evidence candidate  
**And** Discovery does not interpret the report as proof of compliance or automatically create a Claim.

A small test provider and fixture are sufficient. This requirement does not authorize building a complete Trivy integration.

### R6 — Human decision remains authoritative

**Given** candidates from one or more providers  
**When** a user reviews the Discovery results  
**Then** the user can inspect, accept or reject candidates through the existing workflow  
**And** no provider can automatically approve a candidate or persist a Claim  
**And** the existing Claims and Checks contracts remain unchanged.

### R7 — Isolation and failures

**Given** a provider fails, returns malformed data or references evidence outside the selected repository  
**When** Discovery processes its output  
**Then** the failure is reported without accepting invalid evidence  
**And** other providers can still return their candidates  
**And** repository confinement rules remain enforced.

## Out of scope

- Changes to Packs v2, Requirements, Claims or Checks schemas.
- A new agent framework, marketplace or remote plugin installation.
- Loading executable plugin code from a product repository or Pack.
- Implementing Hivemind or other external agent integrations.
- New Check implementations or vulnerability policies.
- Redesigning Human Review.
- Automatic approval of discovered evidence.

## Acceptance

- Existing Discovery tests and relevant end-to-end flows pass.
- A test provider can be added without modifying the Discovery job runner.
- Markdown retrieval continues to work.
- Structured JSON evidence can be presented for human inspection.
- Discovery works without Ollama.
- No provider bypasses human selection or changes signed artefacts.

## Stop if

- Implementing providers requires changing Packs v2.
- The implementation introduces a second Discovery workflow or human-review mechanism.
- Providers can execute arbitrary code supplied by the examined product.
- AI assessment remains mandatory for candidate visibility.

**Implementation boundary:** Reuse the existing Discovery subsystem, job persistence and UI. Introduce only the minimum provider contract and dispatch needed to satisfy the acceptance tests.

Do not implement until the story and its epic placement are accepted.