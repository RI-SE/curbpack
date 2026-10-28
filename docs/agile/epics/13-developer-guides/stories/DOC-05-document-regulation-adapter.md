# DOC-05 — Document how to add a regulation adapter

**Status:** Draft. Not authorization to implement.

**Epic:** [EP-13 Developer guides](../EPIC.md)

**Starts when:** Scheduled. Does not block the EP-01 pilot.

**As a developer**, I want one current guide for adding a regulation adapter, so that I can add a document other than the ones already present without reading the loader and guessing.

This story writes the guide and corrects the sentences that still describe adapters that the tree no longer contains. It does not add an adapter.

### Write only

- one new guide under `docs/development/`
- the adapter sections of `requirements/ARCHITECTURE.md` that disagree with `requirements/extract/adapter.py`
- `docs/development/xml-sources.md`, where a command or path would send the reader to a tree this repository does not use
- the EP-13 story table, if the guide's path is not yet named there

### Requirements (Given / When / Then)

#### DOC5-R01 — One guide says where an adapter lives and how it is listed

**Given** a clean checkout  
**When** a developer opens the guide  
**Then** it names `requirements/extract/adapters/<id>/adapter.json` as the adapter  
**And** it states that `list_adapters()` lists every `*/adapter.json` under that directory, with no separate registry  
**And** it states that a stub has `status` `stub` and refuses extraction  
**And** it states that any other status than `partial` or `stub` is refused by the loader.

#### DOC5-R02 — The guide distinguishes the two adapter shapes the loader accepts

**Given** the guide  
**When** a developer compares a text adapter with a Formex adapter  
**Then** the text shape is the one used by `requirements/extract/adapters/cra/`, where a ready section has a `fixture` file  
**And** the Formex shape is the one used by `requirements/extract/adapters/cra-xml/` and `requirements/extract/adapters/nis/`, with `source_format` `formex` and `formex_package` pointing at an existing directory  
**And** `requirements/extract/adapters/medtech/` is named as the stub, with an empty `sections` array  
**And** the guide says that splitting and atomizing a document that fits neither shape is document-specific code, not a new field in `adapter.json`.

#### DOC5-R03 — The architecture text matches the loader

**Given** `requirements/extract/adapter.py` and `requirements/ARCHITECTURE.md`  
**When** the adapter field list and the confirmed-adapter section are read after this story  
**Then** a ready Formex section is not described as requiring `sections[].fixture`  
**And** the NIS2 adapter is not described as an empty stub or as `adapter.yml`  
**And** Medtech is still described as a stub, at `requirements/extract/adapters/medtech/adapter.json`  
**And** every required-field sentence in that architecture section is true of `load_adapter`.

`requirements/ARCHITECTURE.md` §4.1.1 currently says `sections[].fixture` is required when `ready` is true. `load_adapter` requires `fixture` for a ready text section. A Formex section can be `ready` without `fixture`. The guide and the architecture section record that split. They do not keep the single rule that the Formex adapters already violate.

#### DOC5-R04 — NIST in this repository is not an adapter

**Given** the guide  
**When** a reader looks for NIST  
**Then** the guide says that `docs/ssdf/` maps NIST SP 800-218 to evidence and is not a regulation adapter  
**And** the story adds no directory under `requirements/extract/adapters/`.

#### DOC5-R05 — The older procedure does not point at another tree

**Given** `docs/development/xml-sources.md`  
**When** a developer follows it from this repository  
**Then** its commands and paths resolve in this checkout  
**And** it points at the guide for the adapter shape  
**And** it does not tell the reader to `cd poc2`.

### Definition of done

- The guide exists and is linked from EP-13.
- DOC5-R01 through DOC5-R05 hold.
- No adapter directory was added.
- Packs v2 files are unchanged.
- The story was not done by copying `requirements/ARCHITECTURE.md` §4.1.2 forward. That section still describes `adapters/nis/adapter.yml` as an empty stub.

### Out of scope

- A NIST, or any other new, adapter.
- Changing `load_adapter`, the extract stages, or the Pack Editor.
- A plugin framework or an adapter-editing screen.
- DOC-04, and any move of `docs/reference/packs2.md`.

### Stop if

Stop and record the exact conflict if:

- `load_adapter` and a current `adapter.json` disagree about a required field;
- describing both the text shape and the Formex shape would require a new `adapter.json` field;
- correcting §4.1.2 would mean choosing extraction behavior the loader does not implement.

Do not resolve that conflict by writing the guide as if the architecture paragraph were the loader.
