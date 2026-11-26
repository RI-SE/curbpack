# ARCH-01 — Thin FastAPI shell and component-owned REST routers

**Status:** Draft  
**Epic:** [EP-02](../EPIC.md)  
**Stage:** 1 (handler extraction) and 5 (HTTP migration); do not switch servers early.

**As a developer**, I want the existing HTTP behavior preserved while handlers are separated, and then migrated one route at a time to component-owned FastAPI routers, so that framework replacement does not hide functional regressions.

## Work

- During Python-page extraction, keep the current HTTP server and URLs unchanged. Extract associated handlers into callable Python functions while the existing dispatcher remains the entry point. Do not move all routes at once.
- After backend operations and Pydantic boundaries have been verified, create the thin `studio/app.py` FastAPI shell. Each component owns `studio/<component>/router.py` and routes call its backend operations with explicitly mapped typed arguments.
- `studio/check/router.py` only adapts the public `curbcheck/api.py` to HTTP. Authentication and authorization retain their own shared owners; protect direct API access, not just UI navigation.
- Preserve endpoint behavior, background-job status/abort, error handling, static/resource delivery and navigation. The new route URL may change only when explicitly mapped, with callers/tests updated.
- Old handlers can temporarily delegate, but must be removed after the new route and all callers are verified.

## Acceptance (Given / When / Then)

1. **Given** a working pilot page and POST action, **when** its handler is extracted, **then** the old server, URL, page behavior and persisted effects remain unchanged and focused tests pass.
2. **Given** an extracted backend operation, **when** its FastAPI route is implemented, **then** `studio/app.py` only registers the owning component router, and the route passes explicit typed data into the backend.
3. **Given** valid, invalid and unauthorized requests, **when** they hit the new route directly, **then** responses and side effects match the intended behavior and permission checks cannot be bypassed.
4. **Given** a route with polling, abort or resource-serving behavior, **when** it is replaced, **then** these paths remain functional and tested; moving the happy-path GET alone does not complete the route.
5. **Given** a verified replacement with no remaining old callers, **when** the old handler is removed, **then** focused and integration tests still pass; otherwise migration remains OPEN in `MIGRATION_COVERAGE.md`.

No generic central FastAPI dispatcher, no component business logic in the application shell and no FastAPI imports in `impl/`.
