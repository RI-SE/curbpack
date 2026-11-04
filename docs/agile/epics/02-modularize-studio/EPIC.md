# EP-02 — Migrate to the Curbpack target architecture

**Status:** Planned; implementation starts after the pilot baseline is recorded.
**Type:** Architecture migration, not a feature epic.
**Authority:** [CURBPACK_ARCHITECTURE.md](CURBPACK_ARCHITECTURE.md).

## Goal

Move the existing pilot into the agreed Curbpack structure **without losing working behavior**. The pilot intentionally retained its old HTTP server; that was acceptable for the pilot, **not the target architecture**.

## Target

- `models/`: shared public Pydantic contracts and internal types; generate JSON Schema when needed. Packs v2 remains authoritative.
- `curbcheck/`: independent Python API, CLI and Check implementation; **no Curbcheck REST router**.
- `studio/app.py`: thin FastAPI application shell and router registration.
- `studio/authentication/` and `studio/authorization/`: identity and access control.
- `studio/pack/`: Packs, Requirements, extraction and Pack Editor.
- `studio/claim/`: Claims, Discovery and Claim Editor.
- `studio/check/`: REST adapter calling `curbcheck/api.py`, plus thin UI; **no duplicate Check engine**.
- `studio/compile/`: report compilation and exports; separate from Check and Review.
- `studio/review/`: human review of results, evidence and decisions.

Each Studio functional area owns `router.py`, functionally divided `impl/` and `pages/` where required. Routers own HTTP/Pydantic and map to **explicit typed Python arguments**. `impl/` does not import FastAPI. Thin TypeScript pages perform business operations only via REST. CLI entry points, where needed, reuse the same implementation.

The target directory tree and ownership table in `CURBPACK_ARCHITECTURE.md` are normative. File names under `impl/` are examples, not a checklist for empty modules. **KISS applies to migration as well as code.**

## Stories

| ID | Deliverable |
| --- | --- |
| [ARCH-01](stories/ARCH-01-app-http-and-auth.md) | Thin app shell, subsystem-owned REST routers, identity and access control |
| [ARCH-02](stories/ARCH-02-shared-pydantic-models.md) | Shared contracts without duplicated schemas |
| [ARCH-03](stories/ARCH-03-subsystem-ownership.md) | Move ownership and implementation to target directories, including Curbcheck and Compile |
| [ARCH-04](stories/ARCH-04-thin-gui-pages.md) | Thin subsystem-owned TypeScript pages calling REST |
| [ARCH-05](stories/ARCH-05-headless-subsystem-tests.md) | Functional and regression evidence before and after migration |

## Migration constraints

1. Record a working pilot commit and its known failures **before changes**. Compare existing user journeys, including PoC-only functionality that may have been lost in the pilot; do not silently accept that loss as a desired design change.
2. Prefer straightforward `git mv` and import/path repairs before changing internal behavior. A move does **not** by itself satisfy the new architecture.
3. Migrate one bounded feature or call path at a time. Leave unrelated pilot functionality running until its replacement is verified.
4. Preserve Packs v2, signed artifacts, external formats and observable behavior unless a separate requirement explicitly authorizes a change.
5. No new framework, intermediary service, duplicated domain logic, or process machinery merely to accomplish the migration.
6. Failed tests and unverified behavior must be reported; do not claim parity without evidence.

## Baseline and coverage

[MIGRATION_COVERAGE.md](MIGRATION_COVERAGE.md) enumerates the pilot source areas, legacy HTTP paths, test candidates and observable behaviors. This is a **required completion checklist**, not a new planning workflow. No story can be accepted solely on directory layout, import success or generic test claims. PoC parity needs the actual PoC snapshot; unresolved gaps remain OPEN, not PASS.

## Epic acceptance

- The agreed repository ownership and call paths are in place: `TypeScript page → studio/<area>/router.py → studio/<area>/impl/`; for checks, `studio/check/router.py → curbcheck/api.py → curbcheck/impl/`.
- `studio/app.py` owns only startup, shared application concerns and router registration, **not subsystem endpoints or domain operations**.
- HTTP/Pydantic models remain at the public boundary; implementations take explicit typed Python arguments and run without FastAPI or browser dependencies.
- Curbcheck remains independently usable from Python and CLI, with no separate HTTP server/router.
- Compile owns report generation; Check executes checks; Review handles human review. None silently absorbs another's responsibility.
- Every row in `MIGRATION_COVERAGE.md` is verified against the migrated code with real test evidence, or remains OPEN; EP-02 is not DONE while required rows are OPEN. Full pilot journeys and CLI/build regressions pass. PoC parity is separately checked when a PoC baseline is available; otherwise it is explicitly unverified.

## Outside scope

New features, UX redesign, data-contract changes, unrelated refactors, CI overhauls, plugin frameworks, and additional architectural layers. Discovery provider extensibility (`DISC-01`) is a separate proposed feature, **not part of EP-02**.
