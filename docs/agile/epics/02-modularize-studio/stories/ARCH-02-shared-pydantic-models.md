# ARCH-02 — Shared data contracts

**Status:** Draft; after pilot baseline.  
**Epic:** [EP-02](../EPIC.md)

**As a developer**, I want shared contracts in `models/pydantic/` and internal types in `models/internal/`, so that data is validated consistently without parallel schemas.

**Accept when:**
- Shared public Pydantic contracts reside in `models/pydantic/`; private types belong in `models/internal/` or remain local when not shared.
- Routers use Pydantic at HTTP boundaries and pass explicitly mapped, typed Python arguments to domain functions; domain code does not depend on FastAPI or HTTP request objects.
- JSON Schema is generated from Pydantic when required; do not maintain duplicate hand-written schemas. Preserve any separately authoritative Packs v2 external contract.
- Existing persisted Pack/Requirement/Claim/report formats, signing semantics and relevant validation tests remain unchanged.
- Assert round-trip compatibility for representative persisted Requirement, Claim, Pack and report fixtures; test invalid payload rejection, defaults, references and signing/digest behavior. Generating OpenAPI alone is insufficient.
