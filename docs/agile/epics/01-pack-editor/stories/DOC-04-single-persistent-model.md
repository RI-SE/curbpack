# DOC-04 — One authoritative Packs v2 contract and generated schemas

**Status:** Draft. Not authorization to implement; coordinate execution with accepted VR-00/VL-00 and EP-02 model migration.
**Epic:** [EP-01](../EPIC.md). Coordinate with [VL-00](../../11-pack-version-lifecycle/stories/VL-00-Introduce-namespaces.md) and [ARCH-02](../../02-modularize-studio/stories/ARCH-02-shared-pydantic-models.md).

**As a developer**, I want one normative persistent-data specification and testable Python/schema implementations, so that Curbpack Studio and Curbcheck agree on the accepted Packs v2 documents.

## Authority (decided)

`docs/reference/packs2.md` is the **human/PO-approved normative specification** for persistent data. It stays at that path; do not relocate it to `docs/models/packs2.md` or make a second normative copy.

`models/pydantic/` implements the accepted contract for validation/serialization. **Generate JSON Schema from Pydantic** where needed; JSON Schema and Pydantic do not independently determine normative fields or meaning. If there is a discrepancy, report it and seek a Packs v2 contract decision rather than silently changing the specification. `docs/reference/workspace.md` defines workspace configuration and is updated for VL-00 namespace behavior when VL-00 is accepted.

## Acceptance — Given / When / Then

### DOC4-R01 — One normative source

**Given** all persistent model documentation **when** architecture, stories, README and schema docs are inspected **then** `docs/reference/packs2.md` is the one stated authority for Packs v2 data semantics and no `docs/models/packs2.md` or generated schema claims competing authority.

### DOC4-R02 — Pydantic implementation

**Given** a valid accepted Pack, Requirement, Claim, Run Result or Review Report fixture **when** the corresponding Pydantic model validates and serializes it **then** it round-trips without changing accepted fields or signatures; rejected fixtures produce explicit validation failures.

### DOC4-R03 — Generated JSON Schema

**Given** the Pydantic models **when** schemas are generated **then** their local references resolve, supported positive/negative fixtures behave as expected and regeneration produces no unexplained drift from the checked-in generated output (if committed).

### DOC4-R04 — Explicit contract change

**Given** a mismatch between Packs v2 and a generated/model representation **when** it is reviewed **then** the exact mismatch is recorded for human/PO resolution; neither source data nor the normative spec is silently rewritten to make tests pass.

### DOC4-R05 — Data safety

**Given** existing signed objects and published/exported Pack files **when** the model and generated-schema work runs **then** their bytes, digests and signatures stay unchanged, except for separately approved contract migrations such as VL-00 with explicit fixtures/tests.

### DOC4-R06 — No duplicate system of record

**Given** Studio and Curbcheck use the persistent contracts **when** they read and validate supported documents **then** they use the same model meaning and no alternative database, legacy schema or UI-local domain model becomes authoritative.

## Implementation scope

Align reference links, model implementation, generated schemas and tests with the approved Packs v2 contract. EP-02 owns movement of Python packages and HTTP/UI routing; VL-00 owns new namespace/origin/status fields and its explicit fixture migration. Do not implement VL-01–VL-05, change runtime workflows or move workspace files under this story.
