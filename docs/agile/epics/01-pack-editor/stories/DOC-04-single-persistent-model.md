# DOC-04 — Make Packs v2 the single persistent model contract

**Status:** Draft. Not authorization to implement.

**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md)

**Starts when:** DOC-03 is accepted.

**As a developer**, I want one authoritative human-readable Packs v2 model with machine-readable JSON Schemas, so that Studio, curbcheck, stories and tests use the same definitions of Pack, Requirement, Claim, configuration and result files.

This is a documentation and model-consolidation story. It preserves the accepted Packs v2 semantics and existing persistent files. It does not use the reorganisation to introduce unresolved versioning, workspace or Claim-review behaviour.

### Authority after this story

- `docs/models/packs2.md` is the single authoritative human-readable description of the persistent Packs v2 model, including the relationships, semantics, lifecycle invariants and persistent filesystem layout.
- `models/*.schema.json` are the authoritative machine-readable definitions of individual JSON document structures.
- JSON Schema owns fields, types, required properties and structural validation.
- `docs/models/packs2.md` owns meaning, relationships, ownership, lifecycle, signing semantics and filesystem placement.
- Architecture files describe component responsibilities and refer to the model. They do not redefine persistent document or directory structures.
- Stories and implementation plans may propose model changes, but a proposal does not change the model until this contract is explicitly updated and accepted.

### Write only

- `docs/models/packs2.md`
- `models/*.schema.json`
- `models/README.md`
- `docs/reference/packs2.md`
- references to the authoritative model in:
  - `docs/arch/ARCHITECTURE.md`
  - subsystem `ARCHITECTURE.md` files that currently redefine Packs v2 document or workspace structure
  - `docs/agile/epics/01-pack-editor/EPIC.md`
  - `docs/agile/README.md`
- tests and fixtures used only to validate the schemas and the migration

Moving `docs/reference/packs2.md` must preserve its accepted substance. The old path may remain as a short relocation notice if existing links cannot be changed atomically. It must not remain a second normative copy.

### Requirements (Given / When / Then)

#### DOC4-R01 — One human-readable model owns the whole relationship

**Given** the repository after this story  
**When** a reader opens `docs/models/packs2.md`  
**Then** that file describes the relationship:

```text
Pack → Requirement → Claim → Check result → Review report
```

**And** it identifies which artefacts belong to the Pack publisher and which belong to the product repository  
**And** it distinguishes a working copy, a published release and an imported published release  
**And** it identifies the source-edition, Requirement-payload, Pack-release and product-selection levels without treating a source URL as a version identifier  
**And** no second Markdown file claims authority over the same persistent model.

#### DOC4-R02 — The model owns the persistent filesystem layout

**Given** `docs/models/packs2.md`  
**When** a reader looks for the location of a working copy, published release, imported release, Requirement, Claim, `curbpack.json`, run result or review report  
**Then** the document names one canonical location or explicitly states that the location is deployment-configured  
**And** it distinguishes an extraction run from the Pack working copy to which proposed Requirements belong  
**And** no architecture or implementation-plan file defines a competing canonical layout.

#### DOC4-R03 — Every persistent JSON object has one schema

**Given** the persistent JSON document types named by `docs/models/packs2.md`  
**When** the files under `models/` are listed  
**Then** each document type has exactly one referenced JSON Schema  
**And** every schema declares JSON Schema Draft 2020-12  
**And** each schema has a stable `$id`  
**And** schema references resolve from a clean checkout without network access  
**And** no two schema files claim to be the schema for the same document type.

At minimum this applies to the persistent document types already defined by the accepted Packs v2 contract, including:

- Pack metadata
- Requirement
- Claim
- product configuration
- Check run result
- review report

This story does not require a schema for a proposed object that Packs v2 has not accepted.

#### DOC4-R04 — Existing accepted examples validate

**Given** each JSON example or fixture that the repository identifies as a valid Packs v2 document  
**When** it is validated with the schema referenced for its document type  
**Then** validation succeeds  
**And** the validation command exits zero.

**Given** one negative fixture per schema with a required field removed or an invalid field type  
**When** those fixtures are validated  
**Then** validation fails  
**And** the test identifies the schema and fixture that failed as expected.

#### DOC4-R05 — Schemas do not silently change Packs v2

**Given** the accepted `docs/reference/packs2.md` before this story  
**When** its fields and required/optional rules are compared with the new schemas and `docs/models/packs2.md`  
**Then** every accepted field has one documented disposition  
**And** the disposition is one of:

- represented unchanged
- wording clarified without changing accepted data
- blocked because the existing documents conflict

**And** no accepted field is removed, renamed, made required, made optional or given a new meaning without a separate explicit contract decision.

#### DOC4-R06 — Open design questions remain open

**Given** an unresolved question about:

- whether `curbpack.json` contains only Pack ids or exact source, version and digest pins
- whether several extraction runs contribute to one Pack working copy
- how a publisher revision differs from a buyer working copy
- how a human `keep` decision after a Pack update is persisted
- which Requirement changes require Claim review

**When** DOC-04 is completed  
**Then** the question is recorded as unresolved or linked to its owning decision/story  
**And** neither `docs/models/packs2.md` nor a schema presents a proposed answer as accepted behaviour  
**And** implementation is not authorised for that unresolved behaviour.

#### DOC4-R07 — Architecture refers to the model instead of restating it

**Given** `docs/arch/ARCHITECTURE.md` and the subsystem architecture files  
**When** they mention Pack, Requirement, Claim, `curbpack.json`, a Pack working copy or a published Pack layout  
**Then** they link to `docs/models/packs2.md` for persistent semantics and layout  
**And** they retain only component ownership, dependency direction and runtime responsibility  
**And** a repository search finds no second normative field list or persistent layout presented as authoritative.

#### DOC4-R08 — The old reference path cannot drift

**Given** an existing link to `docs/reference/packs2.md`  
**When** the path is opened after this story  
**Then** it either resolves to the authoritative content without maintaining a separate copy or contains only a relocation notice linking to `docs/models/packs2.md`  
**And** it contains no duplicated field, lifecycle or layout definition that can drift independently.

#### DOC4-R09 — The model-to-schema links are testable

**Given** `docs/models/packs2.md` and `models/README.md`  
**When** the model-link test runs  
**Then** every referenced local schema exists  
**And** every schema is referenced by the model or explicitly marked internal  
**And** every local Markdown link changed by this story resolves  
**And** the test exits non-zero for an absent schema, unresolved local `$ref`, duplicate schema identity or broken model link.

#### DOC4-R10 — Existing persistent bytes remain unchanged

**Given** published Packs, Requirement files, Claim files, run results and signed review reports that existed before this story  
**When** DOC-04 documentation and schemas are added  
**Then** those persistent artefacts keep their bytes  
**And** no migration rewrites signatures, digests, Pack seals or published directories  
**And** the existing pilot tests continue to pass.

### Proof

The story plan must name exact repository commands for all of the following:

1. Parse every `models/*.schema.json` file as JSON.
2. Check that every local `$ref` resolves without network access.
3. Validate every accepted positive fixture.
4. Show that every negative fixture is rejected.
5. Check links from `docs/models/packs2.md` and `models/README.md`.
6. Search the architecture and implementation documentation for competing normative model or layout definitions.
7. Run the affected existing Packs v2, Pack Editor, curbcheck and review regression tests.
8. Show that no published or signed fixture changed bytes.

Observed commands, counts and results belong in the story plan and test evidence. They are not invented in this draft.

### Definition of done

- `docs/models/packs2.md` is the one human-readable persistent-model contract.
- `models/README.md` explains the authority split between Markdown and JSON Schema.
- Every accepted persistent JSON document type has one local schema.
- Positive and negative schema tests pass.
- Architecture documentation refers to the model and does not redefine it.
- The old `docs/reference/packs2.md` path cannot become a drifting second copy.
- Existing published and signed artefacts retain their bytes.
- All unresolved semantic questions remain explicitly unresolved.
- The EP-01 story table contains DOC-04.

### Out of scope

- Deciding the new contents of `curbpack.json`.
- Adding Pack source, version or digest fields.
- Adding a Requirement version field.
- Adding a Claim-review or Claim-acceptance object.
- Redesigning extraction or working-copy behaviour.
- Moving existing workspace data.
- Implementing Pack import, export, registry access or automatic updates.
- Implementing the EP-11 multi-version lifecycle.
- Refactoring application modules under EP-02.
- Generating application classes from JSON Schema.
- Introducing Pydantic or another validation framework solely because the schemas now exist.

### Stop if

Stop and record the exact conflict if:

- the current Packs v2 document and existing accepted files disagree about whether a field is required;
- two accepted documents assign different meanings to the same field;
- a schema requires a new persistent field;
- consolidating the workspace layout requires choosing among unresolved working-copy models;
- preserving an existing valid fixture would contradict the proposed schema;
- completing the story would rewrite a published or signed artefact.

Do not resolve such a conflict by choosing whichever current file is easiest to implement. The conflict requires a separate explicit contract decision.
