# EP-13 — Developer guides

**Status:** Draft. Not authorization to implement.

**Starts when:** Scheduled. Does not block EP-01. Does not wait for EP-02.

## Goal

A developer can follow one current document for an extension the code already supports. The first guide is how to add a regulation adapter. The guide describes the loader and the adapters that exist. It does not add a regulation.

## Why this epic exists

EP-01 is the pilot walkthrough. EP-04's SDD account is done and still fails if an extra path appears under `daniel/ny_sdd/`. DOC-06 updates published documents and does not add a path there. EP-03 maps NIST SP 800-218 to evidence in this repository. That NIST text is not an extraction adapter. A how-to for a new document has no home in those epics.

Further how-tos of this kind are new stories here. They are not new epics, and they are not EP-01 cards.

## Stories

| ID | User goal | Depends on |
| --- | --- | --- |
| [DOC-05](stories/DOC-05-document-regulation-adapter.md) | One current guide for adding a regulation adapter | — |

Draft stories are not permission to implement.

## Epic acceptance

- A developer can open one guide and see where an adapter lives, how it is listed, which fields the loader requires, and how a text fixture differs from a Formex package.
- The guide's examples are the adapters already under `requirements/extract/adapters/`.
- `requirements/ARCHITECTURE.md` no longer describes the current NIS2 adapter as an empty stub, and it no longer points at `adapter.yml` for the adapters that are `adapter.json`.
- No new adapter directory is added. Packs v2 files are unchanged.

## Out of scope

- Implementing an adapter for NIST or any other new document.
- A plugin registry, a UI for writing adapters, or a change to extraction behavior.
- The EP-01 pilot journeys, Publish, or DOC-04's model consolidation.
- Treating `docs/ssdf/` as the adapter guide.
