# EP-11 — Pack version lifecycle and exchange

**Status:** Draft. Not authorization to implement. Keeps focus on the EP-01 pilot by parking multi-version work here.

**Goal:** Give Studio a deliberate grip on **versions** when upstream legal text and published Packs move: detect updates, apply differences selectively, release immutably, exchange Packs as files, import a received release, and rebind Claims when the Requirement set changes. Optional SQLite is an **index** over the same on-disk Packs v2 trees — never a second system of record.

## Why this epic exists

Curbpack Studio’s long-term job is to help people **relate to changing versions** (source → Requirement payload → Pack release → Claim), not to invent a new compliance verdict. Continuous upstream updates make that hard. A SQL database of every version is one possible *query* aid; it is not required to store truth. Packs v2 already stores releases as immutable directories.

## Pilot boundary (EP-01) — agreed simplification

**While finishing the pilot, the product may assume the operator works on the latest selected Pack release / working copy only.**

| Pilot (now) | This epic (later) |
| --- | --- |
| One active working copy / one `pack.version` in focus | Several published versions and working copies side by side |
| Compare/re-extract against that copy (PE-08) | “Has update” marks, update-all / one-by-one against tracked upstream |
| Publish creates `published/<id>/<version>/` (PE-11) | Release readiness when the edited set is “latest”; export/import exchange |
| Claims bind `requirement_id` against the Pack tree in use | Explicit unbound/rebind when a new release is taken in |
| No pack-exchange zip contract | Zip = Packs v2 tree; import into pack list |
| No SQLite | Optional rebuildable index (VL-08) |

Immutable `published/<pack-id>/<version>/` may already exist on disk during the pilot. The pilot UI does **not** have to offer simultaneous editing of two versions. That is the simplification: **storage can keep history; the pilot workflow only needs latest.**

## User journey (target after this epic)

```text
URL (source has an update)
  → Extract (persist only differences ≠)
  → Pack view: Requirements; some marked "has update"
       → update all  OR  one at a time
  → when the chosen set is ready / "latest"
       → Release → published/<id>/<version>/ (sealed; no overwrite)
       → optional export: pack-exchange zip
  → another team imports the zip into their pack list ("bought" update)
  → Claims: show unbound / require rebind where Requirement payloads moved
```

## Storage stance (normative for this epic)

1. **System of record:** Packs v2 files on disk. Pack release identity is `pack.id` + `pack.version` under `published/<id>/<version>/` (and dated working copies as today). Requirement “version” remains the **payload digest**, not a new filename scheme.
2. **Do not** encode Requirement digests or semver into Requirement **filenames** (`CRA-…-v3.json`). That couples identity to path harder than a DB would.
3. **SQLite (VL-08):** optional cache for “list versions”, “latest”, “has update”. Deleting the DB and rebuilding from disk must restore the same answers. The DB must not become the only place a release exists.

## Stories

| ID | User goal | Depends on |
| --- | --- | --- |
| [VL-01](stories/VL-01-vocabulary-and-layout.md) | Shared vocabulary: release vs digest vs working copy vs git | — |
| [VL-02](stories/VL-02-extract-differences-only.md) | Re-extract from URL; persist only ≠ rows | VL-01, PE-08 |
| [VL-03](stories/VL-03-has-update-pack-view.md) | Pack view marks Requirements with available updates; all or one | VL-02 |
| [VL-04](stories/VL-04-release-when-ready.md) | Release the ready set as an immutable published version | VL-01, PE-11 |
| [VL-05](stories/VL-05-pack-exchange-format.md) | Define pack-exchange zip = Packs v2 tree | VL-04 |
| [VL-06](stories/VL-06-import-exchange.md) | Import exchange into pack list without mutating old releases | VL-05 |
| [VL-07](stories/VL-07-claims-after-pack-update.md) | After taking in a new release, Claims unbound/rebind is visible | VL-06, Claims |
| [VL-08](stories/VL-08-sqlite-index.md) | Optional SQLite index over disk; rebuildable | VL-01–VL-07 as needed |

Story details: [`stories/`](stories/). Format matches the newer stories (pedagogical example + Given/When/Then). Draft stories are **not** permission to implement.

## Epic acceptance (when all VL stories are done)

- An operator can detect an upstream source change, apply only differing Requirements (all or one-by-one), and publish a new `pack.version` without overwriting a previous published directory.
- A sealed Pack directory can be exported as a pack-exchange zip and imported elsewhere into the pack list; previous published versions on disk remain unchanged.
- Taking in a new release surfaces Claim impact (unbound / needs review); nothing silently rewrites Claim→Requirement binding.
- If SQLite is present, wiping it and re-indexing from disk yields the same version/latest/has-update answers.
- Packs v2 field contracts are unchanged unless a separate, explicit contract decision is recorded. No Requirement version-in-filename scheme.

## Out of scope

- Blocking or rewriting the EP-01 pilot to require multi-version UI.
- SQL (or SQLite) as system of record.
- Pack inheritance / `extends` / automatic merge of two Pack ids.
- Turning Review into a conformity or CE decision.
- Replacing Git; Git remains file history, not the Packs v2 version graph.

## Relation to other epics

- **EP-01** finishes the pilot on the latest-only simplification above.
- **PE-08 / PE-11** remain the pilot extract-compare and publish stories; VL stories extend them after the pilot is acceptable.
- **EP-09** tool split is independent; exchange/import must keep working through `common/` Packs v2 IO.
- Open Git/workspace mapping stays in [`docs/agile/DECISIONS.md`](../../DECISIONS.md); this epic must not silently decide it.
