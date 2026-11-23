# Curbpack — Target Architecture

**Status:** Approved architectural direction for EP-02 (2026-11-06). This document is the detailed target; `docs/arch/ARCHITECTURE.md` is the repository-wide normative entry point. This target is not a claim that the current implementation conforms. No code moves are authorized by this document alone.

## System boundary

Curbpack comprises **two systems**:

1. **Curbpack Studio** (`studio/`) — one modular-monolith application for people to manage Packs, Requirements, Claims, Discovery, Compile and Review. The application shell starts the server and registers subsystem routers. Each functional component owns its REST router, backend implementation and optional thin TypeScript pages.
2. **Curbcheck** (`curbcheck/`) — independently usable Check execution system, callable from its Python API or thin CLI and from CI without Studio. It owns Check registration, execution and Run Result creation.

**Studio Check is a deliberate adapter, not a third Check implementation:** `studio/check/router.py` and its thin UI expose Curbcheck operations by calling `curbcheck/api.py`. The Check adapter does not own Check execution or its domain rules.

The CLI of any component is **only a thin input/output adapter** calling the same backend Python functions used by REST and tests. No duplicated CLI domain implementation. KISS governs all structure.

## Architecture and contract authority

- `docs/reference/packs2.md` is the human/PO-approved normative persistent data contract. Changes to persistent shapes or meaning require an explicit contract decision.
- `docs/reference/studio-internal.md` defines Studio-internal data structures. `review_decision` is defined there.
- `models/pydantic/` implements those contracts for validation and serialization; JSON Schema is **generated from Pydantic**. Neither Python nor generated schema independently changes the norm.
- `docs/reference/workspace.md` specifies effective workspace/path configuration; it must be updated when VL-00 establishes `namespace_base` and namespace-qualified selection.
- This target and `docs/arch/ARCHITECTURE.md` own system/component boundaries; each subsystem's `ARCHITECTURE.md` owns its own functional architecture, within these boundaries.
- Approved future behavioral changes are VR-00 and VL-00–VL-05 in the revised EP-11. They are **planned changes**, not claims about today's implementation. Completed EP-01 stories remain historical. EP-09 conforms to this architecture, prioritizing CLI, with no requirement for separate GUI processes.

## Target repository structure

```text
curbpack/
├── models/
│   ├── internal/                 # Internal Python types when needed
│   └── pydantic/                 # Pack, Requirement, Claim, Run Result, Review Report
├── curbcheck/
│   ├── api.py                    # Public Python operations (no HTTP)
│   ├── cli.py                    # Thin entry point to api.py
│   ├── impl/                     # Check registry, execution and result creation
│   ├── checks/                   # Check implementations / registered CLIs
│   └── tests/
├── studio/
│   ├── app.py                    # Bootstrap, common middleware, router registration ONLY
│   ├── authentication/           # Authentication and OIDC
│   ├── authorization/            # Authorization policy / permissions
│   ├── pack/                     # Packs, Requirements and Extract
│   │   ├── router.py
│   │   ├── cli.py                 # Only if needed
│   │   ├── impl/                 # Extract, compare, editing, ownership, import/export
│   │   ├── pages/                # Thin TypeScript UI
│   │   └── tests/
│   ├── claim/                    # Claims and Discovery
│   │   ├── router.py
│   │   ├── cli.py                 # Only if needed
│   │   ├── impl/                 # Discovery, binding, editing, Claim signatures
│   │   ├── pages/
│   │   └── tests/
│   ├── check/                    # REST + UI adapter to curbcheck/api.py ONLY
│   │   ├── router.py
│   │   ├── pages/
│   │   └── tests/
│   ├── compile/                  # Assemble and render Run Result-derived reports
│   │   ├── router.py
│   │   ├── impl/
│   │   ├── pages/                # Only if needed
│   │   └── tests/
│   └── review/                   # Human review and report decision/signature
│       ├── router.py
│       ├── impl/
│       ├── pages/
│       └── tests/
├── scripts/                      # Build, CI and package scripts
├── tests/                        # Cross-system / integration / parity tests
├── docs/                         # Normative contracts, architecture and guides
├── policies/
├── AGENTS.md
├── Makefile
└── pyproject.toml
```

This is the **ownership and dependency map**, not a mandate to create empty directories or the example files verbatim. Subsystems may split `impl/` further by responsibility when warranted. No new framework, generic services layer, plugin platform, or database is implied. Existing executable Check programs can remain separate while being invoked through the Curbcheck registry.

## Responsibility contracts

| Owner | Owns | Does not own |
|---|---|---|
| `models/` | Python representation, validation, serialization, generated JSON Schema | Normative Packs v2 decisions or workflow |
`studio/app.py` | Application creation, project selection, middleware, router registration | Component business operations or component routes
| `studio/pack/` | Pack/Requirement IO, adapters, Extract, review/edit, Compare, Consolidator, ownership, signatures, ZIP exchange | Claims, Check execution, final product Review |
| `studio/claim/` | Discovery candidates, Claims editing/binding, Claim review/signing | Requirement edits, Check outcomes, final report decision |
| `curbcheck/` | Registered Checks, execution, independent CLI/API, Run Results | Human Claims binding, Compile, Review |
| `studio/check/` | REST/UI interaction with Curbcheck API | Check engine, registry duplication or Run Result evaluation logic |
| `studio/compile/` | Run Result-based report construction, validation, JSON/PDF output | Running Checks, human decision/signature |
| `studio/review/` | Read/inspect reports, decisions, review signing, historical object resolution (VL-05) | Rebuilding Run Results or implementing Compile |
| `authentication/`, `authorization/` | Identity, sessions, permissions and auth edge | Product rules hidden in the shell |

## Interface rules

1. **Component-owned HTTP:** every component owns its `router.py`. The thin application shell imports and registers routers, but never parses Pack/Claim-specific forms or executes business operations.
2. **Thin adapters:** REST routers and CLI perform interface validation, translate to typed Python arguments, call backend operations, and format results. They do not encode business rules. UI only presents and interacts through REST.
3. **Headless backend:** implementation modules can be called and tested without FastAPI, a UI, or an HTTP server. Shared domain behavior is implemented once.
4. **Independent Curbcheck:** Studio Check invokes `curbcheck/api.py`; its CLI does the same. Neither Studio nor Curbcheck creates a parallel Check engine.
5. **Persistent contracts:** Packs v2 on disk and workspace configuration are shared boundaries. Do not introduce alternative accepted Requirement or Claim payloads.
6. **Security and integrity:** `common`/shared signing and validation can be reused across components; signature verification is independent of status, Check outcomes, and release decisions. Never silently re-sign or treat a signed object as approved.
7. **No silent state mutation:** read-only compare, history inspection and Review may not change source objects; explicit approved operations own changes.
8. **CLI and packaging:** a component does not have to be a separate process to be independently callable. Standalone CLI commands from EP-09 are thin entry points on existing operations.

## Decisions from the revised EP-11

- **VR-00:** Embedded-object signatures and trusted signed Git commits are verified consistently and reported distinctly; invalid embedded signatures are not masked. Export never requires verification success.
- **VL-00:** namespace-qualified Pack/Requirement identities, origin and independent `draft`/`reviewed` status are new *contract work*, approved by the human/PO and to be reflected in `packs2.md`, Pydantic and workspace docs.
- **VL-01:** editing a foreign namespace requires explicit Take Ownership of the **whole** Pack; operation is backend-owned and preserves immediate provenance.
- **VL-02:** ZIP import/export uses the existing Pack directory shape; ZIP exchange extends EP-01 Export without requiring Publish.
- **VL-03:** form-based Compare presents old/new values; diff, preview and apply are backend operations.
- **VL-04:** Claims bind to fully qualified Requirement identity + digest; Curbcheck always runs Checks and separately reports missing/stale bindings.
- **VL-05:** Review uses a read-only backend resolver for exact historical Requirement/Claim/Check chains and Git history, without treating recovered bytes as proof of signing.

No separate Publish service, mandatory `published/` workflow, persistent update queue, or SQLite index is required by this target. Existing historical storage is not automatically removed during architecture migration.

## Runtime configuration

`curbpack-studio.json` contains Studio application configuration, not private keys or runtime database contents. User-specific runtime secrets and certificates reside outside the repository. Product `curbpack.json` and configured directory roots follow `docs/reference/workspace.md` until VL-00 changes it. Do not invent config keys in EP-02.

## Migration rule (EP-02)

`docs/agile/epics/02-modularize-studio/MIGRATION_COVERAGE.md` maps each existing route, backend operation, CLI, user interaction and relevant test to the target owner. Migrate small slices, prove observable behavior parity with tests, then remove obsolete paths. Do not reconstruct behavior from an architecture drawing or assume new EP-11 functionality already exists. EP-02 is **architecture migration, not feature development**. Any real ambiguity is returned for a human decision instead of resolved by the agent.
