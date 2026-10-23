# Studio architecture (imported from PoC2)

**Status:** retained normative architecture for the imported pilot. This file owns subsystem boundaries; `docs/reference/packs2.md` owns persistent data formats. It is not a second Packs v2 specification.

**Path convention:** this document predates the move to Studio. Any `poc2/` path here means the **root of this Studio repository**; the `poc/` references identify a retired functional baseline, not a directory or runtime dependency required here. Keep the distinction between current and proposed target paths. Do not move code as part of this documentation review.

**Direction.** All new PoC2 development follows the target subsystem architecture below. Current physical paths remain valid until migration; do not change behaviour or interfaces merely to fit the target layout.

## Purpose and architectural boundary

PoC2 carries the Packs v2 lifecycle: source text, reviewed requirements, discovery, repository claims, checks, compile, and final human review. `poc/` shows behaviour that already works. PoC2 does not import it.

`docs/reference/packs2.md` in this repository is the common persistent domain model. It is authoritative for the meaning and fields of Pack, Requirement (including `discovery_hints`), Claim, source/check IDs and `args`, signing, and run results. Do not introduce alternate persistent representations. If a field or lifecycle rule is unresolved, record the precise question rather than improvising a schema.

Each subsystem owns one `ARCHITECTURE.md` containing its component contracts. This file does not duplicate those specifications. Extract is a component of Requirements. Its code is `poc2/requirements/extract/`, and its contract is [`../requirements/ARCHITECTURE.md`](../requirements/ARCHITECTURE.md). The check runner is in [`../checks/ARCHITECTURE.md`](../checks/ARCHITECTURE.md). Compile and final review are currently specified together in [`../review/ARCHITECTURE.md`](../review/ARCHITECTURE.md); the target splits them into `compile/` and `review/` without inventing new Packs v2 types.

`doc/END_TO_END_SCENARIO.md` keeps the 12 October narrative unchanged. Its acceptance criteria are the end-to-end test for that Annex VII point 3 path. The narrative is not a second specification. Scenarios that cross several subsystems are in this file.

The original `poc/` and CTAM repositories are historical references only. Studio is the implementation repository.

## Architecture documentation

| Document | Owns |
| --- | --- |
| `poc2/doc/ARCHITECTURE.md` (this file) | Overall architecture, subsystem boundaries, interfaces, current vs target paths |
| One `ARCHITECTURE.md` per subsystem | That subsystem's components and internal contracts |

There is exactly one `ARCHITECTURE.md` per subsystem. Components, including Extract, are specified in their subsystem document; existing component documents may remain as temporary references during migration, but are not additional target architecture documents. Do not duplicate contracts.

## Target subsystem architecture

PoC2 is organised as independently usable subsystems. Each subsystem exposes functions callable from CLI, CI/CD, tests, and graphical UI. A subsystem's UI is an optional interface to those functions, never a prerequisite. Packs v2 objects are the shared persistent interface between subsystems. The same independence applies to HTTP; the boundary to check when specifying a subsystem is [HTTP server](#http-server).

Signing is an operation on existing Packs v2 objects (Requirement, Pack directory, Claim, review report). Do not invent publication, approval, or draft domain types. Candidate, selected, draft, unsigned, and signed are UI or workflow terms describing existing objects and actions (see Workflow words).

| Subsystem | Responsibility | Contains (components) | Does not own |
| --- | --- | --- | --- |
| **requirements/** | Requirements Management | Extract and review proposed changes; import of a published Pack; configured working directories; Compare; Consolidator; Requirements editing and human review; validation and signing; its own UI | Discovery, Claims, checks, compile, final review |
| **claims/** | Claims Management | Discovery; Claims editing, rebinding, and human review; signing of Claims; its own UI | Requirement edits, checks, compile, final review |
| **checks/** | Evaluation of Claims | Check runner, check-args validation used by evaluation, and its own UI | Discovery, Claim binding, compile, final review |
| **compile/** | Compilation and reporting of check results | Building the review report from a run result | Running checks; recording the reviewer's decision or seal |
| **review/** | Final human review of compiled results | Decision text, `review-sign` on the report, and its own UI | Running checks; Claim or Requirement seals |
| **common/** | Shared technical functions | Packs v2 validation, signing helpers, persistence IO | Product workflow, subsystem UI, Extract/Discovery strategy |
| **app/** | Overall application integration and navigation | Cover / navigation, HTTP entry | Ownership of subsystem UIs or domain logic |

Extract is a component of Requirements, not a top-level subsystem. Discovery is a component of Claims, not a top-level subsystem. The Requirements Editor and Claims Editor remain components of their respective subsystems.

### Explicit target directory structure

This is the agreed physical target structure, not merely an illustrative diagram. Do not invent additional layers or directories. Do not create empty directories for components that are not implemented yet.

```text

poc2/

├── doc/

│   ├── ARCHITECTURE.md

│   └── WORKING_RULES.md

├── requirements/

│   ├── ARCHITECTURE.md

│   ├── extract/

│   ├── editor/

│   └── ui/

├── claims/

│   ├── ARCHITECTURE.md

│   ├── discovery/

│   ├── editor/

│   └── ui/

├── checks/

│   ├── ARCHITECTURE.md

│   └── ui/

├── compile/

│   └── ARCHITECTURE.md

├── review/

│   ├── ARCHITECTURE.md

│   └── ui/

├── common/

└── app/

```

`tests/`, `data/`, and other support trees may exist beside this structure; they are not additional product subsystems.

## Current physical paths vs target paths

Until migration, existing implementation paths and documentation links remain authoritative for what is already built. Target paths are the destination. Do not move code, create empty component directories, or rewrite imports solely to match the diagram.

| Concern | Current path (valid until migration) | Target path |
| --- | --- | --- |
| Overall architecture | `poc2/doc/ARCHITECTURE.md` | unchanged |
| Working rules | `poc2/doc/WORKING_RULES.md` | unchanged |
| Requirements subsystem | `poc2/requirements/` (+ [`ARCHITECTURE.md`](../requirements/ARCHITECTURE.md)) | `poc2/requirements/` |
| Extract component | `poc2/requirements/extract/` (contracts in [`../requirements/ARCHITECTURE.md`](../requirements/ARCHITECTURE.md)) | `poc2/requirements/extract/` |
| Requirements Editor | `poc2/requirements/editing.py` (and related) | `poc2/requirements/editor/` |
| Requirements UI | Pages/handlers under `poc2/app/` | `poc2/requirements/ui/` |
| Claims subsystem | `poc2/claims/` (+ [`ARCHITECTURE.md`](../claims/ARCHITECTURE.md)) | `poc2/claims/` |
| Discovery component | `poc2/discovery/` | `poc2/claims/discovery/` |
| Claims Editor / review callables | `poc2/claims/` (e.g. `bind.py`) | `poc2/claims/editor/` (and claims review callables under the Claims subsystem) |
| Claims UI | Pages/handlers under `poc2/app/` | `poc2/claims/ui/` |
| Checks | `poc2/checks/` (+ [`ARCHITECTURE.md`](../checks/ARCHITECTURE.md)) | `poc2/checks/` |
| Checks UI | `check_page` in `poc2/app/pages.py` | `poc2/checks/ui/` |
| Compile | Functions under `poc2/review/` (e.g. `compile.py`); contracts in [`../review/ARCHITECTURE.md`](../review/ARCHITECTURE.md) | `poc2/compile/` (+ its own `ARCHITECTURE.md`) |
| Final review | Same `poc2/review/` tree; contracts in [`../review/ARCHITECTURE.md`](../review/ARCHITECTURE.md) | `poc2/review/` (final review only; compile contracts move out) |
| Review UI | `review_page` in `poc2/app/pages.py` | `poc2/review/ui/` |
| Shared IO / validate / signing | `poc2/common/` | `poc2/common/` |
| Cover / navigation | `poc2/app/` | `poc2/app/` (navigation and integration only) |
| Scaffold (`write_stub`) | `poc2/scaffold/` | **Unresolved** — not in the agreed target tree (see Open questions) |

### Migration (when performed)

Moves are a later, explicit change. When migrating:

1. Move Discovery under `poc2/discovery/` → `poc2/claims/discovery/`.

2. Place Requirements Editor and Claims Editor under `requirements/editor/` and `claims/editor/`.

3. Move subsystem UI out of `app/` into `requirements/ui/`, `claims/ui/`, `checks/ui/`, and `review/ui/`; leave only overall navigation and integration in `app/`. The review page, including its compile action, is the `review/ui/` rendering.

4. Split compile out of the current `review/` tree into `compile/` with its own `ARCHITECTURE.md`; leave final review in `review/`.

5. Update Python imports, package layout, tests, CLI / `__main__` entrypoints, and every documentation reference that still points at the old path.

6. Do not change Packs v2, and do not change subsystem behaviour or callable interfaces merely because a file moved.

## Product ambition and functional baseline

PoC1 is the minimum functional baseline, not the target for PoC2.

PoC2 must preserve the useful capabilities of PoC1 while delivering a substantially more complete, more correct and more maintainable product.

In particular:

- Requirements extraction and discovery hints must be at least as useful and comprehensive as PoC1, with broader coverage, better validation and human-review support.

- Alternative LLM models, prompts and bounded agent strategies must be testable and comparable without changing the Packs v2 domain model.

- Discovery must support improved retrieval and assessment strategies, while keeping human-approved Claims authoritative.

- Requirements and Claims management must support complete workflows, including inspection, correction, editing, signing and subsequent maintenance.

- Checks, compilation and final review must produce trustworthy, traceable and actionable results.

- All subsystem functions must work independently of the graphical UI and be accessible to CLI, CI/CD and tests.

- The graphical interfaces must preserve useful PoC1 workflows and make the expanded capabilities usable.

Architecture cleanup, directory migration and data-model conversion are enabling work, not product milestones in themselves.

**Completion requires demonstrable functional improvements beyond PoC1, verified with comparable source material and realistic end-to-end scenarios.**

Do not change existing subsystem behaviour or interfaces merely to fit the directory layout.

## Data contracts

Packs v2 is the shared persistent domain model and the interface between subsystems. Each subsystem reads and writes those structures directly: Pack, Requirement, repo `curbpack.json`, Claim, the run result, and the review report.

A processing step may keep temporary sections, provisions and model diagnostics. They are not alternate persisted Requirement or Claim schemas. Extract proposes unsigned Requirements with no `origin`; a user previews differences and explicitly applies chosen changes to the configured Requirements working directory. Each run does not create a new working copy. Import preserves an unchanged signed Pack in a configured read-only publication location. Creating an editable local copy of a published Pack uses `origin` according to Packs v2. Downstream Requirements operations read the accepted Requirements directly. No `decisions.json` is needed to replay approved Requirements.

Subsystems do not have to run in one fixed order. Discovery, claim edits, and checks can be repeated after a product change without running Extract again. A changed requirement can lead to new review and discovery. The objects on each side of a boundary stay the same either way. The diagram shows which object a step reads and writes. It is not an execution order, and it does not add a private format on any arrow.

## Data and responsibility map

| Step | Subsystem | Owner / decision maker | Reads | Produces or modifies | Boundary |
| --- | --- | --- | --- | --- | --- |
| Extract source text | requirements (Extract) | Extract operator and legal expert | Legal source; adapter | Proposed unsigned Packs v2 Requirements with `references[]` and `discovery_hints`, and no `origin`; explicitly accepted changes in the selected working directory | Preview before apply; discard leaves working data unchanged; never silently delete missing Requirements or alter imported publications |
| Import published Pack | requirements | Person importing | A published Pack directory for one pack id and version | Identical bytes in the configured imported/publication area | No `origin`. The source is unchanged. The imported directory is not a working copy. Different bytes at that identity are refused |
| Create local working copy | requirements | Legal/domain expert | An imported or own published Pack | Editable contents in a chosen working directory; local Requirements carry Packs v2 `origin` | The published directory is unchanged. The copy is unsigned. Approving it keeps `origin` and does not publish a release |
| Compare working copies | requirements (Compare) | Legal/domain expert | Working contents and a selected snapshot, published Pack, or comparison proposal | Read-only field-level differences; explicitly chosen changes to the destination working copy | The source is unchanged; edited signed objects become unsigned drafts |
| Consolidate requirements | requirements (Consolidator) | Legal/domain expert | Requirements in the selected working copy | One Requirement with combined `references[]`, replacing redundant drafts | Human decision; no separate consolidation domain object |
| Review / edit requirements | requirements | Legal/domain expert | Selected working-copy Requirement; source | Corrected Requirement | Human decision, not an LLM verdict. The object stays a Requirement |
| Validate and sign | requirements | Local approver or publisher | Selected working directory | Validated and appropriately signed Requirement and/or Pack content, using Packs v2 | Signing does not commit, tag, push, distribute, or turn dirty working content into a retrievable release; local acceptance retains `origin` |
| Select applicable collection | (repo config) | Product team | Published Pack | Repository `curbpack.json` selection | Selection is not itself proof of compliance |
| Find candidate evidence | claims (Discovery) | Local QA / engineer | Requirement `discovery_hints`, repo `hunt`, working tree | A candidate list on the Discover job, plus Useful/Poor, checks, and added findings in workspace feedback | Those records are operational. They are not Claims, Requirements, or a domain type |
| Bind and maintain claims | claims | Local QA / engineer | Requirements, the chosen candidate path, product sources | Claims with `requirement_id`, `source`, source `args`, `description`, and `checks[]` | One Requirement may have multiple Claims. One piece of evidence with several Checks is one Claim |
| Seal Claim | claims | Local QA / company key holder | Claim | Same Claim with `signed` set | Signing operation on the existing Claim |
| Evaluate | checks | `curbcheck` or the PoC2 check runner | `curbpack.json`, pack directories, Claim files, the working tree | One run result | [`../checks/ARCHITECTURE.md`](../checks/ARCHITECTURE.md). Read-only evaluation |
| Compile | compile | The person who builds the bundle | That run result, the Requirement files and Claim files it names | One review report in the product repository | Currently specified in [`../review/ARCHITECTURE.md`](../review/ARCHITECTURE.md). Does not run checks. Does not commit |
| Final review | review | Reviewer | The review report | `decision` and `review-sign` on that report | The reviewer's words. Not a check result and not a Claim seal |
| Scaffold | unresolved | Engineer | A relative path in the product repo | A new file on that path | Current code: `scaffold/stub.py`. Refuses to overwrite. Product content, not a Claim or a result. Placement in the target tree is open |

```text

Legal source -> requirements (Extract / edit / seal) -> Requirement + discovery_hints -> Pack

&#x20;                                                             |

Product selection (curbpack.json) -----------------------------+

&#x20;                                                             v

&#x20;                                                   claims (Discovery)

&#x20;                                                             |

&#x20;                                                      Human binding

&#x20;                                                             v

&#x20;                                                            Claim

&#x20;                                                             |

Product content <------ working tree -------------------------+--> checks --> Run result

&#x20;                                                                                      |

&#x20;                                                                             compile / review

```

A failed check may cause a developer to change the product; a moved file may require updating a Claim; an upstream requirement change may lead to new review and discovery. There is no mandatory one-way step after a sealed publication.

## Requirements working directories, signing and distribution

PoC2 operates on **configured filesystem locations**, not on a new timestamped Pack directory per Extract run. Deployment configuration identifies the Requirements working directory, the location of available imported/published Packs, and the Claims working directory. These may belong to different repositories or be outside Git altogether; configuration is not a Packs v2 field. The working directory is writable and may contain uncommitted changes. Published/imported Pack contents are kept unchanged and distinct from writable working content. Path layout, selection, write isolation and validation details belong in the relevant subsystem architecture.

**Repository ownership** is a design decision of 21 October 2026. It assigns those existing locations. It does not add a Packs v2 field, a report database, or a version model, and it does not change the Requirements working-copy contract.

| Repository | Who | What is versioned there |
| --- | --- | --- |
| Packs repository | The publisher, for example RISE | Signed Requirements and Packs. A layout such as `packs/cra/` and `packs/nis2/` is an example, not a new schema. Many product repositories can use the same Pack. |
| Product repository | The product owner | Product code, `claims/`, `curbpack.json`, and the durable review reports under `docs/reports/`. |

`curbpack.json` in the product repository names the Pack id and version that product uses. The Pack bytes stay in the publisher's repository. Deployment configuration, already outside Packs v2, says how the process reaches those Pack directories and which product-repo path receives the durable report. A later named setting must extend that existing configuration explicitly.

`.curbpack/` in the product repository is temporary working data, including the run result. The durable report is specified in [`../review/ARCHITECTURE.md`](../review/ARCHITECTURE.md). Compile and `review-sign` do not create a Git commit. The user may commit the report afterwards. That commit is a later revision of the product repository. It is not the code revision the report describes.

A dirty worktree remains allowed. The report must not present the recorded commit as the sole content that was checked. That distinction is the review contract's reading of `worktree`, not a new field.

**Extract** uses a developer-maintained deterministic legal-source adapter for segmentation. Its model-based stages produce unsigned Requirements proposals with `references[]` and `discovery_hints`, without `origin`. A run stages proposals outside authoritative working Pack files; the UI shows added, changed, and apparently missing Requirements against the current working content before explicit application or discard. An absent result is not permission to delete a Requirement. A rejected proposal changes nothing. Users can repeat extraction with different inputs or models without allocating another Pack working copy. Legal provisions that were not processed must remain visible for review. Model diagnostics and provisional outputs stay outside signed Pack directories. `decisions.json` is not a second authority for accepted Requirements.

**Import** reads a published signed Pack, validates/reads its seals as defined by Packs v2, and copies the published bytes unchanged into a configured imported/publication location. Import does not set `origin`. Reimporting identical content is harmless; conflicting bytes under the same identity are rejected. The source and imported snapshot remain unchanged. Import is not an edit, a Git fork or a new publication.

**Create local working copy** copies a chosen published Pack into a configured writable directory, with Packs v2 `origin` applied to local Requirements as specified by the normative contract. The source remains intact and its publisher's signature does not automatically approve the local copy. There is no mandated timestamp naming scheme or automatic Git branch. A locally accepted Requirement keeps `origin`. Conversion into a separately issued publisher Pack is a distinct, out-of-scope operation, never an implicit removal of `origin`.

**Compare** is read-only until the user explicitly applies chosen changes to the working directory. It can compare working content against an imported publication, a saved comparison source, or Extract proposals, including additions, modifications, apparently missing Requirements and consolidation cases. **Consolidator** proposes overlapping Requirements; consolidation is a human decision that updates selected writable content and its `references[]`, not an automatic deletion from published or imported sources. Detailed matching and operations belong in `requirements/ARCHITECTURE.md`.

**Validate & Sign** is the pilot's terminal Requirements operation. It validates and signs the applicable Requirement and Pack objects according to Packs v2, including the distinction between a locally accepted Requirement with `origin` and a publisher Requirement without it. Only content actually covered by a verified signature may be described as signed. Applying fresh extraction proposals to a local copy with `origin` must not silently erase its provenance or turn that copy into a publisher Requirement. Temporary proposals and diagnostics must not be included unintentionally in the Pack directory seal. Signing does **not** create a Git commit, tag, immutable published release, remote distribution or evidence of organisational authorisation. After successful verification the UI may recommend that the user commit the exact signed content and retain its Git revision identifier. An uncommitted or later-modified working tree must never be presented as a reproducible published release. The existing separate publication implementation is retained for compatibility but is **not part of the pilot's required UI workflow**; its semantics remain governed by Packs v2 until explicitly redesigned.

**Git is optional external revision management.** Users manage commits, branches, tags, restoration, remotes and distribution independently of PoC2. PoC2 must neither require Git for normal editing/signing nor manipulate the user's HEAD, commit, tag, or push as a side effect of these actions. A Git commit identifies only committed bytes; dirty changes do not belong to that commit. Historical checks by Git revision may be added later as an isolated read of that revision, with signature verification and without switching the active working tree. This future check capability is not a requirement of the current Requirements pilot.

## Workflow words

Candidate, selected, draft, and unsigned are UI and workflow concepts. They are not automatic reasons for additional domain types. The domain object is still a Requirement, a Claim, a Pack, a repo `curbpack.json`, a run result, or a review report.

- **Candidate** — A path Discovery shows for inspection, or a repository file a person adds by hand. The Discover job and workspace feedback keep that list. It is not a Claim. Useful or Poor and configured checks live in feedback. A candidate may have zero checks. Adding a check writes one Claim for that evidence when that Claim id is absent.

- **Draft** — A Requirement, Claim, pack, or review report that has not been sealed. It has the same fields as the sealed object. Editing a sealed object removes `signed` and leaves an unsigned draft of that same object.

- **Unsigned** — The object has no applicable signature. An edit to a sealed object removes `signed`, making the edited version unsigned.

- **Selected** — The product repo lists a published pack in `curbpack.json`, or a person has picked a candidate path while binding a Claim. Selection is not a separate stored object or a check result.

- **Signed** — A specific version of a Requirement, Claim, pack, or review report has been cryptographically signed. The object retains its existing data structure.

There is no Candidate schema and no ClaimDraft schema.

## Implementation boundaries

- **common/**: small, explicit functions that load, validate, and persist Packs v2 objects, plus shared signing helpers. The same object shape is read and written by Extract, editors, and downstream tools. The old top-level fields `law_text`, `search`, and `claim` are forbidden on a Requirement. `references[].law_text` is required, as `packs2.md` specifies.

- **requirements/**: Extract and proposal review/application, import of published Packs, configured working content, Compare, Consolidator, Requirements editing and human review, validation and signing, and the Requirements UI. It does not perform product discovery, create Claims, evaluate checks or manage Git history and distribution. Details: [`../requirements/ARCHITECTURE.md`](../requirements/ARCHITECTURE.md).

- **claims/**: Discovery, Claims editing/rebinding/review, sealing Claims, and the Claims UI. It must not rewrite publisher Requirements merely to bind product-specific evidence. Details: [`../claims/ARCHITECTURE.md`](../claims/ARCHITECTURE.md). Current Discovery code remains under `poc2/discovery/` until moved.

- **checks/**: [`../checks/ARCHITECTURE.md`](../checks/ARCHITECTURE.md). The runner executes each entry in `checks[]` and writes one run result.

- **compile/**: builds the review report from a run result. Does not run checks. Until split, contracts remain in [`../review/ARCHITECTURE.md`](../review/ARCHITECTURE.md).

- **review/**: final human review — `decision` and `review-sign` on the report. Does not run checks. Claim sealing stays in Claims.

- **app/**: overall navigation and integration only, including the HTTP entry. The boundary is [HTTP server](#http-server). Not the owner of all subsystem UIs.

- **UI (every subsystem):** strictly presentation and interaction. UI modules render view models, collect input, call use-case functions, and display their results. No filesystem traversal, direct JSON mutation, schema migration, check execution logic, approval rules or business decisions inside UI callbacks. Until migration, several pages still live under `poc2/app/`; that is current layout, not the target ownership rule.

- **Scaffold:** current `write_stub` in `poc2/scaffold/`. Target subsystem placement is unresolved.

The same services/functions should be callable from tests and CLI without starting the UI. Avoid service layers that merely forward a call or wrappers with no clear consumer.

## HTTP server

The HTTP server is a replaceable transport adapter. It dispatches by URL prefix and owns shared response helpers and authentication integration. Each subsystem owns its handlers: form parsing, the call to its operations, and its page. The server does not implement a subsystem workflow. Business operations, domain validation, authorization enforcement, persistence, and signing must remain callable independently of the HTTP framework. Replacing the server with FastAPI and an OIDC-based authentication layer must not require changes to subsystem business logic or Packs v2 data contracts.

Local single-user operation with configured filesystem paths requires no OIDC or organisation service. Optional customer-hosted FastAPI/OIDC deployment can authenticate employees and resolve authorised organisation-specific workspaces; it is not a requirement for local PoC2 and does not impose a shared organisation Git repository as the product data model. PoC2 does not implement OIDC, organisation management, employee management, or repository provisioning. Local Discovery, indexing, prompts, model inference and code-bearing diagnostics must remain inside the authorised environment holding the product code by default; no automatic transmission of source code or code excerpts to a central service. PoC2 does not add a plugin system, a server interface, or an adapter factory for web servers. Local installation keeps the current HTTP entry, `poc2/app/server.py`. Check this boundary when specifying each subsystem. Subsystem operations stay ordinary Python calls that tests, the CLI, and a later server can use without change. The subsystem handler parses its own form, calls those operations, and returns the page. `app/server.py` turns that result into the HTTP response. Existing URLs stay. Do not add an authorization framework to meet this rule. Where the product already decides who may publish, seal, or review, that decision stays in the function the server calls. The employee identity and the Git author string do not sign a Requirement or a Pack.

## Data contracts and storage

- Write **one authoritative persisted representation** of each Packs v2 object. Subsystems read and write that representation directly. Do not maintain both old YAML Requirements and new JSON Requirements as active truth, and do not persist a second Requirement or Claim shape beside it.

- Validate at write boundaries and load boundaries, with errors that identify object, field and expected type.

- Extract proposes unsigned Requirements without `origin`; only accepted changes reach the configured writable directory. Import retains an unchanged published Pack. A local editable copy of that Pack carries `origin` as specified by Packs v2. Editing and consolidation affect only chosen working content. Local acceptance signs a Requirement while retaining `origin`; issuer publication remains a distinct Packs v2 operation, outside the required pilot UI. No implicit conversion between these operations is allowed.

- An unsigned object and a sealed object are the same type. Do not silently alter an original signed Pack or pretend a copied or modified object retains its publisher signature.

- Preserve source-specific `source` + `args` access contracts separately from Requirement's `source` (the legal instrument). Claim `source` uses that same adapter namespace. Check `args` are a different object, inside `checks[]`.

- A run result is persisted as the agreed run result. The review report is the one object specified for compile/final review. A candidate is not persisted. Do not store a simulated result as if a check had run.

- Git metadata describes a Git-backed check run; do not impose Git semantics on non-Git sources.

## Verification architecture

For every migrated component, verify: (1) it reads a Packs v2 fixture; (2) it performs its real task; (3) it writes/returns the expected data shape; (4) round-trip editing preserves unrelated fields; (5) it works through direct calls without UI; and (6) errors are explicit. End-to-end verification uses a controlled sample product and at least one Requirement with multiple Claims, a missing file failure, and a clean/dirty run where supported.

Do not equate a green structural check with the legal Requirement being fulfilled. Keep human review explicit. The Annex VII point 3 path is the acceptance criteria in `doc/END_TO_END_SCENARIO.md`. The product scenarios below add the paths that cross several subsystems.

## Subsystems stay independent

Packs v2 objects are the interface. A subsystem reads the object the previous writer left and does not require that the UI visited an earlier page. A missing file is that subsystem's error.

| Producer | Object | Consumer | Also usable when |
| --- | --- | --- | --- |
| Extract | Proposed unsigned Requirements without `origin`; accepted changes in configured working content | Requirements Editor, Compare and Consolidator | Diff/review and explicit apply or discard; no automatic removal or overwrite of published content. |
| Import | An unchanged published Pack directory | Create local working copy; Discovery and checks when a product repo selects that Pack | The source publication is unchanged. The imported directory is not writable. |
| Create local working copy | Configured editable contents with Packs v2 `origin` | Requirements Editor, Compare, Consolidator, and local acceptance | The published source is unchanged. Approval keeps `origin` and does not publish a release. |
| Compare / Consolidator / Editor | Updated Requirements in selected working directory | Local acceptance or publisher-signing operation, respecting `origin` | Original comparison sources remain unchanged; consolidation does not leave redundant published Requirements. |
| Requirements seal / pack seal | Requirement and `pack.json` | Discovery, checks | Verified signing does not itself publish or commit. Discovery and checks load the Pack directory selected by `curbpack.json`. |
| Discovery | Candidate list on the Discover job; Useful/Poor, checks, and added findings in workspace feedback | Researcher pages, then explicit Claim creation | The job and the feedback file are not Claims. Create writes a new Claim and does not overwrite an existing one. An unsigned Claim can be evaluated. |
| Claims Editor | Claim file | Check runner | `python -m checks` reads the directory and does not call discovery. |
| Check runner | Run result file | Compile | Compile loads that file and does not call the runner. |
| Compile | Review report file | Final review | A reviewer can open the file with `load_report`. Signing it does not run checks. A later completed report lists every unsigned Claim and every Claim whose signature does not verify, with Requirement ids, in an appendix. That appendix does not change check results and is not implemented in the researcher workflow. |
| Final review | `decision` and `signed` on that report | A later reader | The Requirement, Claim, and pack files are unchanged. |

A product change is a new check run. A new sealed Requirement is a Requirements save and, when the person wants it, a new discovery. None of those restart Extract. The cover page links to each area and does not order them.

**Review of failed evidence (cross-subsystem contract).** Review shows the failed Claim, its existing Checks and the Requirement. From that context a user opens **the existing Discovery for that one Requirement in a popup**; the failed Claim remains visible in the underlying Review view. Discovery searches as usual and neither reads nor changes Claims. A presentation-only hook, supplied with the applicable Check run and existing Claims, **greys out** candidate evidence already covered by a matching Claim with passing Checks for that Requirement. It does not remove candidates, alter ranking, modify the discovery job, or declare compliance. With missing, stale, ambiguous or failing Check coverage, the candidate is not greyed. The user inspects candidates and their suitable Checks, explicitly **adds one or more new Claims**, then **deletes the old Claim if it has truly been replaced**; nothing is implicitly replaced or retired. Checks are rerun, new Claim(s) can be reviewed/signed, and final Review records/signs its separate human decision. Discovery never executes Checks or creates Claims. No new Finder/Reconcile/Relocate component, domain type or parallel workflow record is introduced. Details and UI acceptance belong to [`../claims/ARCHITECTURE.md`](../claims/ARCHITECTURE.md), [`../review/ARCHITECTURE.md`](../review/ARCHITECTURE.md) and the Review acceptance scenarios.

`same_run` and the section-progress row are computed on read. The cover does not write them, and it does not keep a workflow file. PoC1's `state.json` and `scan.json` are not inputs.

## Cover page

The front page is `workflow.snapshot` plus links. `snapshot` reads pack directories, the product repo's Claim files, the run-result path, and the report path. It returns a view model and writes nothing. That cover belongs in `app/` as navigation/integration. Linked pages are owned by their subsystems (target); several still render from `app/` today (current).

| Shown | Source |
| --- | --- |
| Each pack: `id`, `version`, and the `read_pack_seal` reading | The pack directory |
| Requirements: how many files, how many readings verify, how many are unsigned | `read_signature` on each Requirement file |
| Claims: how many files, how many `read_claim_seal` readings verify | `load_claims` and `read_claim_seal` |
| Run: absent, or the exit code from `process_exit_code`, the pass / fail / skipped counts, `commit`, and `worktree` | `load_run_result` |
| Report: absent, or the report reading and whether `same_run` is true | `load_report` and the run result |

The counts are not a second copy of those objects. A missing run result is the line "No run result." The link to Check stays.

| Link | Page |
| --- | --- |
| Requirements | The catalog / editor / review in [`../requirements/ARCHITECTURE.md`](../requirements/ARCHITECTURE.md) |
| Discover | Discovery in [`../claims/ARCHITECTURE.md`](../claims/ARCHITECTURE.md) |
| Claims | The Claims editor in that document. Claim sealing is the Claim review surface linked from the editor. |
| Scaffold | The stub form. It calls `write_stub`. Placement of scaffold in the target tree is open. |
| Check | The check page in [`../checks/ARCHITECTURE.md`](../checks/ARCHITECTURE.md) |
| Review | Compile and final review; currently [`../review/ARCHITECTURE.md`](../review/ARCHITECTURE.md) |

The demo's prepare action loads a fixture workspace. It is not a subsystem activity, and the other pages do not call it. The current `snapshot` reads only `CRA-ANNEX-VII-RISK.json`. The target contract is the table above; it must read the configured working content or an available published Pack where applicable.

## Product acceptance scenarios

Each scenario uses the contracts already named. Domain checks call the functions. UI checks render a page or post a form and assert which function ran. The Annex VII point 3 criteria in `doc/END_TO_END_SCENARIO.md` stay the test for that single-provision path.

1. **Several Annex VII provisions.** A deterministic CRA adapter identifies every locus in the controlled source. Extract proposes unsigned Requirements for explicit review and application in the configured working directory, including correctly mapped `references[].law_text` and `discovery_hints`. The user can edit multiple Requirements; no existing Requirement is removed or overwritten merely by running Extract.

2. **New extract, no automatic overwrite.** An Extract run previews additions, changes and apparent removals against current working content. Discard leaves that content byte-for-byte unchanged. Apply changes only the explicitly selected Requirements. A second run can be compared with that content without requiring a new working-copy directory. Published/imported Packs remain unchanged.

3. **Human editing and consolidation.** The person edits a Requirement and consolidates two drafts into one Requirement containing both source references. The redundant draft is removed from the accepted working content only after human confirmation. A new extraction proposal leaves that work untouched unless accepted. A later comparison handles the consolidated Requirement against multiple new proposals without silently replacing it.

4. **Another model or prompt.** A new extraction with changed model/prompt settings creates a fresh proposal, not another Pack working-copy directory; model notes remain diagnostics. Comparison exposes differences against current working content before application. Claims and run results do not change until their respective downstream operations are invoked.

5. **One Claim, several Checks.** `exist` and `contents` on the same evidence are two entries in that Claim's `checks[]`. The run result has one row and two indexed Check results. A second Claim is other evidence for the same Requirement. A Claim with no Checks reloads and is omitted from the run. Retiring a Claim removes that file. Rebinding a path drops that Claim's `signed` and leaves the Requirement digest unchanged.

6. **Fail and skipped.** A missing file is `fail` on every Claim that names it, including `contents`, and the `contents` detail does not add a header miss. A header that `args` still names is `fail` until `args` change. `skip` with a reason yields `skipped` and exit 1. An empty reason writes nothing. A result with no rows exits 1. Exit 0 requires at least one row and every row `pass`. A dirty tree can still exit 0, and the check page states that the result is not verification of that commit's content.

7. **Compile and a signed review.** Compile embeds the run result and the Claims whose digests match the rows. `record_decision` stores the reviewer's sentence, including a sentence that currency of the assessment is a different Requirement. `sign_report` verifies as `review report` for the reviewer's key. That version digest differs from the Requirement seal and from each Claim seal. The report has no key for a conclusion that the product meets CRA. A later run leaves the report file in place until the person compiles again.

8. **Through the UI.** The user selects the configured Pack working location before reviewing Requirements, and may review an Extract diff, accept or discard it, and open Compare or Consolidator. The cover shows the snapshot lines and links to every page above. Opening Check without opening Extract still runs when the repo, the packs, and the Claims exist. The section page lists every Annex VII locus from stage 01. The Claims page saves two Claims for one Requirement. Check shows both rows. Review compiles, saves a decision, and signs. The cover then shows the report reading and a `same_run` line, and the Requirement file's bytes are unchanged by that signing.

 
 

9. **Local signing and external Git.** On a filesystem directory without Git, Requirements validation and signing work according to Packs v2 and display accurate verification status. On a dirty Git working tree, signing does not commit or tag anything and does not imply that the current bytes are retrievable by a commit hash. The UI recommends an explicit user-managed commit after successful signing. No Publish action is required to complete the pilot flow.

10. **Failed Claim → existing Discovery popup → explicit replacement.** Run Checks on C1 and C2 for Requirement R1; C1 fails while C2 passes. Review displays C1 and its failing Checks and opens Discovery for R1 as an overlay without discarding that context. Discovery produces the normal candidate set. The UI greys matching evidence already covered by C2's passing Check(s), without removing it from the results; C1's old path or any ambiguous, unchecked, skipped or failed candidate is not incorrectly greyed. The reviewer chooses new evidence, adds one or more Claims with appropriate Checks, explicitly retires C1 *after* confirming replacement, reruns Checks, reviews and signs the new Claim(s), and separately signs the final report. Canceling the popup or failing to find replacements changes no Claim. Neither the Discovery core nor the Check runner needs a new mode or persistent state.

**Scaffold (deferred).** `scaffold/` remains an optional top-level subsystem. Its intended role is to use check results, Requirement `remediation_hint`, and optionally a library of templates or documents to propose remediation. Documentation scaffolding is the primary plausible use case. Scaffold is not part of the required verification workflow, and no broader automatic remediation capability is committed. Its detailed architecture and implementation are deferred until a concrete use case justifies them.
