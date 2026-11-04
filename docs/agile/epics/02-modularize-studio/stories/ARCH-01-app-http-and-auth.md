# ARCH-01 — Thin app shell and subsystem REST routers

**Status:** Draft; after pilot baseline.  
**Epic:** [EP-02](../EPIC.md)

**As a developer**, I want `studio/app.py` to bootstrap FastAPI and register routers owned by their functional areas, so that app startup is independent of domain operations.

**Accept when:**
- `studio/app.py` owns startup, shared configuration/middleware and router registration only; it contains no Pack, Claim, Check, Compile or Review endpoints/business logic.
- Each HTTP endpoint lives in its owner's `studio/<area>/router.py`; the pilot's old server dispatch is removed only as each route is replaced and verified.
- `studio/authentication/` owns identity/OIDC, `studio/authorization/` owns permission checks; protected endpoints enforce authorization on direct API requests as well as UI use.
- Routers validate public Pydantic inputs/outputs, explicitly map to typed Python arguments and delegate to implementation without duplicating business rules.
- Existing applicable HTTP behavior and access checks are covered by regression tests; no framework types leak into `impl/`.
- Inventory each existing GET/POST action in `app/server.py` using `MIGRATION_COVERAGE.md`: migrate or explicitly account for every live route, including background-job polling/abort, errors, resource serving and navigation. Verify successful, invalid and unauthorized **direct API** requests before removing the old handler.
