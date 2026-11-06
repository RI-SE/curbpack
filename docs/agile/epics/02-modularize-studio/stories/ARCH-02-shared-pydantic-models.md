# ARCH-02 — Shared contract implementation

**Status:** Draft  
**Epic:** [EP-02](../EPIC.md)  
**Stage:** 4, after mechanical extraction/moves and headless logic separation.

**As a developer**, I want shared Pydantic contracts that faithfully implement the approved Packs v2 specification, so that the later FastAPI boundary can validate without changing persisted data.

## Work

- `docs/reference/packs2.md` is the human/PO-approved norm. Implement shared public models in `models/pydantic/`; generate JSON Schema from those models only when needed. Keep private types local unless genuinely shared.
- Include accepted VR-00 and VL-00 schema/verification changes only after their own stories and normative documents are approved. Never improvise namespace, signature or lifecycle fields within EP-02.
- Reuse validated domain operations from stage 3. Pydantic belongs at public boundaries; FastAPI types and request objects do not enter implementation logic.
- Add fixture-based compatibility tests **before** replacing current validation paths. Introduce one model/use-site at a time and test after each replacement.

## Acceptance (Given / When / Then)

1. **Given** representative existing Pack, Requirement, Claim, Run Result and Review Report fixtures, **when** they pass through approved Pydantic serialization, **then** their persistent data, signing/digest semantics and intended defaults are preserved.
2. **Given** invalid payloads and path/reference errors, **when** validated through the new boundary, **then** they are rejected correctly without weakening existing checks.
3. **Given** a difference between a proposed model and `packs2.md`, **when** encountered, **then** it is reported for explicit contract resolution, not silently accepted as a new norm.
4. **Given** one migrated use-site, **when** tests pass, **then** the next use-site may be converted; an OpenAPI document alone is not proof of compatibility.
