# Discovery & Claims — subsystem architecture

Status: **normative target; implementation gaps are identified explicitly.**  
Normative domain model: `docs/reference/packs2.md` in this repository.
Sibling documents (`docs/arch/ARCHITECTURE.md`, `policies/working-rules.md`, `docs/concepts/end-to-end-scenario.md`) describe the wider product. This file owns Discovery and Claims under `poc2/claims/`; some current code is still in `poc2/discovery/` until migration.

Extract is out of scope. Do not change Extract’s implementation or architecture from this document.

`poc/` is a behaviour reference only. PoC2 does not import it at runtime.

---

## 1. Purpose

`curbpack-claims` finds possible evidence locations, maintains product-specific Claim bindings, and lets humans approve and seal those Claims. It implements the durable product loop in Packs v2 §6 without treating discovery as verification and without inventing parallel domain types.

**Claims Review** here is human inspection and signing of Claims. It is not `curbpack-review`, which reviews compiled evidence and check run results.

---

## 2. Three modules

Three distinct, independently testable responsibilities. They do not require three processes, frameworks, or necessarily three directories. UI stays presentation and interaction only.

| Module | Responsibility | Not responsible for |
| --- | --- | --- |
| **Discovery** | Source access, candidate retrieval, and optional assessment; return temporary candidates from `discovery_hints` and `hunt`. The Discover job file and workspace feedback file are operational records of that run and of researcher marks. They are not Candidates-as-a-type, not Claims, and not Requirements. | Creating, editing, or signing Claims; evaluating checks; persisting Candidates as a domain type; mutating Requirements or Packs |
| **Claims Editor** | Create, edit, rebind, and retire Claims | Discovery search; Claim sealing; Requirement edits; check execution |
| **Claims Review** | Human inspection of Claims against the Requirement; approval and signing | Discovery; rewriting Claim `source`, source `args`, or `checks` (that is Editor); `curbpack-review` reports; run results |

Workflow words **candidate**, **selected**, **draft**, and **approved** label UI state. They are not persistent types. An unsigned Claim is still a Claim (`signed` absent).

Shared infrastructure (not a fourth product module): `common.validate`, `common.store`, `common.signing`, and check-args validation. Editor and Review call these; they do not reimplement them.

---

## 3. Persistent Packs v2 structures (used as-is)

`packs2.md` is authoritative. No competing Requirement, Claim, or evidence models.

### 3.1 Requirement (read-only for binding)

Discovery, Editor, and Review **read** Requirements. Product-specific binding changes never rewrite them.

| Field | Why necessary |
| --- | --- |
| `id` | Join key for `Claim.requirement_id` |
| `discovery_hints` | Hunt guidance (`concepts`, `path_hints`, `sources`, `expected_evidence`) |
| `references[].law_text` | Human inspection context; not a search key for the deterministic walk |
| `pack_id` | Confirms the Requirement belongs to a pack selected in `curbpack.json` |

Editing `discovery_hints` is a Requirements concern, not Claims.

### 3.2 Repo config (`curbpack.json`)

| Field | Why necessary |
| --- | --- |
| `packs` / `requirements` / `exclude_requirements` | Which Requirements are in scope |
| `hunt.sources` | Default reach list when the Requirement omits `discovery_hints.sources` |
| `hunt.exclude_path_globs` | Paths discovery must skip |
| `hunt.prefer_path_globs` | Prioritize candidates **already found**; never invent candidates alone |

### 3.3 Claim (the only durable binding)

```json
{
  "id": "claim-risk",
  "requirement_id": "CRA-ANNEX-VII-RISK",
  "source": "documents",
  "args": { "path": "docs/security/risk_assessment.md" },
  "description": "The reviewed file is the evidence for this Requirement.",
  "severity": "high",
  "checks": [
    { "check": "exist", "args": { "paths": ["docs/security/risk_assessment.md"] } },
    { "check": "contents", "args": { "path": "docs/security/risk_assessment.md", "probes": [] } }
  ],
  "signed": { "at": "…", "name": "…", "signature": "…" }
}
```

`source` uses the same adapter namespace as `discovery_hints.sources`. It is not `Requirement.source`. Source `args` identify the evidence. Each `checks[]` entry is `{check, args}` validated by `available_checks.json`. A path inside a Check's `args` is not the Claim's evidence locator. `checks: []` is a saved proposal: it reloads, it is not executed, and it is not published. An unsigned Claim with Checks may be tested. The seal covers the whole Claim, including `source`, source `args`, `description`, and every Check. It does not cover the external file bytes.

| Field | Why necessary |
| --- | --- |
| `id` | Stable evaluation and storage key |
| `requirement_id` | The one Requirement this Claim supports |
| `source` | Adapter id for the evidence, same namespace as hunt sources |
| `args` | Adapter-specific locator for that evidence |
| `description` | Human rationale. Checks do not read it |
| `severity` | Optional product triage (`high` / `medium` / `critical`); not legal `strength` |
| `checks` | Zero or more configured Checks |
| `signed` | Optional seal; absent ⇒ unsigned Claim |

Forbidden on Claims (Packs v2): `remediation`, `expected`, `settlement`, and Requirement fields such as `law_text` or `search`. No `retired` field. No top-level `check`.

Several Claims may share one `requirement_id` when they are different evidence. The same evidence with several Checks is one Claim. Creating a Claim does not overwrite an existing file. Traceability across reruns is that file: same `id`, updated source `args` or `checks` when the binding changes. A changed signed payload drops `signed`.

On disk: one JSON file per Claim (PoC2: `claims/<id>.json`). Packs v2 names the layer `CLAIMS/`; the directory name is packaging, not a second schema.

---

## 4. Data passed between modules

Minimum hand-offs. No duplicated Claim or Requirement copies, no candidate store.

| From → To | Data | Why |
| --- | --- | --- |
| Caller → **Discovery** | `repo` path, loaded Requirement, loaded `curbpack.json`, optional strategy selection (§8.1) | Hunt merge, access, retrieval, optional assessment |
| **Discovery** → caller (UI / tests) | `list[Candidate]` (temporary) | Inspection only; never a Claim |
| Caller → **Discovery** | One returned Candidate | `read_source_text` (§6.1) returns that locator's text. Not stored |
| Caller → **Claims Editor** | Human field values; optional repo-relative `path` string (e.g. from a Candidate) to prefill source `args` | Binding input; path alone, not a persisted Candidate |
| **Claims Editor** → disk | Packs v2 Claim JSON | Sole durable binding |
| Caller → **Claims Review** | Loaded Claim(s), loaded Requirement (for law text), trust material for seal reading | Inspection and seal |
| **Claims Review** → disk | Same Claim object with `signed` set (or left unsigned) | Packs v2 seal; no parallel approval record |

Discovery's **retrieval and assessment functions** do not read or write Claims. A caller rendering Discovery may separately load Claims and a Check run to compute a **presentation-only coverage annotation**. This annotation never enters candidates persisted on the job or feedback, changes neither candidate retrieval nor scoring, and never makes a Claim. Claims Review does not run discovery. Editor does not seal; Review does not invent `source`, source `args`, or `checks`.

---

## 5. Hunt merge (Packs v2 §2.3 / §2.7)

| Input | Source | Rule |
| --- | --- | --- |
| `concepts` | `discovery_hints` | Requirement only; identifies candidates |
| `path_hints` | `discovery_hints` | Requirement only; identifies candidates |
| `expected_evidence` | `discovery_hints` | Stored; not a match key for the current walk |
| `sources` | `discovery_hints.sources` if present, else `hunt.sources` | Requirement wins when set |
| `exclude_path_globs` | `hunt` | Filters before identification |
| `prefer_path_globs` | `hunt` | Orders already-identified candidates only |

`requirement.source` (legal instrument) is unrelated to hunt `sources` (reach).

---

## 6. Discovery pipeline (replaceable strategies)

Discovery is one module with four activities. The first three are independently replaceable and testable. The fourth is the existing human boundary into Claims Editor — not a Discovery strategy.

| Step | Activity | Job |
| --- | --- | --- |
| 1 | **Source access** | Reach material for each effective `{source, args?}` entry |
| 2 | **Candidate retrieval** | Identify possible evidence from that material using a configured method (default: deterministic path/concept search) |
| 3 | **Candidate assessment** | Optionally rank, inspect, or refine the retrieved list (LLM, embeddings, or a bounded agent loop) |
| 4 | **Human inspection → Claim binding** | Only human-accepted choices become persisted Claims (Editor); Discovery never writes Claims |

`source` + `args`, `discovery_hints`, the Claim contract, and human approval stay unchanged. Strategies do not invent a second domain model. Output of steps 1–3 remains temporary. Durable binding remains the Packs v2 Claim.

No general agent framework, connector platform, or plugin registry. Each strategy is an ordinary callable with a fixed input/output shape. Swap it in tests by passing a different callable or strategy id.

### 6.1 Source access

Each hunt source entry is `{ "source": "<id>", "args": { … } }` with `args` omitted when unused (Packs v2).

```text
access_source(repo, source_entry) → list[str]
  # repo-relative locators (or equivalent for that source)
  # or explicit unsupported / failure — never a silent empty “success”
```

Return plain path strings. Do **not** wrap them in a `Material` (or similar) type unless a reach actually needs extra fields or behaviour beyond a locator.

```text
read_source_text(repo, locator) → str
```

`locator` is a path this reach already returned: a string from `access_source`, or `path` on a Candidate from `discover_candidates`. Retrieval and assessment call it when they need the body. The discovery page calls it for the Candidate the person selected and renders the returned text. The page does not open the path itself. The call does not search, list a directory, write, or store. A locator that escapes the repo fails. An unreadable locator fails with that error; it is not an empty success. The current walk's locators are repo-relative markdown paths, and this read returns that file's text. It does not consult `source` or `args`, the same stopgap as the walk.

**Selection:** effective source list from §5. Call one access function per entry.

**When source selection is implemented:** unsupported source IDs must fail or signal unsupported explicitly. They must not look like “searched, found nothing.”

**Current limitation (not product intent):** PoC2’s markdown working-tree walk does not yet honour `source` / `args`. That fused walk is a stopgap for access+retrieval, not the finished split.

### 6.2 Candidate retrieval

```text
retrieve_candidates(
  paths: list[str],           # from access_source (and any prior filtering)
  requirement: Requirement,   # uses discovery_hints
  hunt: hunt object,          # exclude / prefer only
  *,
  limit: int = 40
) → list[Candidate]           # core fields only; no assessment fields required
```

Default strategy: **deterministic path/concept retrieval** (§7.3). Other retrieval methods (e.g. index-backed search) must accept the same inputs and return the same Candidate core shape so they can be compared on controlled fixtures.

Retrieval does not write Claims, Requirements, or Packs. It does not require an LLM.

### 6.3 Candidate assessment (optional)

```text
assess_candidates(
  candidates: list[Candidate],
  requirement: Requirement,   # law_text / references for inspection context
  *,
  args: dict                  # strategy-local only (model name, limits, …); not persisted on Claim
) → list[Candidate]           # input paths reordered, subset, or left as-is; optional assessment fields filled
```

Assessment is optional. Omit it for the reproducible default path.

Reuse PoC1 LLM scoring (`poc/components/cra_evidence_hunt/hunt.py` score prompt / JSON `score` / `rank` / `why` / excerpt) as one assessment strategy when useful. Embeddings or a **bounded** agent loop are other optional strategies with the same I/O. None of them may create Claims, edit Requirements or Packs, or overwrite approved Claim files.

Assessment must not be required for binding. A human may bind from retrieval-only candidates.

The researcher Discover job runs assessment after retrieval, bounded by `assess_limit` (default 5, allowed range 0–20) per Requirement per run. Candidates beyond the cap stay in the returned list with assessment fields omitted and are labeled not assessed. A failed or skipped call does not remove the candidate. A finished assessment with score 0 or rank None is omitted from that list and kept on the job so a later run does not score it again. Binding from a retrieval-only candidate remains valid. The score control explains that method: one model call, temperature 0, the requirement text and the first 12,000 characters, with current product material and risk assessment weighed above roadmap text and a bare mention of security. The number is not a check result.

### 6.4 Orchestration

```text
discover_candidates(
  repo, requirement, config,
  *,
  limit: int = 40,
  retrieval: strategy = deterministic_path_concept,
  assessment: strategy | None = None,
  assessment_args: dict | None = None
) → list[Candidate]
```

1. Merge hunt inputs (§5).
2. For each source entry: `access_source` → paths (fail on unsupported).
3. `retrieve_candidates` → candidates.
4. If `assessment` is set: `assess_candidates` → refined list.
5. Return temporary candidates. The Discover job file stores that return value. Workspace feedback stores Useful/Poor marks, configured checks, and findings a person added. Neither file is a Claim, a Requirement, or a signature.

### 6.5 Configuring, evaluating, and comparing strategies

Strategy choice is **run configuration** for Discovery (CLI flags, test parameters, or an ephemeral tool config). It is not a Packs v2 field on Requirement, Claim, or Pack, and it does not belong in sealed payloads.

| Concern | Rule |
| --- | --- |
| **Configure** | Select `retrieval` and optional `assessment` (+ `assessment_args`) at the call site |
| **Evaluate** | Call the strategy functions directly in tests — no UI |
| **Compare** | Same controlled product tree, same Requirement, same `hunt`; change only the strategy under test; compare Candidate path sets, order, and optional assessment fields |
| **Baseline** | Deterministic retrieval without assessment is the reproducibility baseline |
| **Safety** | After any strategy run, Claim / Requirement / Pack files on disk must be byte-identical to before |

Throwaway debug dumps of candidate lists are allowed for comparison; they are not a domain store and must not be treated as Claims.

---

## 7. Temporary structure: Candidate

Shared temporary structure for retrieval and assessment. Not a persistent domain type.

### 7.1 Shape

```text
Candidate = {
  path:       string                 # required — locator proposed for inspection
  matched_by: string                 # why retrieval identified the path; deterministic uses "path_hint" | "concept"
  excerpt:    string                 # inspection aid; may be filled by retrieval or assessment
  # optional — only when assessment ran:
  score:      float                  # relative strength from the assessment strategy
  rank:       string                 # e.g. PoC1 High|Medium|Low|None
  why:        string                 # short assessment rationale for the human
}
```

| Field | Why necessary |
| --- | --- |
| `path` | What the human inspects and may bind into Claim `args` |
| `matched_by` | Explains retrieval; not stored; keep short |
| `excerpt` | Cheap inspection context |
| `score` / `rank` / `why` | Optional assessment output (PoC1-compatible); presentation only; never copied onto a Claim |

Omit assessment fields when assessment did not run. Do not add model name, votes, timestamps, or requirement copies — those recreate PoC1’s persisted findings store. Prefer ordering stays sort metadata during retrieval, not a `matched_by` value and not a Candidate field.

The Discover job record may store, per candidate, `assessment_state`, `assessment_error` or `assessment_skip`, `model_excerpt`, `model_excerpt_verified`, and the hashes of law text, file body, model, and prompt. Those fields support resume and display. They are not Candidate domain fields and they are not copied onto a Claim. `excerpt` stays the retrieval excerpt.

### 7.2 Lifecycle

| | |
| --- | --- |
| **Producer** | Retrieval (core fields); assessment may add optional fields and reorder |
| **Consumer** | UI/CLI; human may pass `path` into Claims Editor |
| **Persistence** | None as a domain type. The Discover job file stores this run's return value, including assessment fields and resume hashes. |
| **Lifetime** | Call return value / ephemeral view-model |

### 7.3 Deterministic retrieval semantics (default strategy)

1. Apply `exclude_path_globs` to paths from source access.
2. **Identify** candidates only via `path_hints` and/or `concepts`. A path that matches neither is not a candidate, even if it matches `prefer_path_globs`.
3. **Order** identified candidates: `path_hint` before `concept`; within each band, paths matching `prefer_path_globs` before those that do not; then stable sort by path.
4. Cap with an explicit `limit`.

Same controlled paths + same hints + same hunt ⇒ same Candidate core list for this strategy. Assessment, if enabled, may change order or optional fields afterward and is not part of this reproducibility guarantee.

---

## 8. Module interfaces

Each function is callable from tests and CLI without the UI. Reuse `common.validate`, `common.store`, `common.signing`, and check-args validation.

### 8.1 Discovery

```text
access_source(repo, source_entry) → list[str]   # paths; no Material wrapper
read_source_text(repo, locator) → str            # §6.1; one returned locator, not a path the person typed
retrieve_candidates(paths, requirement, hunt, *, limit=40) → list[Candidate]
assess_candidates(candidates, requirement, *, args) → list[Candidate]   # optional strategies
discover_candidates(repo, requirement, config, *, limit=40,
                    retrieval=…, assessment=None, assessment_args=None) → list[Candidate]
```

- Does not write Claims, Requirements, or Packs.
- Does not run checks.
- Presentation of the list is UI/CLI, not these functions.
- Human binding remains Claims Editor (§8.2), using at most a `path` string from a Candidate.

### 8.2 Claims Editor

```text
build_claim(*, claim_id, requirement_id, source, args, checks, description, severity=None) → Claim  # unsigned
rebind(claim, *, source=None, args=None, checks=None, severity=None, description=None) → Claim  # drops signed if payload changed
write_claim(directory: Path, claim: Claim) → Path
read_claim(path: Path) → Claim
read_claims(directory: Path) → list[Claim]
retire_claim(directory: Path, claim_id: str) → None
```

**Retirement:** remove the Claim from the active set. For the current Git-based repository, deleting the Claim file is valid. Git history retains past bytes if committed. No `retired` field, soft-delete model, separate history database, or workflow engine.

A candidate `path` is only a convenience prefill for source `args`. When the Requirement's effective hunt list has one source id, Create uses that id. Validate Claim shape and each Check's args against `available_checks.json` before write. Requirement digests must remain unchanged across create/rebind/retire.

### 8.3 Claims Review

```text
sign_claim(claim, *, name, private_key, at) → Claim
  # thin wrapper over common.signing.sign_object; Packs v2 signed block

read_claim_seal(claim, trust, *, repo=None, relative=None) → five-fact reading
  # reuse common.signing / review.gitseal.read_claim_signature; no second seal model
```

- Inspects the same Claim object the Editor persists.
- When `signed` is absent and the claim file is in a signed Git commit, that commit is the seal (Git signing key, not the author string).
- Does not compile run results, sign review reports, or replace `curbpack-review`.

---

## 9. Human inspection without a candidate database

1. Discovery returns Candidates (retrieval-only or after optional assessment); UI shows them with Requirement law text.
2. Useful or Poor, and a selected check configuration, write the workspace feedback file for this repository, source, and working copy. That file is not a Claim. Skipping still writes nothing.
3. Create writes one Packs v2 Claim for that evidence, with every configured Check on it, when that Claim id is absent. The Claims Editor is the path for a confirmed update. A path from a finding may prefill source `args`; the person does not retype it.
4. Claims Review seals when the organisation wants a Claim seal.
5. Re-run Discovery with any strategy mix; Editor Claims, Requirements, and Packs are untouched unless a human edits them through the proper Editor / Requirements paths.

PoC1 `feedback.json` votes and check selections are operational researcher state, not a domain store and not a signature. `_signs` stays dropped. Assessment output is stored on the Discover job record so the same inputs are not scored again. It is not evidence and not a Claim field.

---

## 10. Reproducibility and durability

| Rule | Meaning |
| --- | --- |
| Discovery never writes Claims, Requirements, or Packs | Rerun / assessment cannot overwrite human or publisher artefacts |
| Deterministic retrieval baseline | Same controlled paths + hints + hunt ⇒ same Candidate core list |
| Optional assessment | May be non-deterministic. Not evidence, and not required for binding. The researcher job runs it under `assess_limit`. Completed rows on the job are reused when law text, file body, model, and prompt are unchanged. |
| Claims are repo files | Sealed Claim changes persist independently of discovery |
| Edit drops seal | Rebind clears `signed` |
| Requirement isolation | Relocate evidence by updating Claim `args` only |

---

## 11. Proven PoC1 behaviour to retain

| Behaviour | Why keep |
| --- | --- |
| Working-tree file walk with exclude globs | Proven access/retrieval core (scope of files may widen later) |
| Identify via `path_hints` and `concepts` | Default deterministic retrieval |
| Prefer only as prioritization among identified hits | Repo-wide guidance without false candidates |
| Case-insensitive glob / `**` handling | Matches how humans write hints |
| Concept excerpt for inspection | Helps reject weak hits |
| Optional LLM score / rank / why / excerpt | Assessment strategy; presentation only |
| Human gate before binding | Suggestions are not evidence |
| Multi-claim per requirement | Packs v2 evaluation model |

### Not retained

| Behaviour | Why drop |
| --- | --- |
| A candidate database separate from the Discover job | The job file already stores that run's return value. Feedback is one workspace file. Neither is a Claim. |
| Prefer globs creating candidates alone | Corrected search semantics |
| LLM scoring as a required stage for binding | Assessment may be omitted. A candidate without a score can still be bound. |
| Fake `_signs` in feedback | Real Claim `signed` / Git commit seal |
| Check picker as the Claim write | The picker writes feedback after `validate_check_args`. `build_claim` and `write_claim` run only on explicit Create, and only for an id that is not already a file. |
| Legacy YAML `search` / top-level `claim` on requirements | Forbidden on Packs v2 Requirements |

---

## 12. PoC2 today vs this architecture

Already aligned (callable without UI):

- `discover_candidates` returns temporary lists and does not write
- `build_claim` / `rebind` / `write_claim` / `retire_claim` (file delete)
- Validation and store helpers in `common`
- Rebind drops `signed`; Requirement digest unchanged

Gaps to close in implementation (not open design):

| Gap | Notes |
| --- | --- |
| Access / retrieval / assessment not split | Current `discovery/search.py` fuses walk + identify; split per §6 |
| Prefer still creates candidates | Must match §7.3 |
| No optional assessment entry point | Port PoC1 scoring as `assess_candidates` strategy when needed |
| No Claims Review entry points under claims | Use `sign_object` / seal reading; wire as §8.3 |
| `source` / `args` unread | Limitation (§6.1); when wired, unsupported IDs must fail visibly |
| Markdown-only walk | Limitation, not product intent |
| Claims UI does not seal Claims | Review responsibility |

---

## 13. Focused acceptance tests (no UI)

Direct function tests on controlled fixtures.

**Discovery**

1. **Identify:** Only `path_hints` and `concepts` create candidates; `exclude_path_globs` removes paths.
2. **Prefer does not create:** A path matching only `prefer_path_globs` is absent from the list.
3. **Prefer orders:** Among identified candidates, prefer matches sort before non-prefer within the same `matched_by` band; `path_hint` before `concept`.
4. **Deterministic retrieval:** Same tree + hints + hunt ⇒ identical Candidate core lists (no assessment).
5. **No write:** Claim, Requirement, and Pack files unchanged after discover (with or without assessment).
6. **Strategy swap:** Same fixture; alternate retrieval or assessment callable/id; compare path sets / order / optional fields; baseline remains deterministic retrieval.
7. **Assessment optional:** Retrieval-only candidates are bindable; assessment fields absent when assessment is off.
8. **Unsupported source:** When selection is wired, an unsupported `source` id fails explicitly (not an empty success list).
9. **Open a returned locator:** `read_source_text` on a Candidate `path` from that search returns the file text. A locator outside the repo raises and writes nothing. An unreadable locator raises. The page renders that text and does not read the file.

**Claims Editor**

6. **Reject is silence:** Discover without `write_claim` ⇒ no Claims on disk.
7. **Bind:** Claim has `requirement_id`, `check`, `args`; Requirement digest unchanged.
8. **Multi-claim:** Two Claims share one `requirement_id` and round-trip.
9. **Rebind:** Path update clears `signed`; Requirement unchanged; discover rerun does not alter Claim files.
10. **Retire:** File removed from the active set; other Claims remain. No `retired` field.
11. **Invalid check args:** Rejected at build/rebind with an explicit error.

**Claims Review**

12. **Unsigned / signed:** Unsigned Claim validates; `sign_claim` adds `signed`; five-fact reading; edit after sign drops `signed`.
13. **Rerun safety:** Sealed Claim bytes unchanged across a discovery rerun.

Existing tests cover much of Editor and today’s discover walk; update discovery tests for §7.3 prefer semantics, strategy boundaries (§6), and add Review seal tests under the claims API.

---

## 14. Placement

```text
poc2/discovery/    # current path. Target: poc2/claims/discovery/. Access, retrieval, read_source_text, optional assessment
poc2/claims/       # Claims Editor and Claims Review callables
poc2/claims/ui/    # Claims rendering (target). Until migration, those pages still render from poc2/app/
poc2/common/       # validate, store, signing — shared, not discovery logic
poc2/app/          # HTTP routes and navigation. Not Claims rendering
```

Access, retrieval, and assessment may live as separate modules under `discovery/` or as named functions in one file. They must stay independently callable in tests. Splitting Editor and Review into separate directories is optional. Claims owns the rendering in `poc2/claims/ui/`. `app/server.py` dispatches a URL prefix to the subsystem handler when that handler exists. New researcher routes under `/discover/claims` and `/discover/feedback` are handlers in `claims/ui/`. Those handlers own form parsing, the operation call, and the page. The existing `/discover` launcher routes and the `/claims` editor stay in `app/server.py` and keep calling subsystem operations. The server method does not retrieve, assess, validate checks, or write Claims.

---

## 15. Residual non-blockers

Not architecture blockers:

1. **Default claims directory name** (`CLAIMS/` vs `claims/`) — packaging default; PoC2 may keep `claims/`.
2. **Claim `id` suggestion in UI** — UX only; manual ids satisfy the model.
3. **Which concrete `source` ids the first non-stopgap reach implements** — decide when implementing source selection; until then the markdown walk remains an explicit limitation, and unsupported IDs must not silently look like empty success once selection is on. A Candidate `path` does not record the `{source, args}` entry that produced it. `read_source_text` takes the locator alone. Which reach applies when more than one source can emit the same locator is part of this decision. Do not add a field to Candidate for it here.

Extract / pack-publication open questions stay in `docs/arch/ARCHITECTURE.md`.

---

## 16. Complexity kept out

- A candidate database other than the Discover job file, and a feedback store other than the one workspace file per repository, source, and working copy
- ClaimDraft / Approval / Binding status types
- Soft-delete / `retired` field / retirement workflow engine
- Version graphs or signature chains between Requirement and Claim
- Source-adapter / connector platforms or general agent frameworks
- Assessment as a condition of binding
- Strategy configuration sealed into Requirement, Claim, or Pack
- Duplicating law text or hunt config onto Claim files
- Merging Claims Review into `curbpack-review`

What remains: Packs v2 Requirement and Claim, repo `hunt`, temporary Candidates (plus plain path lists from access), replaceable Discovery callables, three product module surfaces.

---

## 17. User capabilities

Status: design decision for the screens. Sentences about `poc/components/requirement_manager/`, `poc/components/cra_evidence_hunt/`, and `poc2/app/` are confirmed by that code. Behaviour already dropped in §11 is not decided again here.

PoC1, after Extract, registers a product repository and runs Discover for every requirement in the selected batch. The claims screen then lists those requirements with hit counts, vote counts, and a demo signed flag. Opening one shows the law text, the claim slug, and each hit: path, score, rank, rationale, excerpt, the file with that excerpt highlighted, a Useful/Poor vote, and a check picker. Votes, checks, and the signed flag are written to `feedback.json`. Discover is a job with a log, and it can be aborted. A failed job that already wrote some result files is shown as partial.

PoC2 opens Discover by loading `/discover`, for `CRA-ANNEX-VII-RISK` only, and shows path, `matched_by`, and excerpt. "Use path" opens the claims form with that path inside `args`. The form creates, edits, and retires Claims. It does not sign them, does not show a seal, and does not show the law text. A failed post replaces the page. `?saved=1` is not rendered.

| Capability | Decision | Why |
| --- | --- | --- |
| Choose a product repository and search it | Retain | PoC1's repo path and Discover button. The arguments are already `repo`, the Requirement, and `curbpack.json` on `discover_candidates`. |
| See path, why it was retrieved, and an excerpt | Retain | Candidate `path`, `matched_by`, and `excerpt`. |
| Read the file and see the excerpt in it | Retain | PoC1 `/doc/`. The page calls `read_source_text` with the Candidate `path` and renders that text, marking `excerpt`. It does not read the file. A failed read shows the excerpt and the error. |
| See score, rank, and rationale when a model scored the hits | Retain | Optional assessment fields. The page shows them only when assessment ran. |
| Bind a chosen path to a check | Retain | Human gate. The write is `build_claim` and `write_claim`. |
| Several bindings for one requirement | Retain | Several Claims, one `requirement_id`. PoC1 allowed several check choices on one evidence path. In PoC2 they belong in one Claim's `checks[]` for that evidence, rather than being separate Claims. |
| Change check, args, severity, or description | Retain | `rebind` and `write_claim`. A payload change drops `signed`. |
| Remove a binding | Retain | `retire_claim`. |
| Approve a binding with a real seal and read it back | Adapt | PoC1 toggles `_signs` on the requirement id and says the signature is fake. The seal is `sign_claim` on the Claim. The reading is `read_claim_seal`. |
| Law text beside the hits, and a way back to the requirement | Adapt | PoC1's detail header. The text is `references[].law_text` on the loaded Requirement. The page does not edit it. |
| Walk every in-scope requirement after one Discover | Adapt | One Discover job stores a candidate list per Requirement. The researcher overview reads the latest job for that repository, source, and working copy, including an aborted job that already has results. A later run reuses assessments whose inputs are unchanged and does not delete feedback. |
| Progress, the requirement it is on, the error, and stop | Adapt | PoC1's hunt job. The page shows the `discover_candidates` call in progress. Abort keeps every candidate the job has already written, including assessments finished inside the current Requirement. A later Discover reuses those rows when the inputs are unchanged. |
| Mark a hit Useful or Poor and see that mark later | Adapt | Workspace feedback for this repository, source, and working copy. Not a Claim. A new Discover run does not delete it. |
| Vote counts on the requirement list | Adapt | Counts from that file. |
| Check picker writing into the findings file | Adapt | The picker shows a sentence a reviewer can read. The saved `check` id is the implementation name. Saving a check writes one Claim for that evidence. The same check again leaves the file unchanged. A further check updates that Claim. |
| Signed flag on the requirement, including clearing it with no other change | Drop | `_signs` is not a Claim seal. A seal leaves when `rebind` changes the payload. Review does not flip a boolean. |
| Come back another day to the same hit list without searching | Adapt | The latest Discover job for that repository, source, and working copy. Abort keeps candidates already written on that job. A later run reuses an assessment whose law text, file body, model, and prompt are unchanged. |
| Claim slug and top-level locus columns | Drop | Forbidden on the Requirement. The list shows Requirement `id` and `references[].locator`. |
| Hide hits the model ranked None | Adapt | Score 0 and rank None are omitted from the candidate list. The judgment stays on the job for reuse. Paths that were not assessed stay in the list. |
| `repos.json` registry | Drop | The product repository is the path passed to `discover_candidates` and the directory passed to `write_claim`. Another product is another path. |

## 18. UI

Status: design decision for presentation. Claims owns this rendering. Target path: `poc2/claims/ui/`. `app/server.py` dispatches a URL prefix to the subsystem handler when that handler exists. New researcher routes under `/discover/claims` and `/discover/feedback` are handlers in `claims/ui/`. Those handlers own form parsing, the operation call, and the page. The existing `/discover` launcher routes and the `/claims` editor stay in `app/server.py` and keep calling subsystem operations. The server method does not retrieve, assess, validate checks, or write Claims. Discovery, Editor, and Review stay the functions in §8. The page does not search, validate checks, seal, or read a source file inside the template. Candidate, selected, draft, and approved are labels on this interaction.

`discovery_hints` are edited in the requirements application. This UI reads them. Check execution and the review report stay on their own screens.

### Discovery as a Review popup (one Requirement)

From a failed Claim on the final Review page, open the **same existing Discovery** for that Claim's Requirement in a popup/modal. While it is open, Review retains the failed Claim and its Check details behind it; closing/canceling returns to the same failed row without mutation. Reuse the already-existing one-Requirement discovery behavior, search results and source inspection. The presentation can include a short reminder: *Find equivalent supporting evidence and configure suitable Checks; adding a candidate does not establish a passing result.* This interaction is a target UI integration, **not a claim that the current Review page already implements it**.

The Discovery core accepts the Requirement and repo and produces its ordinary candidates, with **no Claims or Check-result input**. A thin caller/UI hook annotates the rendered candidates using existing Claim bindings and the applicable most recent Check run for the same selected repo/pack and Requirement. For an unambiguous repo-relative source path, grey the candidate (do **not** hide it) only when its evidence path matches an existing Claim's source `args`, the corresponding Claim digest matches its row in that run, and that Claim and **all its configured Checks** passed. If any path-specific Check targets different evidence, do not call that candidate covered without a verified correspondence. If matching Claim coverage includes failures or skips, or path matching is ambiguous, or the run is absent/inapplicable, **do not grey**. A signed Claim by itself is not a passing Check; a passing Check does not certify compliance or permanently certify file currency. The label must read *Already covered — passed in the selected Check run*, not *legally approved* or *currently valid*. No extra search, validation, new domain field, or backend filtering is authorized by this hook. All original candidates, including greyed candidates, remain inspectable and available in the underlying result. Grey styling is advisory, not an access restriction.

The user may **Add one or several Claims** through the ordinary existing Claims editor/binding path, selecting/checking appropriate `checks[]` for each. **Add never overwrites or automatically removes the old failed Claim.** After inspecting the new bindings, the user may explicitly **Retire/Delete** the old Claim via the normal confirmed operation; this is a separate action, and UI must warn if the replacement has not yet been checked. New/revised Claim signatures are handled by Claims Review, and the user reruns Checks before relying on any new result. Final report signing stays in `review/`. Do not build a separate Reconcile/Finder/Relocate operation or a new per-item Keep/Re-hunt record for this flow.

The researcher overview reads the latest Discover job for the selected repository, source, and working copy. That job is operational state. Useful/Poor marks, configured checks, and candidates added by hand live in the workspace feedback file for the same identity and remain across sessions. A candidate may have zero checks. No check means no Claim file. Saving a check writes one Claim for that evidence, with every check saved on the row. Saving the same checks again leaves the file unchanged. An unsigned Claim can be evaluated. Signing is a separate action.

Unsaved means the form has not been passed to `write_claim`. The Claim file is unchanged until that call returns. A validation error is shown on the form, and the entered values stay.

### Requirements

The person sees each in-scope Requirement: `id`, locator, findings, High, Useful, Poor, and the seal reading of Claims for that Requirement. When a Discover job has results, the findings cell is the candidate count, including findings added by hand. A row with no job does not show a zero. High is blank until assessment has run. Law text is the passage they open.

| Action | Function |
| --- | --- |
| List requirements | Load the Requirements the repo's `curbpack.json` selects. |
| Count bindings | `read_claims`, grouped by `requirement_id`. |
| Open discovery or open claims | Navigation. Neither action writes. |

A missing Requirement file or a Requirement outside the selected pack is the load error, shown on that row. Incomplete work is a Requirement with no Claims. That is an empty binding, not a failed search.

### Discovery

The person sees the law text, the locator, `source.url`, and the hints that will be used (`concepts`, `path_hints`, and the effective sources). The candidate table shows path, `matched_by`, and excerpt. Score, rank, and why appear only after assessment, with the model name from that call. A path that already occurs in a Claim's `args` for this requirement is marked bound; **bound does not mean passed**. In the Review-launched presentation only, the coverage hook above may additionally grey candidates backed by passing Check results. Links open the Editor and, for an existing Claim, Review.

| Action | Function |
| --- | --- |
| Search | `discover_candidates` for this Requirement. The page passes `retrieval`, and `assessment` only when the person asked for it. Opening the page does not search. |
| Search the other in-scope requirements | The same function, once each. The page shows which requirement it is on. |
| Stop | Abort keeps every candidate the job has already written. |
| Open the file | `read_source_text` for this finding's path. The page marks an excerpt only when that excerpt occurs exactly in the returned text. A model excerpt that does not occur is labeled as not found. |
| Add a candidate | The person picks a repository file Discover missed. Feedback stores it with the discovered candidates. A check is not required; adding a check makes a Claim. |
| Bind this path | Saving a check writes feedback and one Claim for that evidence. A later check on the same source updates that Claim through `rebind`. The Editor remains the place for severity, description, retire, and sign. |
| Skip | No call. |

An unsupported source, once selection is wired, is the explicit failure from §6.1, not an empty table presented as a successful search. A readable failure from the current markdown walk is shown the same way. No candidates means the call returned an empty list. The file view, when the path cannot be read, shows the excerpt and the read error.

### Claims editor

The person sees the Claims for this `requirement_id`: id, check, severity, description, args, and whether `signed` is present. The law text is on the page and is not a field. Links return to Discovery for this Requirement and to Review for this Claim. A new Claim starts with the path from Discovery when they came from a candidate; otherwise the path is empty. One save writes one Claim. A second Check on the same evidence is another entry in the **same Claim**'s `checks[]`; distinct evidence for this Requirement may have distinct Claims. This is the target domain contract, even where current UI code still requires correction. The check control offers the checks `validate_check_args` accepts. The argument fields are the ones that check requires: `exist` takes `paths`; `contents` takes `path` or `paths`, and `probes`.

| Action | Function |
| --- | --- |
| Create | `build_claim`, then `write_claim`. The person types the Claim `id`. |
| Save | `rebind`, then `write_claim`. |
| Retire | `retire_claim`. |

`ModelError` and `CheckError` are shown on the form. A check id the runner knows but does not implement shows that `CheckError` before a file is written. When the loaded Claim has `signed` and the form differs, the page says that saving clears the seal. After a successful save, the seal reading is gone and the page says it was cleared. Retire asks for confirmation because the file is removed. Other Claims for the requirement stay.

### Claim review

The person sees one Claim, the requirement's law text, and the five-fact reading.

| Action | Function |
| --- | --- |
| Read the seal | `read_claim_seal`. Absent `signed`, plus a signed Git commit of the Claim file, is that commit. |
| Sign | `sign_claim` with the signer name. The page does not edit `check` or `args`. |

`SigningUnavailable` and a failed verification are shown on the reading. The Claim file is unchanged when signing fails. Unsigned is the label when `signed` is absent and Git has no signature. Changing the binding is a link to the Editor, not a field on this page.

A later completed Review report lists every unsigned Claim and every Claim whose signature does not verify, with their Requirement ids, in an appendix. That appendix does not change check results. It is not part of this researcher workflow and is not implemented here.
)
