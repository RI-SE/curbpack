# ARCH-02 — Shared data contracts

**Status:** Draft; after pilot baseline.  
**Epic:** [EP-02](../EPIC.md)

**As a developer**, I want shared contracts in `models/pydantic/` and internal types in `models/internal/`, so that data is validated consistently without parallel schemas.

**Accept when:**
- Shared public Pydantic contracts reside in `models/pydantic/`; private types belong in `models/internal/` or remain local when not shared.
- Routers use Pydantic at HTTP boundaries and pass explicitly mapped, typed Python arguments to domain functions; domain code does not depend on FastAPI or HTTP request objects.
- `docs/reference/packs2.md` is the human/PO-approved normative contract. Pydantic implements it; JSON Schema is generated from Pydantic when required. Do not create a competing human-readable norm or hand-maintained JSON Schema. A mismatch is reported for an explicit contract decision, not silently resolved in code.
- EP-02 preserves accepted persisted formats and signature semantics; incorporate VR-00/VL-00 only after their approved contract changes. DOC-04 must not relocate `docs/reference/packs2.md`.
- Assert round-trip compatibility for representative persisted Requirement, Claim, Pack and report fixtures; test invalid payload rejection, defaults, references and signing/digest behavior. Generating OpenAPI alone is insufficient.
