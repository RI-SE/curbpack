# EP-09 — Headless CLI interfaces

**Status:** Draft; implementation after EP-02 establishes the component boundaries. Individual stories require acceptance.
**Authority:** [EP-02 target architecture](../02-modularize-studio/CURBPACK_ARCHITECTURE.md) and [system architecture](../../../arch/ARCHITECTURE.md).

## Goal

Provide useful command-line entry points to existing backend operations without starting a browser or creating independent application servers. **Curbpack has two systems:** Curbpack Studio (modular monolith) and Curbcheck (independent execution system). EP-09 does not split Studio into separate products, repositories or GUI processes.

## Design rule

A CLI parses arguments, calls its component's existing Python operations and prints results/errors with a meaningful exit code. **The CLI must not implement domain behavior.** REST routes call the same operations. Component code stays independent of the browser/HTTP layer; Studio Check is a GUI/REST adapter to `curbcheck/api.py` and is not a second Check engine. Do not create a CLI merely to satisfy the folder tree.

CLI commands and package entry-point spelling are settled against the actual post-EP-02 repository. Preserve existing public commands and flags unless a separate accepted change supersedes them.

## Stories

| ID | Deliverable | Disposition |
| --- | --- | --- |
| [TL-01](stories/TL-01-start-requirements.md) | Pack/Requirements CLI | Retargeted to `studio/pack/` backend |
| [TL-02](stories/TL-02-start-claims.md) | Claims/Discovery CLI | Retargeted to `studio/claim/` backend |
| [TL-03](stories/TL-03-start-scaffold.md) | Scaffold command if useful | No standalone GUI; preserve safe stub behavior |
| [TL-04](stories/TL-04-start-curbcheck.md) | Independent Curbcheck CLI | Retain existing command and behavior |
| [TL-05](stories/TL-05-start-compile.md) | Report compilation CLI | Reuse `studio/compile/` backend |
| [TL-06](stories/TL-06-start-review.md) | Optional headless Review commands | No standalone Review server |
| [TL-07](stories/TL-07-start-pilot-app.md) | Keep integrated Studio start/cover | No `pilot_app` product or extra process |
| [TL-08](stories/TL-08-check-module-discovery.md) | Proposed Check module discovery | Separate design change; **not authorized** by CLI scope |

## Acceptance

- A supported CLI runs without the Studio HTTP server and uses the **same backend operation** as the owning REST endpoint (or, for Curbcheck, its public Python API).
- Direct-backend and CLI tests establish equivalent outputs, errors, and persistent side effects for equivalent inputs.
- CLI import paths do not require UI pages, FastAPI request objects or the app shell; Curbcheck does not depend on Studio.
- Studio starts as **one** application with its existing navigation and journeys; no per-component GUI servers or new `pilot_app` shell.
- Existing CLI, build, Make and packaging behavior remains available unless explicitly superseded. No new Make target is assumed here.
- Signed objects and reports remain unchanged when an operation is read-only. Existing tests continue to pass.

## Scope boundary

EP-02 owns the code/HTTP/UI migration. EP-11 owns identity, ZIP exchange, Requirement binding and historical resolution. EP-09 adds CLI exposure of **implemented** operations, not copies of their domain rules. TL-08 changes Check discovery/registry semantics and requires its own explicit approval against the authoritative Packs v2 Check contract; it is not an implicit part of CLI migration.
