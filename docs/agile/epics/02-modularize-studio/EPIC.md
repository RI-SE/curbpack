# EP-02 — Migrate to the Curbpack target architecture

**Status:** Planned. No code migration is authorized by this epic alone.  
**Type:** Behavior-preserving architecture migration, not a feature epic.  
**Authority:** [CURBPACK_ARCHITECTURE.md](CURBPACK_ARCHITECTURE.md) and the normative overall architecture in `docs/arch/ARCHITECTURE.md`.

## Goal

Convert the working pilot to the agreed two-system Curbpack architecture **without losing existing behavior**. Keep changes small enough that a failing regression has an obvious cause.

The target architecture remains unchanged: **Curbpack Studio** is a modular monolith with component-owned REST routers, backend operations and thin TypeScript pages; **Curbcheck** is a standalone Python API and CLI. Studio Check is a thin REST/UI adapter to Curbcheck, not another Check engine. `docs/reference/packs2.md` is the human/PO-approved persistent contract; Pydantic implements it and JSON Schema is generated from Pydantic.

## Mandatory migration order

**One page, handler, or bounded operation at a time. Verify each change before proceeding.** The stages below are ordered; they are not authorization to batch all files in a stage into one change.

| Stage | Change | Verification gate |
| --- | --- | --- |
| **0. Baseline and inventory** | Record the current working commit, actual GET/POST routes, page-producing functions, backend calls, data effects and applicable tests in [MIGRATION_COVERAGE.md](MIGRATION_COVERAGE.md). | Capture passing tests, known failures and representative requests/pages. Unverified behavior stays OPEN. |
| **1. Extract Python pages** | Split one page/rendering function and its associated handler code out of `app/pages.py` / `app/server.py` into small Python files, **without changing the HTTP server, URL, HTML behavior or business logic**. The original dispatcher may delegate to those functions. | The page and its GET/POST actions still work, including invalid input and persistence. Run focused tests after **each** extraction. |
| **2. Move to owners** | Move the already separated modules, one at a time, into the appropriate component (`studio/pack`, `studio/claim`, `studio/review`, etc.). Keep existing server dispatch as a temporary adapter. | Same output and behavior before and after each move; imports, direct calls, CLI and page tests pass. No whole-tree `git mv`. |
| **3. Separate responsibilities** | Move business operations from handlers/pages into component `impl/`; leave the existing HTTP adapter and Python-rendered UI thin. Make Curbcheck's public Python API the only Check execution implementation and assign Compile and Review correctly. | Direct headless backend tests and unchanged old HTTP/UI flows pass after each operation. No duplicate implementation. |
| **4. Implement boundary contracts** | Introduce shared Pydantic representations according to approved Packs v2 and the already accepted VR-00/VL-00 changes. No unapproved persistent changes. | Fixture round trips, validation, serialization, digests and signatures remain correct. |
| **5. Switch HTTP incrementally** | Introduce FastAPI with a thin `studio/app.py`; place routes in component-owned `router.py`, **one tested route/flow at a time**. Use temporary compatibility only as needed for gradual replacement. Studio Check calls `curbcheck/api.py`. | Test actual FastAPI requests, success/failure/auth and persistence. Remove old route handlers only after the replacement is proven. |
| **6. Replace UI incrementally** | Convert one verified Python-rendered page/flow at a time to thin TypeScript under its owning component. The UI calls REST; it never reimplements domain behavior. | Browser interaction proves the full UI → REST → backend path and relevant error handling before deleting the old page. |
| **7. Final consolidation** | Remove remaining obsolete code, compatibility adapters and unused imports; update supported entrypoints and packaging. | Coverage complete, full regression/E2E, CLI and package smoke tests pass. Document any accepted exceptions explicitly. |

**Stop at a failed gate.** Fix the bounded change or restore it before starting another. Record actual results; never mark a stage or coverage row PASS because files moved, imports work or a page looks similar. Make a local checkpoint commit after a verified bounded change; any push, PR, release, destructive Git operation or remote change requires separate authorization.

## Stories

| ID | Responsibility in the staged migration |
| --- | --- |
| [ARCH-01](stories/ARCH-01-app-http-and-auth.md) | Preserve old HTTP while extracting handlers; then introduce thin FastAPI shell and component routers in stage 5 |
| [ARCH-02](stories/ARCH-02-shared-pydantic-models.md) | Approved shared models and compatibility verification in stage 4 |
| [ARCH-03](stories/ARCH-03-subsystem-ownership.md) | Extract Python pages, move one module, then separate backend ownership in stages 1–3 |
| [ARCH-04](stories/ARCH-04-thin-gui-pages.md) | Convert only already migrated flows to thin TypeScript in stage 6 |
| [ARCH-05](stories/ARCH-05-headless-subsystem-tests.md) | Establish baseline and verify each stage; final system regression in stage 7 |

These are **target responsibilities, not five large implementation batches**. [MIGRATION_COVERAGE.md](MIGRATION_COVERAGE.md) tracks actual migrated pages/routes/operations and their evidence. Do not create a second project-management process.

## Ownership decisions

Four questions that were open in [MIGRATION_COVERAGE.md](MIGRATION_COVERAGE.md) are decided there under "Decided ownership": Scaffold, try-discovery, authentication, and compare/consolidate apply. No new story records them. They do not block the one-handler extracts. Scaffold keeps its current stub through this epic; its later agent and repair architecture is out of scope. Authentication keeps the packages named by the target architecture and is not added by a page extract. Try-discovery belongs to `studio/claim/` Discovery, and the requirement editor only calls it. Compare and consolidate apply belong to `studio/pack/` through the shared Requirements backend, not through logic in the router or the UI.

## Dependencies and boundaries

- VR-00 and VL-00 contract work must be accepted before the stage that relies on their changed contracts; baseline, Python page extraction and isolated behavior-preserving moves need not wait solely for future feature work. Do not mix contract changes into a mechanical extraction.
- EP-11's VL-01–VL-05 are **later product features**, not incidental scope within EP-02. New EP-11 behaviors are not assumed implemented.
- EP-09 conforms to EP-02. Thin CLIs call existing Python operations; standalone GUI processes are not required.
- Source behavior from the current pilot is the regression baseline. Historical PoC behavior is separate reference material; a gap is reported, not secretly added during migration.
- Do not replace existing files, signatures, paths, exports, decisions or acceptance semantics to simplify migration.
- No generic service layer, new process topology, redundant validation schema or unnecessary refactor is implied.

## Epic acceptance

1. All active legacy pages and GET/POST actions have explicit ownership, replacements and passing verification evidence in `MIGRATION_COVERAGE.md`.
2. `studio/app.py` only starts the app, configures shared concerns and registers component routers. Every feature endpoint belongs to its component.
3. Business implementation is headless and independent of HTTP/UI. CLI and REST reuse the same functions; Studio Check calls Curbcheck's public Python API.
4. Persistent data, signatures, workspace paths, errors and user interactions retain their accepted behavior. Pydantic reflects Packs v2, not a parallel norm.
5. Every bounded migration has a passing test gate; all required rows are verified and final functional, API, browser, CLI and packaging regression suites pass. A known exception is documented and explicitly accepted, not silently reported as PASS.
6. The replaced `app/server.py` / `app/pages.py` paths and any temporary adapters are removed only once every caller and behavior is accounted for.

## Out of scope

New UX features, new data contract decisions, Release/Publish redesign, feature work from VL-01–VL-05, Discovery plugin frameworks, separate GUI applications and unrelated CI/tooling overhauls. `DISC-01` is a separate proposal and not part of EP-02.
