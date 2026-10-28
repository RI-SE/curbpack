# EP-02 - Modularize Curbpack Studio

**Status:** Planned, not approved for implementation until the pilot baseline is verified.
**Type:** Technical epic.
**Priority:** After the working pilot is completed and frozen as a tested baseline.

## Goal

Make the existing Studio application easier to maintain and test, and allow future GUIs or clients to reuse the same functionality without rewriting it.

**As a developer**, I want to keep HTTP/presentation code separate from shared contracts and subsystem behavior, so that we can change the GUI or deployment arrangement without changing what Requirements, Discovery, Claims, Checks, Compile, and Review do.

## Scope

- Keep FastAPI routing, authentication/authorization, HTTP handling and GUI integration in `app/`.
- Split GUI pages into understandable files under `app/pages/`; keep browser-side code limited to presentation and interaction.
- Put Pydantic models shared by the app and subsystems in `models/`; do not invent a parallel schema to Packs v2.
- Keep each subsystem's business rules, operations, validation and persistence owned by that subsystem.
- Ensure subsystem functions can run and be tested without importing the GUI or starting FastAPI.

The existing PoC2 pilot is the functional and regression baseline. Refactoring should change structure, not observable product behavior.

## Stories

| ID | Story |
| --- | --- |
| [ARCH-01](stories/ARCH-01-app-http-and-auth.md) | Keep HTTP routing and access checks in `app/` |
| [ARCH-02](stories/ARCH-02-shared-pydantic-models.md) | Share Pydantic contracts in `models/` |
| [ARCH-03](stories/ARCH-03-subsystem-ownership.md) | Give each subsystem ownership of its functionality |
| [ARCH-04](stories/ARCH-04-thin-gui-pages.md) | Keep GUI pages thin and separate |
| [ARCH-05](stories/ARCH-05-headless-subsystem-tests.md) | Run and test subsystem functions without the GUI |

## Epic acceptance

1. Existing pilot user journeys continue to behave as before; affected regression tests and agreed manual acceptance scenarios pass.
2. Neither Packs v2 nor published/signed artifacts are changed by this refactoring.
3. No domain behavior is duplicated between browser JavaScript, page handlers and subsystem Python code.
4. GUI code does not directly implement persistence, extraction, signing, checking, or review business rules.
5. Subsystem functions can be called and tested without a running web server.
6. Each migration step is small enough to review and verify; findings and outstanding failures are reported, not hidden.

## Not part of EP-02

- The development container ([EP-12](../12-development-environment/EPIC.md)), a central database, a multiuser service, or a new GUI.
- New business features, UX redesign, Packs v2 changes or a new API version merely for architectural purity.
- Generic plugin frameworks, service abstractions, or additional layers without an existing need.
- Unrelated cleanup before the tested pilot baseline is established.

These are possible future uses of the modular design, not acceptance criteria for this epic.

## Before implementation

1. Freeze a fresh, tested PoC2 pilot baseline and record known failures.
2. Inspect the actual code and existing architecture/contracts; choose a sequence of small moves.
3. Derive testable requirements in `docs/req/` and map them to existing and new regression tests.
4. Do not start moving code simply because this epic exists.
