# ARCH-03 — Move code to its functional owner

**Status:** Draft; after pilot baseline.  
**Epic:** [EP-02](../EPIC.md)

**As a developer**, I want each feature's routes, implementation and optional CLI/UI in its owner directory, so that changes remain local and understandable.

**Accept when:**
- Match the repository tree and responsibility table in [CURBPACK_ARCHITECTURE.md](../CURBPACK_ARCHITECTURE.md): `studio/pack/`, `studio/claim/`, `studio/review/`, `studio/check/`, `studio/compile/`, and independent `curbcheck/`.
- Requirements, extraction and Pack Editor belong to `studio/pack/`; Claims and Discovery to `studio/claim/`; human review to `studio/review/`.
- `curbcheck/api.py` and `curbcheck/cli.py` reuse its `impl/` and `checks/`. `studio/check/router.py` is only the REST adapter to that Python API; there is no Curbcheck HTTP router or duplicated Check engine.
- `studio/compile/` owns report assembly/export (including functionality previously dispersed between root `compile/` and `review/compile.py`). Review does not own report generation.
- Domain code lives in functional modules under `impl/`, not one giant file. Avoid empty scaffolding and unnecessary layers; CLI and REST call the same logic where relevant.
- Prefer mechanical `git mv` and necessary import/path/entrypoint repairs first, then move responsibilities in bounded tested slices. Preserve runtime behavior, data and tests throughout.
- Account for the existing code and tests under `app/`, `requirements/`, `claims/`, `discovery/`, `checks/`, `compile/`, `review/`, `common/`, and callers in `scripts/`, `Makefile`, native package/CLI entrypoints. Update the rows in `MIGRATION_COVERAGE.md`; no capability is considered migrated just because its directory moved.
