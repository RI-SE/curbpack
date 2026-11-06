# ARCH-03 — Extract, move and separate one component at a time

**Status:** Draft  
**Epic:** [EP-02](../EPIC.md)  
**Stages:** 1–3. Mechanical changes precede architecture changes.

**As a developer**, I want each existing page and operation moved into its functional owner in small verified changes, so that the result has correct ownership without losing the working pilot.

## Mandatory order for each bounded page/operation

1. **Extract:** From `app/pages.py` and/or `app/server.py`, extract one Python page/render function and its handler into small Python module(s). Keep the old server, URL, generated HTML and behavior intact. Run its tests.
2. **Move:** Move those already separated files to their target component; repair imports and call sites only. Keep the old dispatcher as a temporary entry point. Run the same tests again.
3. **Separate:** Where the handler/page still contains domain behavior, extract that behavior into the owning component's `impl/` so it is callable directly. Preserve the current Python page and old HTTP path. Run direct unit tests **and** the page/HTTP regressions.
4. **Checkpoint:** Record source → destination, current callers, behavior, executed tests and any remaining gaps in `MIGRATION_COVERAGE.md`. Make a local commit of the verified bounded change; move on to the next page only then.

Do not move the whole `app/`, `requirements/`, `claims/`, `checks/` or `review/` tree first. Do not combine mechanical moves, domain rewrites, Pydantic, FastAPI and TypeScript in one step.

## Ownership

- `studio/pack/` owns Packs, Requirements, Extract, Compare, editing and export.
- `studio/claim/` owns Claims, Discovery, binding and Claim review/signing.
- `curbcheck/` owns the execution engine, registered Check CLI programs, Python API and thin CLI.
- `studio/check/` is only a GUI/REST adapter that calls `curbcheck/api.py`.
- `studio/compile/` owns JSON/PDF report assembly; `studio/review/` owns evidence inspection, human decisions and review signing.
- Reuse shared signing/validation where warranted, without adding an extra generic service layer. Preserve scripts, Make targets, package entrypoints and externally visible behavior.

## Acceptance (Given / When / Then)

1. **Given** a working old Python page, **when** it is extracted to its own file, **then** it renders and handles the same requests and errors through the old server and relevant tests pass.
2. **Given** an extracted file, **when** moved to its owning component, **then** no behavior, output or file effect changes and no unrelated files need restructuring.
3. **Given** logic embedded in a page or handler, **when** extracted to `impl/`, **then** it works directly without the UI/HTTP layer and the old UI still passes the same tests.
4. **Given** a Check run initiated from Studio, **when** component ownership is separated, **then** Studio only calls Curbcheck's public Python API; no duplicate Check engine appears.
5. **Given** a completed bounded migration, **when** coverage is reviewed, **then** the source, target, tests and remaining legacy callers are recorded. No row is marked VERIFIED just because the file moved.
