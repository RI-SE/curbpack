# Pack / Requirements — subsystem architecture

**Status:** Target functional contract for `studio/pack/`, aligned with the approved Curbpack target architecture and revised EP-11 (2026-11-06). Current `requirements/` is a migration source. All exact persistent shapes remain governed by the human-approved `docs/reference/packs2.md`; VR-00/VL-00 changes must be incorporated there before implementation.

## 1. Scope and invariants

The Pack component owns regulation adapters and Extract, Pack/Requirement workspace selection and IO, import/export, human Review/Edit, Compare, Consolidator, signing, and cross-namespace Take Ownership. Its HTTP router, backend implementation, and thin TypeScript pages belong together under `studio/pack/`. It does **not** own Claims, Discovery of product evidence, Check execution, Compile, or final product Review.

- Extract source parsing is deterministic; interpretation and discovery-hint proposals may use models and must remain reviewable. A proposal is not silently applied.
- Pack/Requirement persisted objects are exactly Packs v2; extraction diagnostics and proposals are operational artifacts, not alternative accepted Requirement types.
- Only an explicitly selected writable Pack is modified; reads and Compare previews are side-effect-free. Existing payload changes invalidate only affected signatures; a no-op does not.
- Pack and Requirement identity, `origin` and `status` follow VL-00. Cross-namespace editing invokes the explicit whole-Pack Take Ownership backend operation defined by VL-01; originals are untouched.
- Embedded signatures and trusted Git-commit signatures are independently reported by VR-00. Signing is not review status or an approval decision. A signed Pack can contain unsigned Requirements.
- EP-01 Export is extended by VL-02 ZIP export/import of the existing Pack directory. Export is non-blocking; Import performs safe extraction and collision protection.
- `studio/pack/router.py` owns Pack/Requirements REST paths; `impl/` is headless and called by REST and optional thin CLI. UI uses REST and does not implement filesystem, diff, validation, or signing policy.
- Preserve the current working flows, data and tests during EP-02. VL-00–VL-03 are subsequent behavioral changes, not undocumented migration assumptions.

## 2. Workspace, versions, ownership and exchange

`docs/reference/workspace.md` is the current source for configured Pack locations. `docs/reference/packs2.md` is the norm for Pack/Requirement identity and persistent fields. The revised VL-00 namespace contract must update both documents through explicit approval; do not infer a new pathname scheme from `namespace` or from the version digest.

The current repository supports selected Pack directories, Extract outputs, editable snapshots and Git history. A working snapshot is different from `pack.version`, a Requirement payload digest, and a Git commit. Existing dated-copy behavior remains a migration baseline where in use, **not** a required new publication scheme.

| Backend operation | Responsibility and invariant |
|---|---|
| List/select/load Packs and Requirements | Respect configured paths, namespace-aware identity after VL-00, reject ambiguous or missing selection; no mutation on read |
| Extract and save a proposal | Preserve existing extraction flow, diagnostics and source traceability; do not silently overwrite accepted Requirements |
| Compare/preview/apply | Compare current and proposed data in backend; explicit selected changes only; atomic saves, no read-time mutations |
| Edit Requirement / Pack metadata | Validate against Packs v2; preserve unmodified fields; invalidate affected signatures on actual payload change |
| Take ownership (VL-01) | Explicitly confirm then atomically copy the **entire** foreign Pack into the local namespace, set immediate Pack and Requirement origins, invalidate copied signatures, protect source/collisions |
| Import/Export ZIP (VL-02) | Exchange the existing Pack directory tree, preserve bytes/signatures/origin; validate ZIP path safety and identity collisions; allow unsigned export |
| Verify/sign | Reuse shared signing verification and Pack directory seal, report method/status separately; do not make Export depend on sealing |

**No separate mandatory Publish operation** or immutable `published/<id>/<version>/` service is part of the revised target. Older published directories, if present, remain historical data and must not be deleted as part of EP-02. Retired `publish_pack`, `publish_requirement` and `approve_working_copy` workflow assumptions are not new acceptance requirements. Git provides version history; do not build a separate SQLite version store.

## 3. Component responsibilities

| Component | Owns | Does not own |
|---|---|---|
| Source/adapters and Extract | Deterministic source parsing, model proposals, extraction diagnostics | Claims or repository evidence discovery |
| Pack catalog and workspace | Selection, configured paths, read/write rules, import/export | Alternative data format or invisible versioning |
| Editor | Human-reviewed Requirement/Pack changes, backend validation and save | Extraction adapters or Claim editing |
| Compare | Backend diff/preview/apply, source/proposed values, explicit selection | Automatic merge or UI implementation of diff rules |
| Consolidator | Suggested overlaps, explicit human-confirmed consolidations | Silent deletion, new persistent decision schema |
| Signing and verification | Shared Pack/Requirement signature operations and distinct validity readings | Approval, status changes or release gates |
| Ownership | Atomic whole-Pack cross-namespace copy with provenance | Rewriting imported originals |
| Router / UI | Thin HTTP contract / presentation and interaction respectively | Backend business logic |

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

The Editor loads an exact Requirement from the selected Pack. It presents all references, legal source, notes, properties and discovery hints, preserving fields not explicitly edited. Editing legal text in a draft is a human modification, not an adapter change. The backend validates all writes against Packs v2 and performs compare-and-save protection against stale input.

| Operation | Result / protection |
|---|---|
| Load/select Requirement | Resolve namespace-qualified identity after VL-00; no hard-coded Requirement IDs |
| Apply edits | Change only selected fields; no-op keeps signatures; a changed signed payload invalidates its signature |
| Save Requirement | Write atomically to selected writable Pack; never mutate another Pack merely by viewing it |
| Sign / verify Requirement or Pack | Use shared VR-00 signing/verification; Pack signature and Requirement signatures are independent |
| Ownership before foreign edit | VL-01 confirmation and **whole-Pack** copy; all copied Requirements carry immediate origins |

`status` (`draft` / `reviewed`) is a separate human declaration under VL-00, not computed from the signature. No automatic re-sign, no implicit signed = approved. `withdraw_signature` remains an explicit supported operation where applicable.

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

## 8. Signing, ownership and Pack exchange

Signature reading and signing are backend operations shared with other components. A signed Pack may contain unsigned Requirements. Export of a Pack directory or ZIP is permitted whether signatures verify, fail, or are absent; display the independent reading instead of gating export. The VR-00 verification rules distinguish valid/invalid/unsigned and method/reason, and an invalid embedded signature must not be concealed by a signed Git commit.

When `pack.namespace` is foreign to the configured namespace base, any edit first requires VL-01's explicit Take Ownership confirmation. On acceptance the **entire Pack** is copied atomically with `origin` recorded for the Pack and each Requirement, current namespace assigned, signatures invalidated, and the original left unchanged. Failure leaves no partial copy. Normal same-namespace edits retain origins.

VL-02 ZIP export/import exchanges existing Pack files, not a second manifest/schema. Import is atomic, rejects traversal/symlink escape and collisions, preserves signatures and origin, and enters the same Requirements compare/review/edit workflow as Extract. Neither import nor export implies Publish.

## 9. Thin UI and interaction contract

Pack UI belongs under `studio/pack/pages/` as thin TypeScript components using Pack REST operations. `studio/pack/router.py` owns all Pack/Requirements HTTP paths, not `studio/app.py`. Pages do not parse arbitrary on-disk Pack data, implement business validation or compute canonical differences.

Retain Pack -> Sections / Sources navigation, source Edit/Extract, job progress and diagnostics, complete Requirement editing, signing, Compare, Consolidator and non-blocking Export functionality. The new VL-03 Compare page displays the familiar editing form with changed fields offering complete Old/New values, supports select-all choices, and calls the existing backend compare/apply operations; it is not a second diff engine. Compare and Import feed the same review flow. See VL-03 for precise GWT acceptance rather than re-specifying the UI here.

The old Python-HTML pages and central handlers are implementation sources for EP-02 only. Do not preserve their placement or introduce a second UI backend.

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

## 11. Preservation and verification

EP-02 moves this component without altering extraction semantics, existing selectable Pack content, adapter rules, diagnostics, signing behavior (except separately authorized VR-00), Compare/Consolidator outcomes, or successful accepted user flows. Each migrated entry point is mapped to a target operation and an existing or improved regression in `MIGRATION_COVERAGE.md`.

Later VR-00/VL-00–VL-03 tests establish signature readings, namespace/origin/status, whole-Pack ownership, ZIP round-trip and form-based Compare explicitly. Do not silently label those future requirements already satisfied by migration.

## 12. Current implementation notes (non-normative)

Legacy `requirements/`, `app/server.py` and Python-rendered pages are source locations for EP-02 migration; any historical PoC1/PoC2 paths in retained Extract sections refer to evidence/examples, not authorized destination paths. The destination owner is `studio/pack/`, and the detailed current-to-target inventory is `docs/agile/epics/02-modularize-studio/MIGRATION_COVERAGE.md`.
