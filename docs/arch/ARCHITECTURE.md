# Curbpack — System Architecture

**Status:** Normative architectural direction for migration under EP-02 (2026-11-06). This describes the **target**, not a claim that the repository has already been migrated. Historical PoC2 layout and behavior remain implementation evidence, not current architectural authority.

## Architecture authority

Curbpack consists of **two systems**: Curbpack Studio, a modular monolith, and Curbcheck, an independently callable execution system. The full target directory map and ownership rules are in [`../agile/epics/02-modularize-studio/CURBPACK_ARCHITECTURE.md`](../agile/epics/02-modularize-studio/CURBPACK_ARCHITECTURE.md). This document and that detailed target describe **one** architecture; do not maintain competing targets.

- `docs/reference/packs2.md` defines the **human/PO-approved normative persistent data contract**. Nothing here overrides it.
- `docs/reference/studio-internal.md` defines Studio-internal data structures. `review_item` is defined there.
- `models/pydantic/` implements that contract; **generate** JSON Schema from Pydantic. When they disagree, resolve against Packs v2 through an explicit change decision.
- `docs/reference/workspace.md` defines current configuration/path behavior; new VL-00 namespace fields require an explicit update there.
- The subsystem `ARCHITECTURE.md` files define functional boundaries within this overall target; obsolete routing, import and Publish claims in those files do not override it.
- `docs/agile/DECISIONS.md` records accepted decisions; EP-11 VR-00/VL-00–VL-05 define approved *future work*. These features are not implied to be already implemented.

## System and component ownership

| Area | Target owner | Boundary |
|---|---|---|
| Studio bootstrap/auth | `studio/app.py` plus auth components | Startup, common infrastructure, authentication and router registration only; no feature logic |
| Packs/Requirements | `studio/pack/` | Extract/adapters, edit, Compare, Consolidator, signs, ownership and ZIP exchange |
| Claims/Discovery | `studio/claim/` | Candidate search/assessment, binding, Claims Editor, Claim review/signing |
| Studio Check | `studio/check/` | Thin HTTP and GUI adapter to `curbcheck/api.py`; **exception** to normal feature implementation ownership |
| Curbcheck | `curbcheck/` | Independent Python API, CLI, registry, Check execution, Run Result creation |
| Compile | `studio/compile/` | Assemble Run Result-derived review reports, JSON/PDF rendering |
| Review | `studio/review/` | Human decision, signature, inspect evidence, historical read-only resolution |
| Shared models | `models/` | Pydantic validation/serialization, generated schemas and internal types |

**Every Studio functional component owns its REST `router.py`, implementation modules, and optional thin TypeScript pages.** `studio/app.py` registers those routers and does not dispatch feature requests or implement their workflows. The `studio/check/` adapter is deliberately thin because Curbcheck owns its own engine; it is not an alternative Check implementation.

**Backend logic is callable headlessly.** The CLI and REST are thin adapters to the **same** Python operations, not independent implementations. No UI business logic; no added service layers for their own sake. Curbcheck can be run directly in shell/CI without Studio.

## End-to-end responsibility

```text
External source / Pack ZIP
       |
       v
Studio Pack: Extract / Import -> Compare / Edit -> Sign / Export
       |
       v
Pack and Requirement (Packs v2; workspace files)
       |
       v
Studio Claim: Discovery -> human binding -> Claim review/sign
       |
       v
Curbcheck Python API / CLI -> registered Checks -> Run Result
       |                  ^
       |          Studio Check REST/UI adapter
       v
Studio Compile -> Review report (JSON / PDF)
       |
       v
Studio Review -> Retire with a reason / record decision / sign
       |
       v
Claim files change only when that signed report chose removal
```

This is a responsibility diagram, not a forced chronological workflow. Not every action is needed for every run. Extraction and Discovery suggestions are not verified compliance evidence. Check results are technical facts; review and organizational release decisions remain distinct. Signing does not imply approval or conformity.

## Invariants

1. **Packs v2 files are the system of record.** Workspace configuration defines selection and file locations. Git provides history and possibly a verifiable seal, not a parallel source of domain objects.
2. **Identity and provenance:** the revised EP-11 introduces qualified identities, declared `origin`, ownership transfer, and independently declared status. The persistent contract and migrations belong to VL-00/VL-01, not an unrequested EP-02 refactor.
3. **Signatures:** VR-00 makes embedded and trusted signed-Git evidence consistently reportable; invalid/unsigned is not a release gate. Do not treat one valid mechanism as erasing a known invalid embedded signature.
4. **Claim binding:** VL-04 adds the exact Requirement identity/digest and separate stale/missing reporting without suppressing Check execution. VL-05 makes exact historical chains inspectable in Review.
5. **Write ownership:** only explicit editor/ownership/import operations mutate their own files. Compare, Discovery candidate retrieval, and Check history inspection do not edit them. Review does not edit a Claim until a signed report has `remove_retired_checks` true, and then only the Checks that report named.
6. **Compile vs Review:** Compile creates and renders reports from recorded results; Review owns decisions/signatures. Neither runs Checks. A new run never deletes an existing saved report. Signing does not rewrite the Check result stored in the report.
7. **Compatibility:** EP-02 must preserve existing accepted observable behavior, APIs and CLI workflows or document an explicitly accepted change. Every migration slice has regression tests.
8. **No implied complexity:** no mandatory Publish lifecycle, separate Studio GUIs, duplicate CLI backends, SQL version store, generic plugin platform, or empty architectural layers.

## Current implementation vs target

The repository currently contains legacy paths such as `app/server.py`, `app/pages.py`, `requirements/`, `claims/`, `checks/`, `review/compile.py` and `compile/pdf.py`. These are **sources for migration**, not destination rules. Some old architecture files describe central HTTP dispatch, Python HTML pages and publisher-specific release procedures: those are not the target.

The target path and owner for each existing operation must be recorded and checked in `docs/agile/epics/02-modularize-studio/MIGRATION_COVERAGE.md`. Migrating a capability means preserving its observable behavior and tests, not moving filenames blindly. Do not add VL-01–VL-05 features during a behavior-preserving EP-02 move.

## References

- [Detailed approved architectural target](../agile/epics/02-modularize-studio/CURBPACK_ARCHITECTURE.md)
- [Normative Packs v2](../reference/packs2.md)
- [Studio-internal structures](../reference/studio-internal.md)
- [Current workspace config contract](../reference/workspace.md)
- [Agreed decisions](../agile/DECISIONS.md)
- [EP-02 migration](../agile/epics/02-modularize-studio/EPIC.md)
- [Revised EP-11 scope](../agile/epics/11-pack-version-lifecycle/EPIC.md)
- `requirements/ARCHITECTURE.md`, `claims/ARCHITECTURE.md`, `checks/ARCHITECTURE.md`, `compile/ARCHITECTURE.md`, `review/ARCHITECTURE.md` — subsystem functional architecture
