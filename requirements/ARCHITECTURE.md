# Requirements architecture

Status: **target subsystem contract, ready for iterative review; not a claim that current PoC2 code conforms**. This is the **only** `ARCHITECTURE.md` for the Requirements subsystem, including Extract. The separate `poc2/extract/ARCHITECTURE.md` has been removed and is not a second contract. The governing overall boundary is `doc/ARCHITECTURE.md`; the persistent contract reference is `docs/reference/packs2.md` in Studio. PoC1 is a *functional and UX reference*, never a schema authority.

## 1. Scope and invariants

Requirements owns regulation adapters and extraction, import of a published Pack, dated Pack working copies, Requirements review/edit, Compare, Consolidator, local acceptance, and publishing immutable Pack versions. It does not discover product evidence, create Claims, run Checks, compile run reports, or perform final product review. Git history of the workspace is repository history, not a second Requirements workflow.

- A **Pack** is the unit of work. An extraction is a new working copy of that Pack, not an overwrite of an existing one.
- Every saved Requirement draft uses the **Packs v2 Requirement JSON shape**, without `signed`. There is no second accepted interpretation object, `ClaimDraft`, approval schema, or `decisions.json` in the target workflow.
- The regulation-specific parser/atomizer is deterministic at runtime. Developers use a coding agent to develop adapters and inspect readable JSON next to source law text. Product UI does **not** configure cuts or offer a segmentation editor.
- LLM interpretation and discovery-hint proposals are nondeterministic and separate from deterministic parsing. A completed extraction preserves its results in its own directory.
- Editing, Compare transfers, and Consolidator modifications apply only to the explicitly selected writable working copy. No read-only comparison and no new Extract may mutate other working copies or a published Pack.
- If a payload is changed, drop `signed` on the changed object. A no-op edit must not drop it. `signed` and directory seals use the existing Packs v2 semantics; a signature does not confer organizational authority. The employee identity and the Git author string are not a signature.
- Import copies a published Pack unchanged into `published/<pack-id>/<version>/`. It does not set `origin`. That directory is not a working copy.
- A local working copy of a published Pack is a new timestamped directory. `working_copy` sets `origin`. The published source stays unchanged. `approve_working_copy` signs that copy and keeps `origin`. That acceptance does not publish a release.
- Publisher publication applies to Requirements with no `origin`. It writes a new `published/<pack-id>/<version>/`. It does not remove `origin` or present a local copy as the source publisher's release. An organisation publishing under its own separate pack identity is outside this contract.
- One Requirements subsystem specification. Component implementation can be split into directories, but component architecture documents are not created.
- `app/` owns HTTP routing and navigation; Requirements owns ordinary Python operations and its own HTML rendering. CLI/tests must call operations without HTTP or UI.

## 2. Working-copy lifecycle and storage

`Pack id` groups independently selectable working copies. Every *new Extract invocation* creates a **new, collision-free UTC timestamped directory**. Reopening, editing, comparing, or signing within an existing selected working copy does not create a new Extract directory. The same timestamped layout is the working-copy identity for a local copy of a published Pack. The timestamp is not `pack.version`, `origin.version`, or a Requirement version.

The workspace root is deploy-time configuration, not a Packs v2 domain field. Authentication, the organisation/employee relationship, and provisioning of the organisation's Git repository are outside Requirements and outside PoC2. When the deployment supplies that repository, it is the workspace root: the same directories live there, and that repository's Git history is how those directories are committed, diffed, and restored. Restoring a revision recovers the Packs v2 files at that revision. It does not change selection by pack id and timestamp, and it does not assign `pack.version`, `origin`, or a signature. A signed Git commit remains the Packs v2 seal reading when `signed` is absent. Until that repository is supplied, the configured workspace root remains, and Requirements does not add a history of its own.

Illustrative (exact configured root and corpus naming are deployment details):

```text
internal-data/
  cra-baseline/
    2026-10-13T090000Z/
      pack.json
      REQ-A.json
      REQ-B.json
    2026-10-13T143000Z/
      pack.json
      REQ-A.json
  published/
    cra-baseline/
      1.0.0/
        pack.json
        REQ-A.json
      1.1.0/
        pack.json
        REQ-A.json
```

A working-copy directory represents one editable Pack snapshot. `pack.json` carries its Pack metadata using the existing Packs v2 fields; timestamp is **not** `pack.version`, `origin.version`, or a Requirement version. Temporary section/provision JSON, model-call diagnostics, job logs and comparison previews reside in a non-published work/diagnostics area associated with that extraction, **never inside the directory that will be sealed**. Publisher publication copies only the validated Pack files to a newly created release directory. The exact location/linkage of non-pack diagnostics must be selected in implementation without introducing a new persistent domain schema.

Required operations (ordinary Python callables; these names are descriptive contracts, not already-implemented claims):

| Operation | Input | Result / invariant |
| --- | --- | --- |
| `list_working_copies` | Pack id | Ordered available dated copies; latest selection is explicit and deterministic. |
| `create_extraction_copy` | Pack id, corpus/adapter, run settings | Uniquely allocated *new* directory of unsigned Requirements with no `origin`; fails rather than overwrites on collision. |
| Import published Pack | Source published directory for one pack id and version | Unchanged files at `published/<pack-id>/<version>/` after the existing published-pack validation and signature reading pass. Identical bytes already stored remain. Different bytes at that identity are refused. No `origin`. The source is unchanged. Failure leaves no new directory. The result is not a working copy. |
| Local working copy | A published Pack already in this workspace | A new timestamped directory. `working_copy` sets `origin` to that pack id and version on each included Requirement. The copy is unsigned. The published directory is unchanged. |
| `select_working_copy` | Pack id, timestamp | Valid existing location; reject missing or wrong-Pack location. No file mutation. Selecting a published directory, including an import, does not make it writable. |
| `load_working_copy` | Selected directory | Validated `pack.json` and Requirements, with clear errors for corrupt/missing files. |
| `publish_pack` | Selected working copy whose Requirements have no `origin`, explicit `pack.version`, signing inputs | A new immutable published Pack directory. Refuse an existing destination, invalid objects, and a Requirement that still has `origin`. Do not partially publish. |

A new Extract may fail midway; it leaves an identifiable incomplete run for inspection, and that run is not a publishable Pack. Do not expose a failed or partial run as ready. Validation and signing precede writing a new published directory; stage output must never appear half-published. Keep the source working copy after publishing. The Packs v2 files in the selected directory are the Requirement data. When the workspace root is the organisation repository, Git history restores an earlier revision of those files and is not a second copy of their fields.

**Terminology distinction:** the timestamp identifies the working-copy directory for both an Extract output and a local copy of a published Pack. Packs v2 `origin` is set only by `working_copy` / `accept_published_version` when a published version is taken in. Extract does not set it. Import does not set it. A timestamp does not set it.

## 3. Components and responsibility boundaries

| Component | Owns | Does not own |
| --- | --- | --- |
| Extract | Adapters; stages 00–04; model proposals; validation; new working-copy output and run diagnostics | Editing old copies, decisions replay, publication, Claim discovery |
| Catalog / workspace selection | Pack and dated-copy selection; import of a published Pack; creating a local working copy from a published Pack; reading statuses; launching Extract jobs | Deterministic parser internals or domain validation |
| Requirements Editor | Read/modify saved Requirements and associated Pack metadata; form-to-operation mapping | Adapter corrections or Claims |
| Compare | Read-only diffs across copies or published Packs; explicit selected-field/whole-Requirement copy to selected destination | Automatic reconciliation or source mutation |
| Consolidator | Recommend overlaps; show evidence and proposed merged Requirement; human-confirmed merge of drafts | Parser segmentation or silent deletion of signed/published objects |
| Publication | Seal Requirements; validate and publish a versioned Pack | Running Extract or editing published releases |
| Requirements UI | Thin pages, forms, job log, interaction feedback | Filesystem traversal, cryptographic checks, validation policy, business decisions |

`common/` remains owner of shared Packs v2 validation, canonical digests, signing and IO primitives.

## 4. Extract: deterministic preparation and LLM proposals

Stages 00–01 parse controlled legal source into **disposable** sections and provisions. Stages 02 and 03 propose Requirement interpretation and discovery hints; stage 04 assembles **unsigned Packs v2 Requirements**, validates, and writes them as the new dated working copy's Requirements. Stage 04 is *not* an acceptance gate requiring `decisions.json`, nor is there a later `accept_assembled` transfer to overwrite an earlier copy. Never run a model in stages 00–01 or 04. Stages remain callable independently for development and tests, but the product's full Extract command produces a new dated working copy.

| Stage | Input | Output | Properties |
| --- | --- | --- | --- |
| 00 Structure | Controlled source and adapter | Section list / optional split text | Deterministic, adapter-specific |
| 01 Atomize | Selected, ready section | Provision list with `locus`, `law_text` | Deterministic, no editor for cuts |
| 02 Interpret | Provisions, guidance, model settings | Proposed `id`, `locator`, `note`, optional five properties | LLM, validate count/loci/fields |
| 03 Discovery hints | Provisions, guidance, model settings | Proposed Packs v2 `discovery_hints` | LLM, validate count/loci/shape |
| 04 Assemble | Stage 01 passages, validated proposal fields, adapter metadata | Unsigned Requirement JSON objects, plus explicit diagnostics for invalid/incomplete proposals | Deterministic for fixed inputs; never overwrites earlier work |

**Important changed contract:** old Extract stage 04 assembled *only* entries accepted in `decisions.json`. Now stage 04 builds **drafts from validated proposals**, with relevant source passage, and exposes any incomplete/unusable proposals as errors or exclusions that remain visible in run diagnostics. It must not silently pretend all propositions are correct. Human review happens on saved Requirement drafts in the selected working copy.

### 4.1 Regulation adapter

An adapter is a set of files for a regulation, not a plugin framework. The developer uses a high-capability coding agent if useful to create/adjust regulation-specific deterministic splitting and atomizing. The developer verifies readable sections/provisions JSON against official text in a separate browser tab. Errors in cuts and source hierarchy are fixed in adapter code/configuration and retested; not patched via UI or `decisions.json`. Source version and language must be explicit; no LLM is required for segmentation.

### 4.1.1 `adapter.json`

| Field | Type | Required | Why it exists |
| --- | --- | --- | --- |
| `id` | string | yes | Directory name and the id stages print when they refuse a stub. |
| `status` | string | yes | `partial` or `stub`. A stub has no extraction. |
| `pack_id` | string | yes, unless `status` is `stub` | Copied onto every Requirement as `pack_id`. |
| `source` | object | yes, unless `status` is `stub` | Copied onto every Requirement as `source`. |
| `source.framework` | string | yes | Packs v2 `source.framework`. |
| `source.instrument` | string | yes | Packs v2 `source.instrument`. |
| `source.identifier` | string | yes | Act id a person looked up, such as `CELEX:32024R2847`. |
| `source.language` | string | yes | Language of `law_text`. |
| `source.url` | string | yes | The one address the passages were cut from. |
| `sections` | array | yes | The sections this adapter knows. Empty for a stub. |
| `sections[].id` | string | yes | Section id. For CRA annexes this is the roman numeral, such as `VII`. |
| `sections[].title` | string | no | Human title, so a reviewer can tell the sections apart. |
| `sections[].in_scope` | boolean | yes | Selected for stages 01–04. |
| `sections[].ready` | boolean | yes | The fixture and the atomize procedure for this section exist. Guidance and experiment settings are not part of this flag. |
| `sections[].fixture` | string | yes when `ready` is true | Path of the controlled section text, relative to the adapter directory. |

`source` has no `edition`. The edition is set or corrected when the person reviews the saved Requirement; the adapter never fabricates it.

There is no field for repo hunt globs. PoC1 `maps/defaults.yml` carries `exclude_path_globs` and `prefer_path_globs`. Those are `curbpack.json` `hunt` fields. Assemble does not copy them.

### 4.1.2 Confirmed adapters

**CRA** (`poc/components/transform/adapters/cra/adapter.yml`), status partial.

\- Section `VII` is ready and in scope. The working fixture is `fixtures/annex_vii.txt` in PoC1 and `poc2/requirements/extract/data/annex_vii.txt` in the current PoC2 code. The contract path is the adapter `fixture`.

\- Sections `II`, `V`, and `VIII` are in scope and not ready. They have no completed extraction.

\- Sections `I`, `III`, `IV`, and `VI` are not in scope and not ready.

\- The splitter cuts a full dump on lines `ANNEX \<roman>`. Text before the first annex is section `_body`. It is not in scope and it is not atomized. `_body` is not an `adapter.json` section; stage 00 adds it only when a dump was split.

\- The atomizer cuts CRA-style parts, numbered points, and lettered clauses, and it drops EUR-Lex footnote tails. That procedure is the CRA adapter's. It is not a general regulation parser.

**NIS2** (`adapters/nis/adapter.yml`) is a stub. `sections` is empty. Its note says no transform is defined.

**Medtech** (`adapters/medtech/adapter.yml`) is a stub. `sections` is empty. Its note says the current medtech material is file and structure gates, not atomized standard text. There is no fixture, prompt, or prior approved mapping.

A stub adapter refuses stages 01–04. Stage 00 lists its sections (none, for these two) and does not atomize. Passing the existing pressure-test flag (`--allow-stub` on the PoC1 steps) runs the stage anyway. That run is not support.

### CRA stage 00 and stage 01 procedures

Stage 00 with a dump calls the CRA splitter. The observable result is one section per `ANNEX \<roman>` heading, plus `_body` when any text precedes the first annex. Each annex id is the roman numeral.

Stage 00 without a dump does not split. It returns the `sections` array.

Stage 01 calls the CRA atomizer on one section's text. The observable result:

\- One provision per numbered point, and one provision per lettered clause under a point.

\- `locus` is the point (`3`), the point and letter (`1(a)`), or the part, point, and letter when the annex has a `Part` heading (`II-4(b)`). A repeated locus gets a `\~` suffix and a count, as the current atomizer does.

\- `law_text` is the passage after the atomizer collapses whitespace, wraps lines at 78 characters, and, for a lettered clause, puts the parent preamble on the line above the clause.

\- Footnote tails of the form `(n)` followed by an OJ line are removed.

\- The atomizer does not record character offsets. `locus` is the source position the later stages use.

The code is the procedure. This file does not restate the regular expressions.

### 4.1.3 Section list (disposable)

Disposable output of stage 00. JSON:

```json

{

&#x20; "sections": [

&#x20;   {

&#x20;     "id": "VII",

&#x20;     "in_scope": true,

&#x20;     "ready": true,

&#x20;     "text_file": "fixtures/annex_vii.txt"

&#x20;   }

&#x20; ]

}

```

| Field | Type | Required | Why it exists |
| --- | --- | --- | --- |
| `id` | string | yes | The section id stage 01 is called with. |
| `in_scope` | boolean | yes | Whether this run treats the section as selected. Copied from the adapter. `_body` and an annex that the dump contained but the adapter does not list are `false`. |
| `ready` | boolean | yes | Whether stage 01 may run. Copied from the adapter. An unlisted annex is `false`. |
| `text_file` | string | when the run has text for this section | Where the reviewer reads the section. A fixture path is relative to the adapter. A dump split writes the cut under the work directory, and this path points there. |

The title stays on the adapter. Stage 01 does not read `in_scope` from this file. The caller passes a section id, and stage 01 reads `in_scope` and `ready` from `adapter.json`.

A dump split writes the cut text under the work directory. PoC1 writes it into `adapters/\<id>/fixtures/annexes/`. That mixes a generated cut with controlled source. The contract keeps the cut in the work directory. Replacing an adapter fixture with a cut is a deliberate change of the controlled source.

### 4.1.4 Provision (disposable)

One disposable JSON object for stages 01, 02, and 03. Stage 01 creates it. Stages 02 and 03 add fields to the same object. There is not a separate atom file, identity file, and search file.

```json

{

&#x20; "provisions": [

&#x20;   {

&#x20;     "locus": "3",

&#x20;     "law_text": "an assessment of the cybersecurity risks …"

&#x20;   }

&#x20; ]

}

```

The file is one section's provisions. The section id is the call argument and the work-directory name, so it is not repeated on every row.

| Field | Type | Required | Written by | Why it exists |
| --- | --- | --- | --- | --- |
| `locus` | string | yes | 01 | Position of this provision inside the section. Stage 02, stage 03, and assembly use it. Unique within the section. |
| `law_text` | string | yes | 01 | The passage, as the atomizer emitted it. Assemble copies it to `references[].law_text` . |
| `id` | string | no | 02,  | Proposed Requirement `id`. |
| `locator` | string | no | 02,  | Proposed `references[].locator`. |
| `note` | string | no | 02,  | Packs v2 `note`. Omit the key when there is nothing to say. |
| `strength` | string | no | 02,  | `MUST`, `SHOULD`, or `MAY`, and only when that word is pointable in this provision's `law_text`. |
| `responsible` | string | no | 02,  | Who the duty names, only when that party is pointable in this `law_text`. |
| `applicability` | string | no | 02,  | The "where" clause in this `law_text`. |
| `exceptions` | string | no | 02,  | The exception written in this `law_text`. |
| `scope` | string | no | 02,  | The enumeration written in this `law_text`. |
| `discovery_hints` | object | no | 03,  | Packs v2 `discovery_hints`. The shape is fixed by `packs2.md` §2.7 and checked by `poc2/common/validate.py`. |

`discovery_hints` fields, all optional, at least the keys that have values:

| Field | Type | Why it exists |
| --- | --- | --- |
| `concepts` | non-empty string array | Terms for candidate discovery. |
| `path_hints` | non-empty string array | Globs for candidate discovery. |
| `sources` | non-empty array of `{ "source": string, "args"?: object }` | Where a hunt may look. `args` is omitted when that source id needs nothing. |
| `expected_evidence` | non-empty string array | What kind of artifact is sought. |

PoC1 stores this under `search`, and its `sources` entries are strings (`documents`, `git`, `requirements`). A proposal uses the Packs v2 shape. When reusing a PoC1 search entry, each string becomes `{ "source": "\<that string>" }`. `packs2.md` does not fix the list of source ids, so `requirements` may be copied as a source id. The current discovery walk does not read `source` or `args`.

The provision has no `part`, `parent_point`, `claim`, or `search`. The CRA atomizer still uses part and parent point to build `locus`. The PoC1 claim slug is not copied. PoC1 `maps/claims.yml` `id` values (`vii-3`, `vii-1a`) are not Requirement ids.

`poc2/common/validate.py` checks `strength` against `MUST` / `SHOULD` / `MAY` and checks that the other four properties are non-empty strings. It does not check that the words appear in `law_text`. The pointability rule is the one in `packs2.md`. Annex VII point 3 does not contain "shall", so its Requirement has no `strength`. The current CRA maps and the PoC1 interpret prompt do not set these five properties.

### 4.1.5 LLM note (diagnostic)

Present on the provision diagnostics only when a model ran. A parser-only developer run has no model note.

```json

{

&#x20; "llm": [

&#x20;   {

&#x20;     "stage": "interpret",

&#x20;     "strategy": "single_call",

&#x20;     "model": "qwen3-coder:30b",

&#x20;     "temperature": 0.2,

&#x20;     "endpoint": "http\://127.0.0.1:11434",

&#x20;     "prompt": "prompts/interpret.txt",

&#x20;     "prompt_sha256": "<64 lowercase hex characters>"

&#x20;   }

&#x20; ]

}

```

One entry per model call. A producer that calls the model more than once appends one entry per call, in call order. Those entries share `stage` and `strategy`. There is no separate run object: the provision file is the run, and the list is the calls.

| Field | Type | Required | Why it exists |
| --- | --- | --- | --- |
| `stage` | `interpret` or `discovery_hints` | yes | Which stage's producer made this call, when both stages wrote one file. |
| `strategy` | `single_call`, `multi_prompt`, or `propose_critique_revise` | yes | Which producer implementation ran. The call list does not show this: two calls can be two stages, two prompts, or a revise loop. The same value is repeated on each call from that invocation so the list stays flat. |
| `model` | string | yes | The model name requested for this call. PoC1's default is `qwen3-coder:30b`. |
| `temperature` | number | yes | Sent for this call. PoC1 sends `0.2`. |
| `endpoint` | string | yes | PoC1's default is `http\://127.0.0.1:11434`. The model name alone does not say which server answered. |
| `prompt` | string | yes | Path of the guidance file for this call, as the caller passed it. The default is the adapter's `prompts/interpret.txt` or `prompts/discovery_hints.txt`. |
| `prompt_sha256` | string | yes | Lowercase hex SHA-256 of that file's UTF-8 bytes. The path can later point at different text; the hash is the guidance that was sent. The prompt body is not copied onto the note. |
| `max_rounds` | integer | only when `strategy` is `propose_critique_revise` | The bound the caller set. Absent for the other two strategies. The number of entries is not this bound when the loop stops early. |

The call does not send a seed. The note does not include the raw response, a critique, or a score. Two runs with the same note can still differ. The note is not copied onto the Requirement.

### 4.2 Stage interfaces, proposal validation and model settings

Each stage is a direct Python callable and runs without the web server. Caller supplies adapter id, section id, source/provision path and work location where relevant; jobs forward typed arguments rather than hard-coded CLI strings. Unsupported or stub adapters refuse extraction, not successful empty output. The pressure-test option, if retained, is developer-only and never enabled by the product UI.

**00:** validate unique section IDs, Boolean scope/readiness, existing fixture for ready sections; full-dump splitter may add `_body` but never silently places that text in scope.

**01:** nonempty and unique `locus` strings with nonempty `law_text`; fail explicitly if no operable text. The CRA adapter preserves numbered and lettered clauses and parent preamble as specified above. A developer changes adapter code to correct mistakes.

**02:** producer receives the exact provision list and rendered guidance. Require exactly one result per input locus, no missing, duplicate or invented loci. Allowed result fields: `locus`, `id`, `locator`, `note`, `strength`, `responsible`, `applicability`, `exceptions`, `scope`. Reject legacy `claim`, top-level `search`, and unexpected fields. Strength is `MUST`, `SHOULD` or `MAY` only when supportable by source text; the validator checks enum/shape, not semantic truth. Source passage is never replaced by the model. Interpret outputs are **draft proposals**, not approved decisions.

**03:** independently receives provisions (not requiring stage 02 identity); validates one result per input locus; allowed fields `locus`, `discovery_hints` only. `discovery_hints` follows Packs v2, preserving `sources[].args` and every optional field. Stages 02 and 03 can run independently or as one product job.

**04:** deterministically combines validated stage 02/03 proposals with adapter `pack_id` and `source` and the stage 01 passages: `references[]` starts with `nr:1`, source `locator`, and `law_text`. Omit `signed`, `origin`, top-level `law_text`, `claim`, `search`, `locus`. Validate each draft. A missing required id/locator or invalid object is reported and never saved as a valid Requirement; the run must visibly report incomplete coverage rather than silently dropping loci. The normal full Extract creates a new dated working copy, not a modification to an earlier one.

| Proposal argument | Default from existing PoC1/PoC2 design |
| --- | --- |
| `strategy` | `single_call` |
| `model` | `qwen3-coder:30b` |
| `temperature` | `0.2` |
| `endpoint` | `http://127.0.0.1:11434` |
| `guidance` | adapter `prompts/interpret.txt` or `prompts/discovery_hints.txt` |
| `max_rounds` | required only for `propose_critique_revise` |

Strategies: `single_call` (one call); `multi_prompt` (several prompts/models and a producer-defined reduction to one validated list); `propose_critique_revise` (bounded proposal, critique, revision, returns final validated list). Record per-call model, strategy, endpoint, temperature, prompt path/hash and max_rounds where relevant as **diagnostics**, not in Requirement or Pack. Model output is not guaranteed reproducible even with identical arguments. Compare separate dated runs to evaluate model/prompt changes. No vector store, RAG pipeline, or additional domain schema is introduced.

### 4.3 Re-running extraction

Re-running the same or changed parser/LLM **always** creates a new dated working copy. This replaces the old `decisions.json` replay/clean-rebuild semantics. Deterministic parser reruns can validate structure without model calls, but they are developer actions; they do not reconstruct saved, human-edited Requirements. No approved Requirement is recreated from `decisions.json`; existing working copies remain intact. An optional comparison of fresh output with previous work is **Compare** (§6), not Extract's own replay mechanism.

## 5. Requirements Editor and signing

Editor loads one Requirement by ID from the **selected working copy**. It never infers a fixed `CRA-ANNEX-VII-RISK` path. It shows every `references[]` item, source fields, `note`, `remediation_hint`, five properties, and full `discovery_hints` including sources `args`. It must preserve every field not explicitly changed. `references[].nr` is assigned `1..n` in current array order. A no-op patch does not remove `signed`; a changed payload does. All writes validate Packs v2. Editing source `law_text` in a draft is a human correction to the Requirement, **not** a change to the regulation adapter.

| Operation | Input | Result / protection |
| --- | --- | --- |
| `load_requirement` | selected copy, Requirement id | Parsed and validated existing object |
| `apply_edits` | stored object, subset patch | New validated object; omitted keys preserved; `signed` dropped if and only if payload digest differs |
| `save_requirement` | selected writable copy, updated object | Saves only to selected copy, never a published directory; reject stale/changed-on-disk input rather than silently overwriting concurrent changes |
| `withdraw_requirement_signature` | signed object | Same content without `signed`; explicit confirmation |
| `publish_requirement` | publisher Requirement, signer inputs | Signed Requirement; `source.edition` required as in Packs v2 |
| `approve_working_copy` | Requirement with Packs v2 `origin`, signer inputs | Signed local Requirement, retains `origin` |
| `working_copy` / `accept_published_version` | publisher Requirement and destination local Pack | Sets `origin` per Packs v2. The destination is a timestamped working copy. The timestamp does not set `origin`. Extract writes no `origin`. |
| `read_signature` / `read_pack_seal` | object or directory, trust, file context | Five-fact reading under Packs v2 §2.6 (including applicable signed-Git-commit fallback) |

Signatures are stored on the existing object. A pack directory seal is separate from each Requirement's signature. Changing a file invalidates the directory seal until it is created again. An unsigned Requirement is a draft, not a different schema. The system validates signatures; organizational signing authority is not inferred from a signer name. Preserve signed Git-commit semantics from Packs v2 when no `signed` block exists. The Git author string and the employee identified at the deployment boundary are not that signature.

## 6. Compare (independent component inside Requirements)

Compare takes any two selected existing Pack snapshots (dated copies or published versions). Reading and diff computation are **strictly read-only**. Compare produces a transient view model; not a persisted comparison/domain object. A user can explicitly choose a *writable destination working copy* and apply a whole Requirement or selected field changes. Never modify comparison sources simply by opening Compare. Changes to signed destination payload remove `signed`; a no-op does not. Published versions cannot be chosen as writable destinations.

**Matching and comparison:** first compare Requirements of the same ID, then use source `references[].locator` plus the source identity to detect possible one-to-many/many-to-one relationships (e.g. a previously consolidated Requirement against two new extracted drafts). A reference match is **a candidate relationship**, not automatic acceptance. Show unchanged, changed (field-level), newly present, missing, and possible consolidation/split; ambiguous matches require user choice. `source` and complete `references[]` remain visible. Diffs must include `discovery_hints.sources[].args`, not just visible text. A missing ID match is not grounds for automatic deletion.

| Operation | Input | Return / side effect |
| --- | --- | --- |
| `compare_copies` | source path, other path | Unmodified snapshots and transient diff including ambiguous matches |
| `preview_transfer` | selected fields/Requirements, destination | Exact resulting JSON and validation/error list, no writes |
| `apply_transfer` | explicit selection, writable destination, expected source/destination digests | Validate and write destination atomically; source unchanged; fail on stale versions |

Copying one field must preserve all unrelated fields. A whole-Requirement copy must resolve duplicate IDs and `pack_id` consistency before writing; it must **not** carry an old signature covering a different local payload. Applying a candidate match never silently deletes an existing Requirement. The Compare page provides a human choice of source, destination and selected changes.

## 7. Consolidator (independent component inside Requirements)

Consolidator detects *possible* duplicate/overlapping Requirements in one selected writable working copy. Initial matching may use deterministic text/reference overlap; optional LLM suggestions are explicitly advisory. Compare/Consolidator share Packs v2 Requirements, **not** a new persistent merge schema. The user inspects original Requirements with their passages, chooses the resulting Requirement ID and edited fields, reviews the combined references, and confirms.

A confirmed **merge** leaves exactly **one** Requirement whose `references[]` preserve all relevant passages, renumbered `1..n`. Redundant **unsigned drafts** are removed only after the merged output has been validated and durably saved; log their identities for operational diagnosis if needed. Do not automatically delete a signed draft, any previously published object, or anything outside the selected working copy. Require explicit treatment of conflicting properties, hints and source metadata; never silently pick one side. A confirmed split is ordinary explicit creation/editing of Requirements and removal of source draft only with user confirmation; no independent `ConsolidationDecision` schema is needed.

| Operation | Input | Return / side effect |
| --- | --- | --- |
| `suggest_consolidations` | selected copy | Transient ranked candidate groups and reasons; no writes |
| `preview_consolidation` | selected IDs, proposed retained ID/fields/references | Validated preview and conflicts; no writes |
| `apply_consolidation` | confirmed preview, expected digests, selected writable copy | Atomic save of retained Requirement and removal of redundant unsigned drafts, or no writes on failure |

If a source Requirement carries `signed`, do **not** strip it and delete it as an implicit consequence. Require separate explicit human workflow first. Newly consolidated content is an unsigned draft until signed. The source legal text is preserved via references; the redundant Requirement ID is not itself a new persisted object.

## 8. Publication

The user selects the Pack working copy and explicit `pack.version`. Publisher publication validates the pack metadata, every included Requirement and the required seals per Packs v2, and then creates an **immutable release directory**. It applies only to a working copy whose Requirements have no `origin`. It refuses to overwrite an existing version and refuses an invalid, missing, partial, or inconsistent working copy, including a Requirement that still has `origin`. A file change after review invalidates the relevant signature: publication cannot pretend a verified reading applies to new bytes. Publication failure must not leave a directory discoverable as a complete published release.

| Action | Function | Effect |
| --- | --- | --- |
| Save Pack metadata | Pack validation and save on selected copy | Updated draft metadata; existing directory seal no longer verifies after payload changes |
| Publish/sign Requirement | `publish_requirement` or `approve_working_copy` according to Packs v2 `origin` | Signed version of that saved Requirement |
| Seal Pack | `seal_pack_directory` over validated directory | Pack directory seal, independent of Requirement seals |
| Publish release | `publish_pack` | New immutable `published/<pack-id>/<version>/` with Pack metadata and Requirements only |

An unsigned Requirement may be visible during editing, but publish must not silently treat it as signed approval. Existing Packs v2 seal requirements govern what can be called a published Pack. Avoid inventing `Approved`, `PackDraft`, or a new publication entity. The timestamped source copy remains available after release. Publication is a *new version*, never in-place modification of a prior release.

Publisher publication uses `publish_requirement` and `publish_pack` and applies only to Requirements with no `origin`. Local acceptance uses `approve_working_copy`, keeps `origin`, and does not create `published/<pack-id>/<version>/`. Local acceptance is not a new version from the source publisher. This contract has no operation that removes `origin`, changes `pack_id`, or signs a local copy so the result is the source publisher's release. An organisation publishing under its own separate pack identity is a separate publisher workflow and is outside this document.

## 9. Thin UI/UX contract

Requirements owns rendering of its pages; `app/` only routes and serves them. The visual baseline is PoC1: compact tables, English labels, source link in new tab, status pills, green save flash/red error, modal for signer name and long jobs. UX is specified to be reproducible without copying legacy UI code. Developer-only parsing and adapter debugging may later get optional support UI; they are not required product screens.

| View | Shows | Important actions |
| --- | --- | --- |
| Catalog / working copies | Packs and regulation adapters, source links, available dated copies, latest marker, incomplete/failed run flags, published versions with pack id, version, and the signature reading | Select a dated working copy, start **new Extract**, import a published Pack, create a local working copy from a published Pack, open the current working copy. A published directory stays read-only |
| Section / extraction status | Parsed provision loci/passages and model notes for a selected run (diagnostic context); generated Requirements and coverage/errors | Open Requirement, inspect job progress; no visual editing of cuts; use adapter code for parser corrections |
| Requirement Editor | All reference passages and all Packs v2 fields, signature reading and pack seal summary | Edit, save, add/reorder references, sign/withdraw, return to copy |
| Compare | Side-by-side snapshots, field differences, one-to-many candidate relationships | Choose explicit source/destination, preview and apply selected fields/Requirements |
| Consolidator | Candidate overlaps, source references and conflicting fields, resulting JSON preview | Review and confirm merge, reject suggestion without saving |
| Pack publication | Full Pack metadata, included Requirements, individual and directory seal readings, destination version | Save metadata, sign, seal, publish as new version |

### 9.1 Job modal and states (preserve PoC1)

A long operation reports `running`, `done`, `failed`, or `aborted`, current stage, progress as activity (not provision coverage), last 200 log lines and explicit error. Poll twice per second while visible/running. While running, Escape/backdrop does not abort or dismiss; **Abort** requests termination; UI polls until terminal. On done/aborted reload the relevant page; on failure keep the log visible until **Close**. A failed Extract never implies successful published Requirements; prior copies and published releases are byte-for-byte unchanged. A job record is operational, not Packs v2 data; do not store it inside a Pack directory to be sealed.

### 9.2 Editor interactions

The editor shows every `references[]` item with `locator`, `law_text` and displayed `nr` (assigned by the operation, not manually submitted). **Add**, **Remove**, **Move up/down** affect local form state only until save. Display `source.framework`, `instrument`, `identifier`, `edition`, `language`, and clickable `url`; `note`, `remediation_hint`, `strength` (blank/MUST/SHOULD/MAY), `responsible`, `applicability`, `exceptions`, `scope`; discovery-hints lists `concepts`, `path_hints`, `expected_evidence` and every `{source,args?}` entry (with JSON validation for `args`). Blank optional values remove the key; omitted inputs leave fields unchanged. Never convert sources to bare strings or lose `args`.

Initially a verifiably signed Requirement is read-only; **Edit** enables inputs locally without writing. **Save** validates and changes only the selected copy, stripping `signed` if and only if the payload digest changes. Dirty form shows **Unsaved edits. The saved version is unchanged.** Signing/publishing controls do not operate on unsaved inputs. Show five-fact reading (what/who/when/which version/verifiable/reason) and separate Pack seal state. Unknown Requirement shows Not found, not an unhandled traceback. Success/failure flashes identify the operation; never show raw stack traces.

### 9.3 Sign and publish modals

One name modal for **Publish and sign**, **Approve and sign**, and **Seal Pack directory**; name required, Cancel/escape/backdrop writes nothing. Current PoC2 local-key sentence: *Local Ed25519 keys are created when someone signs. They are not X.509 certificates.* These operations never sign unsaved browser state. A publishing Requirement with no `origin` uses `publish_requirement`; a Packs v2 local copy with `origin` uses `approve_working_copy`. Do not infer approval authority from a typed name. Display errors returned by the operations, not duplicated validation in page handlers.

### 9.4 Human journeys

1. **New run:** choose Pack and corpus/adapter → Extract allocates a new dated copy → show job progress and incomplete coverage/errors → open its drafts after successful completion.
2. **Review:** inspect legal text/reference beside interpretation → edit and save actual Requirement draft → sign when satisfied. Parser segmentation corrections are made in adapter code outside the product UI.
3. **Later run:** run Extract again → *new* directory → compare against previous working copy/publication → explicitly transfer desired fields or requirements to selected destination (never overwrite implicitly).
4. **Consolidate:** review overlap candidates → preview one merged Requirement preserving multiple references → confirm → redundant unsigned draft(s) removed in the current copy only → sign merged draft later.
5. **Publish:** select a working copy whose Requirements have no `origin` → verify contents/signatures → set `pack.version` → seal as required → create a new immutable published release. Published packs remain available for future comparisons. A working copy that still has `origin` is approved with `approve_working_copy` and is not this release.
6. **Recovery:** a failed/aborted job never mutates previously existing copies. A failed compare/consolidate/publish/import write leaves a consistent previous state and clear error. When the workspace is the organisation repository, restoring an earlier Git revision recovers the Packs v2 files from that revision and leaves selection by pack id and timestamp in place.
7. **Import and local copy:** import a published Pack, then read that published directory unchanged. Create a local working copy: a new dated directory with `origin` set. Edit that copy and approve it with `origin` retained. The imported or previously published directory is unchanged. Publishing a release remains journey 5 and applies to Requirements with no `origin`.

## 10. PoC1 capabilities carried forward

This table is a **functional preservation checklist**, not permission to keep PoC1's YAML, approval files, maps or job schema as canonical types.

| PoC1 capability | Target decision |
| --- | --- |
| Registered documents, adapter/batch listing, source URL | Keep as Pack/adapter catalog and dated working-copy selection. |
| CRA regulation-specific splitter and atomizer | Keep deterministically in adapter, with controlled fixture and developer-inspected JSON. |
| Batch extraction and progress modal with Abort/log | Keep, now create a new dated copy per Extract run. |
| View all extracted loci/passages and proposals | Keep as review/context; actual accepted data lives in Requirement JSON. |
| Edit requirement text, notes, hints and save | Keep; extend to **all** Packs v2 fields and multiple references without losing unsubmitted fields. |
| Signed/unsigned badges and signer modal | Keep with real Packs v2 signatures and independent Pack directory seal; no demo seal. |
| LLM strategy/model/prompt experimentation | Keep as callable Extract arguments and diagnostics; no required product experiment UI. |
| Offline replay of PoC1 map values | **Remove as approval/reconstruction mechanism.** Compare saved Requirements across separate runs instead. |
| Compare old gold output | Replace with component Compare operating on actual Packs v2 Requirements. |
| Human merges/edits | Persist directly as one or more Requirements; Consolidator supports reviewed merge. |
| Legacy hunt YAML, `claim` slug, `seals.json`, `sources.json`, gate approval file | Do not revive. Claims/Discovery are separate subsystem. |
| Fake Curbpack SCAN panel | Drop; real Checks and Review are separate. |

## 11. Acceptance criteria (target)

1. Two new Extract calls on the same Pack create **different** uniquely dated directories with intact pre-existing outputs; first run contents and published versions are byte-identical afterward.
2. A developer-controlled CRA adapter yields stable section/provision JSON with unique loci and complete correct source cuts across the Annex VII test fixture. NIS2/Medtech stub adapters refuse rather than claiming success.
3. Stages 02 and 03 reject invented/missing loci, wrong count, forbidden fields and malformed discovery hints; no `Claim`, `claim` or `search` field is emitted on a Requirement.
4. Stage 04 creates validated, **unsigned Packs v2 Requirement JSON** within the newly created copy from available valid proposals, recording unmatched/invalid provisions as visible incomplete extraction. `decisions.json` is neither read nor written.
5. Different model/prompt arguments leave adapters and earlier copies untouched; new output contains traceable model-call diagnostics outside published Pack material.
6. Selecting a previous working copy loads its Requirements directly without replaying or running Extract; switching to another copy changes the read/write target explicitly.
7. Editing `remediation_hint` preserves all unsubmitted properties, references and `discovery_hints.sources[].args`. Same-value edit preserves `signed`; changed payload removes `signed` and invalidates the relevant directory seal reading.
8. Two references store `nr` 1 and 2 in array order; the editor displays both passages and all fields, including source URL.
9. Compare identical and changed IDs, additions/deletions and one-to-many reference correspondence. Merely comparing makes **zero filesystem writes**. Transferring a selected field alters only the chosen writable destination, preserves unrelated fields, and cannot overwrite concurrent modifications.
10. Consolidator suggestions make **zero writes**. Confirmed consolidation of two unsigned Requirements yields exactly one with both law passages; conflicts are explicitly resolved. Partial failure does not lose a source. Signed/published requirements are never silently removed.
11. Publication refuses an existing version, an invalid/partial copy and stale signatures as Packs v2 requires; a successful versioned directory contains only correct Pack artifacts and remains immutable. No published directory is partially exposed after failure.
12. Signing a Requirement and sealing its Pack are independent; `read_signature`/`read_pack_seal` show the correct five facts, including applicable signed Git commits and missing-key states.
13. All operations are callable directly from Python tests/CLI without importing the HTTP server. UI handlers do not implement source parsing, file IO, signing or domain validation.
14. UI can select working copies, render a multi-Requirement catalog, edit all fields, show a long-running job, Compare, Consolidate and publish, with the correct read-only and unsaved states.
15. `curbcheck`, Claims, Compile and Review continue to operate on selected **published Packs v2** independently of Extract and the Requirements UI.
16. Import stores a published Pack byte-for-byte, with no `origin` added, and leaves the source unchanged. The same bytes at the same pack id and version stay as they are. Different bytes at that identity are refused, and a failed import leaves no new published directory. The imported directory is not a writable working copy.
17. A local working copy of an imported or own published Pack is a new timestamped directory. `origin` names that pack id and version. The published directory is unchanged and the copy is unsigned. `approve_working_copy` retains `origin` and does not create a published release.
18. Publisher publication still requires every included Requirement to have no `origin`. Removing `origin`, changing pack identity, or signing a local copy so it reads as the source publisher's release is outside this contract.

## 12. Implementation delta and matters to verify

**This is a specification, not a statement of current implementation.** Current PoC2 still renders one hard-coded CRA Requirement, and current Extract stage 04 / previous architectural text rely on `decisions.json` and acceptance after assembly. Migration must update code/tests to the target contract; never treat those obsolete behaviors as requirements to preserve.

- Replace `write_decision`, decision replay and `accept_assembled` in the target lifecycle with durable unsigned draft output per dated Extract working copy and explicit later editing.
- Retain precise adapter parsing, valid proposal shapes, model experiment strategies and PoC1 job UX. Preserve existing signing, canonical digest, validation and Packs v2 working-copy (`origin`) functions where consistent.
- Specify/implement unique copy allocation, copy selection and publication transaction/atomicity and test safe failure. These are engineering details required by the already-decided workflow, not additional domain schemas.
- Distinguish `pack.version`, Requirement content digest and extraction timestamp. Do not invent a sequential Requirement-version counter.
- Confirm the precise adapter/source pairing, ID and locator conventions for additional CRA loci, CRA articles, NIS2 and Medtech when implementing those adapters. Keep regulation-specific naming out of shared stage code; do not guess IDs from old PoC1 claim slugs.
- The target **one document** supersedes the previous standalone Extract architecture; keep its old code/path as an implementation reference only until physical migration.

**Scope limit:** no additional user-facing adapter-editor UI, no vector database, no new persistence engine, no generic workflow framework, no OIDC, organisation, or employee implementation, no repository provisioning, and no HTTP-framework coupling. The workspace root stays the configured directory until the deployment supplies the organisation's Git repository as that root. Product decisions follow Packs v2 and the overall PoC2 architecture. The dated working-copy layout and selection by pack id and timestamp stay. An organisation publishing under its own separate pack identity, after adapting someone else's Pack, is not specified here.
