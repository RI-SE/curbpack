# Discover claims view — review plan

> **Status: COMPLETE as a record of the researcher pilot.** The Claim shape in the global constraints below — one Check per Claim file — was superseded by `curbpack/docs/reference/packs2.md` §2.4. A Claim now has `source`, source `args`, `description`, and `checks[]`. Create writes one Claim for the evidence. Architecture sentences from section 3 are applied for the rest of the pilot: a finding may have zero checks, Create does not overwrite, and an unsigned Claim with Checks can be evaluated. This file belongs in `doc/IMPL/`.
>
> **Later Review, not this pilot:** a completed Review report must list every unsigned Claim and every Claim whose signature does not verify, with their Requirement ids, in an appendix. That list must not change check results.
>
> This is the only plan for this pilot.

**Goal:** A tester can run Discover against `cyberready-test-product` and a CRA Annex VII working copy, then complete the PoC1 researcher workflow: overview, assessed findings, highlighted file, Useful/Poor, a check popup, a Packs v2 Claim created from that selection, and a seal reading. No step is replaced by a log or by an empty Claim form.

**Architecture:** `/discover` stays the launcher. Discover retrieves candidates, then assesses a bounded number of them. Researcher marks live in workspace `feedback.json`. Claim files in the product repo stay the only durable binding. `discovery/` and `claims/` own their operations, pages, and handlers. `app/server.py` dispatches the URL and writes the HTTP response.

**Tech stack:** Python 3, the existing `http.server`, `unittest` from `poc2/`, Ollama through the same HTTP client shape as `requirements/extract/call.py` `_default_complete`. No import of `poc/`.

## Global constraints

- Packs v2 Requirement and Claim shapes do not change. `feedback.json` is operational researcher state. It is not a Claim, a Requirement, a legal decision, or a signature.
- One Claim has `source`, source `args`, `description`, and `checks[]` (`packs2.md` §2.4). Several Checks on one piece of evidence are one Claim. Creating it never calls `write_claim` on an id that already exists. An update is a separate confirmed `rebind`.
- The HTML page does not search, call the model, validate checks, read the product file, or write.
- Do not copy PoC1 check ids (`file_present`, `text_forbid`, `anti_placeholder`) or PoC1 `_signs`.
- Do not invent scores. An unassessed candidate has no `score`, `rank`, or `why`.
- Requirements editing and signing, Claim binding, and Claim sealing stay as they are. Extract, check execution, and final Review stay out of scope.
- Do not edit `ARCHITECTURE.md` while executing this plan. Section 3 is the amendment proposal for a human.

---

## 1. PoC1 baseline (from the code)

Inspected: `poc/components/cra_evidence_hunt/hunt.py`, `ui.py`, `check_dialog.py`, and `poc/components/requirement_manager/claims_bridge.py`.

| Function | Implementation | Input | Output | Stored |
| --- | --- | --- | --- | --- |
| Retrieve | `hunt.select_candidates` | repo, YAML `search` (`concepts`, `path_hints`, exclude globs), limit 20 | markdown paths. Prefer globs are not applied. | not stored; the scored file is |
| Assess | `hunt.ollama_score` then `run_one` | law text, claim id, path, body truncated to 12_000 chars. Ollama `POST /api/generate`, model `qwen3-coder:30b`, temperature 0, JSON format | `score` 0–1, `rank` High/Medium/Low/None, `why`, `excerpt` (or a local snippet if the model excerpt is empty) | one JSON per requirement under `results/<repo-slug>/<req-id>.json`, including `model`, `law_text`, `claim`, `locus` |
| Hide weak hits | `positive_findings` | that JSON | drops `score <= 0` or rank None | the file still contains only the kept rows; None never reaches the UI |
| Failure | `run_one` | `URLError` on any file | prints the error and returns 1. No partial file for that requirement. | previous file, if any, is left as it was |
| Overview | `ui._index` | requirements YAML + result files + feedback | rows: id, locus, claim slug, finding count, High count, 👍/👎, signed button | — |
| Hit page | `ui._detail` | same | law text, model pill, one row per positive finding | — |
| Open file | `GET /doc/<req>?path=` → `render_full_doc` | repo file + excerpt | HTML with the excerpt marked, or the full file plus a note when the excerpt is not found verbatim | nothing |
| Useful/Poor | `POST /vote/<req>` | `path`, `vote` `up` or `down` | feedback entry `vote`, `at`, and copied `ai_vote` / `ai_rank` / `model` from the result file | `feedback.json` |
| Checks popup | `check_dialog.py` | catalog hardcoded from an older packs2 bag | form fields from `required` and `optional` | `POST /checks/<req>` writes `{check, args}[]` and `checks_at` on that path. `normalize_checks` does not validate args |
| Signed | `set_signed` / `is_signed` | button toggle | `_signs[req_id] = true` or key removed | same feedback file. Comment in code: not a real signature |
| Navigation | `claims_bridge.build_cfg` | batch id + repo id | mounts the hunt UI at `/claims/<batch>/<repo>/` | feedback path `step2_discover/feedback/<batch>__<repo>.json` |

PoC1 does not create a Packs v2 Claim. The check list and the signed flag are both feedback.

## 2. Parity matrix

| PoC1 function | PoC1 implementation | PoC2 today | Gap | Proposed owner | Acceptance test |
| --- | --- | --- | --- | --- | --- |
| Choose repo and working copy, run every requirement | requirement-manager hunt job + `hunt.py --all` | `/discover` + `discovery/jobs.py` calls `discover_candidates` only | No assessment. Popup is a log plus Use path into the Claim editor | `discovery/jobs.py` | Job log names each Requirement id. Candidates carry `matched_by` before assessment fields exist |
| Overview | `ui._index` | none | No `/discover/claims` | `claims/ui` page and handler; `app/server.py` dispatches | GET list has one row per Requirement in the copy, with that Requirement's id |
| Hit page | `ui._detail` | none | No law text, score, why, checks, or votes | same | Opening the id shows `references[].law_text` and each candidate path |
| Score, rank, why | `ollama_score` | none | Must be a real model call | `discovery/assess.py` | Injected completer returns a fixed JSON object; live walkthrough records the model name from the page |
| Keep retrieval visible when the model fails | PoC1 aborts the requirement | retrieval already returns candidates | Record the error on the candidate and keep the path | `discovery/jobs.py` | Unreachable endpoint leaves `matched_by` set and `score` absent |
| Open file, highlight excerpt | `ui._doc_fragment`, `locate_excerpt` | `read_source_text` is specified in claims architecture §6.1 and not implemented | Add the read and a pure highlighter | `discovery/search.py` `read_source_text`; highlight helper next to it | A path from the candidate list returns the file text. A path outside the repo raises. The page marks the excerpt |
| Useful/Poor remembered | `POST /vote` | none | Operational feedback file | `discovery/feedback.py` | Reload shows the same vote. No Claim file is created |
| Check popup from the real schema | `check_dialog.py` catalog | `checks/schema.py` implements `exist` and `contents` only | Do not copy PoC1 ids | `claims/ui` popup calls `validate_check_args` | `exist` saves `paths`. A contents probe missing `op` does not write |
| Create the Claim from that selection | not in PoC1 | `claims/bind.py` `build_claim` / `write_claim`, reached only by retyping the editor. `save_claim` overwrites an existing id | Add an explicit create that copies the saved check and refuses an existing id | `claims/bind.py` | The new Claim's `requirement_id`, `check`, and `args` equal the feedback entry. A second submit leaves the file bytes unchanged |
| See the Claim and whether the seal verifies | PoC1 toggles `_signs` | `sign_claim` / `read_claim_seal` on `/claims` | Link to that page; do not copy `_signs` | existing Claim page | A Claim with a bad `signed` block reads as not verifiable |

### Cannot be copied as-is

| PoC1 | Why | PoC2 behaviour |
| --- | --- | --- |
| Requirement id `vii-1a`, columns locus and claim slug | Those are YAML fields. Packs v2 Requirement has `id` and `references[].locator`. A claim slug on the Requirement is forbidden (`claims/ARCHITECTURE.md` §17). | Id column is Requirement `id`. Locus column is the first `references[].locator`. No slug column. |
| `file_present`, `text_forbid`, `anti_placeholder` | `packs2.md` §4 replaced that bag. PoC2 `validate_check_args` accepts `exist` and `contents` only. `fresh`, `owned`, `dep_ban` raise `CheckError`. | Popup offers `exist` and `contents`. `text_forbid` is a `contents` probe `pattern`. `anti_placeholder` is probe `placeholder`. `file_present` with only a path is `exist`. Size and headers are `contents` probes. The three unimplemented ids are named in the popup as not available and cannot be saved. |
| Several checks stored on one path in feedback, and no Claim | Packs v2: one Claim, one `check`. Several Claims may share `requirement_id` (`claims/ARCHITECTURE.md` §3.3). `save_claim` replaces the file for that id. | Feedback may hold several `{check, args}` on one path. Create writes one new Claim file per entry. An id that already exists is reported and left untouched. |
| `_signs` boolean | Not a signature. `read_claim_seal` is the reading. A present `signed` block can still fail verification. | The overview signed cell comes from Claim files and `read_claim_seal`. |
| Drop rank None before the UI | `claims/ARCHITECTURE.md` §17 says the page does not keep a second, filtered list. | Every retrieved path is shown. Rank None stays visible and is not counted as High. |
| Result JSON under `step2_discover/results/<batch>/` | A second findings database. The Discover job file already holds the return value. | The overview reads the latest finished job for that repo, source, and working copy. |
| `POST /api/generate` | PoC2 extract already calls Ollama `POST /api/chat` in `_default_complete`. | Assessment uses that client, with `format` left to the prompt (JSON object in the reply). Temperature 0, as in `hunt.ollama_score`. |

## 3. Architecture amendments for human approval

Apply these sentences only. Do not rewrite the surrounding sections. Until they are in the architecture files, do not implement.

### `poc2/doc/ARCHITECTURE.md` — HTTP server

Replace:

> It owns routing, request parsing, authentication integration, and response rendering.

with:

> It dispatches by URL prefix and owns shared response helpers and authentication integration. Each subsystem owns its handlers: form parsing, the call to its operations, and its page. The server does not implement a subsystem workflow.

Replace:

> HTTP types and framework calls stay in the server. Subsystem functions stay ordinary Python calls that tests, the CLI, and a later server can use without change. Pages still render view models, as stated for UI under Implementation boundaries; the server turns that result into the HTTP response.

with:

> Subsystem operations stay ordinary Python calls that tests, the CLI, and a later server can use without change. The subsystem handler parses its own form, calls those operations, and returns the page. `app/server.py` turns that result into the HTTP response. Existing URLs stay.

### `poc2/claims/ARCHITECTURE.md`

**§2 Discovery, Not responsible for.** Replace `persisting candidates` with:

> persisting Candidates as a domain type; creating, editing, or signing Claims; evaluating checks; mutating Requirements or Packs

Add at the end of the Discovery responsibility cell:

> The Discover job file and workspace feedback file are operational records of that run and of researcher marks. They are not Candidates-as-a-type, not Claims, and not Requirements.

**§6.3.** After "Assessment must not be required for binding." add:

> The researcher Discover job runs assessment after retrieval, bounded by `assess_limit` (default 5, allowed range 0–20) per Requirement per run. Candidates beyond the cap stay in the returned list with assessment fields omitted and are labeled not assessed. A failed or skipped call does not remove the candidate. Binding from a retrieval-only candidate remains valid.

**§7.1, the sentence that forbids model name and votes on the Candidate.** Leave it. Add after it:

> The Discover job record may store, per candidate, `assessment_state`, `assessment_error` or `assessment_skip`, `model_excerpt`, `model_excerpt_verified`, and the hashes of law text, file body, model, and prompt. Those fields support resume and display. They are not Candidate domain fields and they are not copied onto a Claim. `excerpt` stays the retrieval excerpt.

**§9, points 2 and the closing paragraph.** Replace point 2 with:

> 2. Useful or Poor, and a selected check configuration, write the workspace feedback file for this repository, source, and working copy. That file is not a Claim. Skipping still writes nothing.

Replace the closing paragraph with:

> PoC1 `feedback.json` votes and check selections are operational researcher state, not a domain store and not a signature. `_signs` stays dropped. Assessment output is stored on the Discover job record so the same inputs are not scored again. It is not evidence and not a Claim field.

**§10 Optional assessment row.** Replace the Meaning cell with:

> May be non-deterministic. Not evidence, and not required for binding. The researcher job runs it under `assess_limit`. Completed rows on the job are reused when law text, file body, model, and prompt are unchanged.

**§11 Not retained.** Replace the three rows for persisted hunt results, LLM scoring as a required stage, and check picker writing into feedback with:

| Behaviour | Why drop |
| --- | --- |
| A candidate database separate from the Discover job | The job file already stores that run's return value. Feedback is one workspace file. Neither is a Claim. |
| LLM scoring as a required stage for binding | Assessment may be omitted. A candidate without a score can still be bound. |
| Check picker as the Claim write | The picker writes feedback after `validate_check_args`. `build_claim` and `write_claim` run only on explicit Create, and only for an id that is not already a file. |

Leave the `_signs` row and the legacy YAML row unchanged.

**§14 last sentence and §18 opening.** Replace both "routes stay in `app/`" statements with:

> `app/server.py` dispatches a URL prefix to the subsystem handler when that handler exists. New researcher routes under `/discover/claims` and `/discover/feedback` are handlers in `claims/ui/`. Those handlers own form parsing, the operation call, and the page. The existing `/discover` launcher routes and the `/claims` editor stay in `app/server.py` and keep calling subsystem operations. The server method does not retrieve, assess, validate checks, or write Claims.

**§16.** Replace the bullets "Persisted candidate / findings / feedback databases" and "LLM or assessment as a required discovery stage" with:

> - A candidate database other than the Discover job file, and a feedback store other than the one workspace file per repository, source, and working copy
> - Assessment as a condition of binding

**§17.** Change these four rows from Drop to Adapt. Leave every other row, including `_signs`, claim slug, rank None, and `repos.json`.

| Capability | Decision | Why |
| --- | --- | --- |
| Mark a hit Useful or Poor and see that mark later | Adapt | Workspace feedback for this repository, source, and working copy. Not a Claim. A new Discover run does not delete it. |
| Vote counts on the requirement list | Adapt | Counts from that file. |
| Check picker writing into the findings file | Adapt | The picker writes feedback after `validate_check_args`. Create then writes one new Claim per saved check. An existing Claim id is not overwritten. |
| Come back another day to the same hit list without searching | Adapt | The latest Discover job for that repository, source, and working copy. Abort keeps candidates already written on that job. A later run reuses an assessment whose law text, file body, model, and prompt are unchanged. |

**§17 Progress row, Why.** Replace the last two sentences with:

> Abort keeps every candidate the job has already written, including assessments finished inside the current Requirement. A later Discover reuses those rows when the inputs are unchanged.

**§18 Discovery, Bind this path.** Replace the Function cell with:

> Check selection writes feedback. Create calls `build_claim` and `write_claim` only when that Claim id is absent. Discovery does not call `rebind`. A confirmed update in the Editor does.

## 4. Records and how they relate

They are five different states. None is implied by another.

| State | Where | Means |
| --- | --- | --- |
| Retrieval | candidate `path`, `matched_by`, retrieval `excerpt` | The file matched a path hint or a concept. |
| Assessment | `score`, `rank`, `why`, labeled model assessment | One model call judged that file against the law text. Absent when the call did not succeed, was skipped, or has not run. |
| Model diagnostics | on the job, not on the Requirement or the Claim | `model`, `endpoint`, temperature, prompt sha256, per-file error string. |
| Researcher feedback | `feedback.json` | A person marked Useful or Poor, and/or saved check configurations. |
| Claim | `product/claims/<id>.json` | A person explicitly created a binding. |
| Seal | Claim `signed` plus `read_claim_seal` | `signed` present is not enough. The reading says whether it verifies. |

### `feedback.json`

Owner: Discovery, as operational state. Path:

`poc2/data/workspace/discover-feedback/<repo_id>__<source_id>__<timestamp>.json`

Identity inside the file: Requirement id, then repo-relative path. The filename is the repo, the legal source, and the working copy. Two copies do not share a file.

```text
{
  "repo_id": "cyberready-test-product",
  "source_id": "cra-xml-vii",
  "timestamp": "2026-10-14T043810Z",
  "requirements": {
    "<Requirement id>": {
      "<path>": {
        "vote": "useful" | "poor",
        "checks": [ { "check": "exist"|"contents", "args": { } } ]
      }
    }
  }
}
```

Update rules:

- Vote replaces `vote` on that path and leaves `checks` in place.
- Save checks replaces `checks` on that path and leaves `vote` in place. Each entry must pass `validate_check_args` before the file is written. A failure leaves the bytes unchanged.
- A new Discover run does not delete or rewrite the file. Paths that are no longer in the new candidate list stay in the file and are not shown on the current hit page.
- Unknown Requirement id, unknown repo, or a timestamp that is not a working copy of that source is rejected and writes nothing.
- Feedback is not copied onto the Claim. Create reads it once and calls `build_claim`.

### Several checks become one Claim

The steps below were the pilot's first write path, one file per Check. The global constraint above replaces that: the same evidence and every saved Check are one Claim file.

`save_claim` replaces whatever file already uses that id. Create therefore checks the claims directory before any write.

Suggested id, stable across submits: requirement id, the path with `/` replaced by `__`, and the check id, joined by `-`. Characters outside `A-Za-z0-9._-` are dropped, which is the alphabet `_safe_id` accepts. The same check on the same path always suggests the same id. No numeric suffix.

For each saved `{check, args}`, in order:

1. `require_requirement_id` against the working copy. `build_claim` with that id, the feedback `check`, and the feedback `args`. The person does not type the path again. `exist` args are `{ "paths": ["<the hit path>"] }` from `exist_args_for_path`. `contents` args are `{ "path": "<the hit path>", "probes": [ ... ] }`.
2. If no file has that id: `write_claim`. Outcome `created`.
3. If a file has that id and its `requirement_id`, `check`, and `args` are equal to the built claim: do not write. Outcome `unchanged`. A signed file in this case is also left byte-for-byte.
4. If a file has that id and any of those three differ: do not write and do not call `rebind`. Outcome `blocked`, naming the existing id. A signed block on that file is reported as signed and unchanged. The Editor remains the only place that can `rebind`, and only after the person confirms. Confirmation is not implied by submitting Create again.

One validation error or one blocked id does not roll back Claims already created in this submit, and it does not stop the remaining checks. The page lists every outcome: created id, unchanged id, or blocked id with the reason. A check that never reached `write_claim` is not described as created.

Create does not sign. After it returns, each created or unchanged id links to the existing `/claims` editor, which shows the law text and `read_claim_seal`.

## 5. Assessment

Owner: `discovery/assess.py`. The researcher job always passes `assessment`. `assess_limit` defaults to 5 and must be an integer from 0 through 20. Zero retrieves and stores every candidate with `assessment_state` `not_assessed` and makes no model call. A value outside 0–20 is rejected at job start and writes no job.

Retrieval limit stays the existing `discover_candidates` limit. Every retrieved path is stored and shown. Low scores, rank `None`, failures, and paths past the cap stay in the list.

### What one call does

What the model receives, from `hunt.SCORE_PROMPT`, with PoC2 fields:

- Law text: the Requirement's `references[].law_text` joined in order. Not `discovery_hints`.
- Id: Requirement `id`. Not a claim slug.
- Path and the file body from `read_source_text`, truncated to 12_000 characters with the same truncation marker as PoC1.

`score` is a float from 0 to 1. `rank` is `High`, `Medium`, `Low`, or `None`. `why` is one short sentence. The page labels all three **model assessment**. They are not verified evidence and they are not copied onto a Claim.

`excerpt` on the candidate stays the retrieval excerpt. The model's quote is stored separately as `model_excerpt`.

Client: `requirements.extract.call._default_complete` with temperature 0, model `qwen3-coder:30b`, endpoint `http://127.0.0.1:11434`, timeout 600. The prompt asks for one JSON object. Parse with the existing `_parse_json_object`. This is one call per file, not the extract strategy loop. Extract's provision schema is not reused.

### Verified quotation

`verify_excerpt(body, excerpt)` returns a span only when `excerpt.strip()` occurs as an exact substring of `body`. No whitespace folding and no fallback to a single line.

- Verified model excerpt: `model_excerpt_verified` true. The file view highlights that span and labels it a model excerpt found in the file.
- Model excerpt missing or not an exact substring: `model_excerpt_verified` false. The page says the model excerpt was not found in the file. If the retrieval excerpt verifies, the file view highlights that span and labels it a retrieval excerpt. Nothing else is highlighted.
- Empty model excerpt: same as not found. No score is invented to fill it.

A missing file fails `read_source_text`. That candidate is `failed`, with the read error, no score, and no highlight.

### States

| `assessment_state` | Shown as | Fields |
| --- | --- | --- |
| `not_assessed` | Not assessed | retrieval fields only. This includes paths past `assess_limit`. |
| `assessed` | Model assessment | `score`, `rank`, `why`, plus the verification flag |
| `failed` | Assessment failed | `assessment_error`, no score, no rank, no why |
| `reused` | Model assessment, reused | same fields as `assessed`, copied from an earlier job |

`not_assessed` rows also carry `assessment_skip: cap` when the cap was the reason. The job log lists skipped paths and failed paths by those words.

### Bound, abort, resume

Order is the retrieval order. The job assesses the first `assess_limit` candidates that are not reusable, then marks the rest `not_assessed` / `cap` without calling the model.

Progress uses the existing job file. After each file the thread calls the same `_advance` that already persists `results`, with a log line `scoring i/n` or `skipped cap: <path>` or `failed: <path>`. `n` is the number of calls this requirement will make, not the retrieval count.

Abort is the existing `request_abort`. The thread checks status before each file. Candidates already passed to `_advance` remain on that job. The overview reads an aborted job that has `results`.

Resume uses that job infrastructure and no other store. A new Discover creates a new job id, as `start_discover_job` does now. Before a model call it loads the newest prior job for the same `repo_id`, source, and working-copy timestamp that has `results`, including `aborted` and `failed`. A candidate is reusable when that prior row is `assessed` or `reused` and all four hashes match: sha256 of the joined law text, sha256 of the truncated body, model name, and sha256 of the prompt string. The new job copies `score`, `rank`, `why`, `model_excerpt`, and `model_excerpt_verified`, sets `assessment_state` to `reused`, and does not call the model. A hash mismatch is assessed again and counts toward `assess_limit`. Reused rows do not count toward the cap.

Diagnostics on the job, per requirement: `model`, `endpoint`, `temperature`, prompt sha256. Per candidate: the state, the four hashes when a call or a reuse happened, and either the assessment fields or `assessment_error` / `assessment_skip`.

Failure of a call:

- Unparseable reply, score outside 0–1, or rank not in the four words: state `failed`, retrieval fields kept, no score stored.
- Endpoint unreachable: the same for that file and for every later file in that requirement that has not already been reused. The job still finishes `done` when retrieval succeeded. Reused rows stay. The hit page says assessment failed on the failed rows. The person can still vote and bind from retrieval.
- Abort between files stops further calls. Rows already written stay.

Tests, without a live model:

- Completer returns `{"score": 0.9, "rank": "High", "why": "Names the intended purpose.", "excerpt": "<an exact span of the fixture file>"}`. State `assessed`. The prompt contains the law text and the path. `model_excerpt_verified` is true only for that exact span.
- The same response with an excerpt that is not in the file: score and why are kept, `model_excerpt_verified` is false, and the retrieval excerpt is the only highlightable span when it occurs exactly.
- Completer returns `not json`. State `failed`, `matched_by` kept, no `score`.
- Completer raises the endpoint error `_default_complete` raises. No score is written. Requirement and Claim files are byte-identical.
- Six candidates and `assess_limit` 2: two calls, four `not_assessed` with `assessment_skip` `cap`. None are removed.
- Abort after the first call: the job's `results` contain that candidate's score, and the completer is not called again for it.
- Second job, same law text, body, model, and prompt: completer call count is zero for that path and the state is `reused`. Changing one byte of the file causes one new call.

The live walkthrough is the semantic check against `cyberready-test-product`. A unit test does not claim the model's sentence is correct.

## 6. Checks popup and Claim creation

Catalog for the popup, derived from `checks/schema.py` and `packs2.md` §4, not from `check_dialog.CHECKS`:

| Check | Fields | Prefill |
| --- | --- | --- |
| `exist` | `paths` | the hit path, as a one-element list |
| `contents` | `path`, and a probe list. Probe kinds: `size` (`bytes`, `op`), `words` (`n`, `op`), `headers`, `token`, `pattern`, `placeholder` | `path` is the hit path. Probes start empty. The person adds at least one |

`fresh`, `owned`, and `dep_ban` are listed as unavailable (`CheckError` text from `validate_check_args`). They have no inputs and are not posted.

Save calls `validate_check_args` for every selected check. Any failure returns the error and does not write `feedback.json`.

**Create claim** is a button on the hit row, enabled when that path has at least one saved check. It runs the mapping in section 4 and then shows the per-check outcomes on the same page. It does not open a blank editor and it does not call `rebind`. The existing editor remains for severity, description, retire, sign, and a confirmed update of an existing id.

## 7. Routes and ownership

| Piece | Owner | Notes |
| --- | --- | --- |
| `discover_candidates`, `read_source_text`, highlight lookup | `discovery/search.py` | Highlight lookup is a pure function over the returned text. The page does not open the file. |
| `assess_candidates` | `discovery/assess.py` | |
| Job orchestration | `discovery/jobs.py` | Already runs the loop. It gains the assessment call. |
| Feedback load/save | `discovery/feedback.py` | |
| `build_claim`, `write_claim`, `rebind`, `read_claim_seal` | `claims/bind.py` | Reuse. No second writer. |
| HTML for `/discover`, `/discover/claims`, the hit page, the popup, the file view | `claims/ui/pages.py` | |
| Handlers for those pages, vote, checks, and create | `claims/ui/http.py` | Parses the form, calls the operation, returns the page. |
| URL dispatch | `app/server.py` | One prefix dispatch to that module. No retrieval, assessment, feedback, or Claim write in the server method. |

| URL | Behaviour |
| --- | --- |
| `GET /discover` | Current launcher. **Open claims** appears when a finished job exists for the selected repo, source, and timestamp. |
| `POST /discover/run` | Current start, plus `assess_limit` (default 5). The job assesses after retrieval, within that cap. |
| `GET /discover/claims?repo=&source=&timestamp=` | Overview. |
| `GET /discover/claims/<requirement id>?repo=&source=&timestamp=` | Hit page. Unknown id is an error, not another requirement. |
| `GET /discover/claims/<requirement id>/file?path=` | Renders `read_source_text` with the excerpt marked. Missing file shows the excerpt and the error. |
| `POST /discover/feedback/vote` | Useful or Poor. |
| `POST /discover/feedback/checks` | Validated checks. |
| `POST /discover/claims/create` | One new Claim file per saved check whose id is absent. The response lists created, unchanged, and blocked. It does not redirect away from those outcomes. Links go to `/claims?requirement_id=`. |

`/claims` stays the Claim editor. It is not replaced.

Smallest migration: existing `/discover`, `/discover/run`, `/discover/jobs`, and `/claims` editor methods stay in `app/server.py` so their current behaviour does not move. New researcher routes are functions in `claims/ui/http.py`. `do_GET` and `do_POST` gain a prefix call for those paths and nothing else. Do not relocate the Claim editor in this pilot.

## 8. Implementation sequence

Each step is independently testable. Later steps depend on earlier ones. Rollback is reverting that step's files; feedback and job files are workspace data and are not packed.

### Step 1 — `read_source_text` and highlight

- Files: `discovery/search.py`, `tests/test_m2_discovery.py`.
- Reuse: path confinement already implied by the architecture (a locator outside the repo raises).
- Tests: a candidate path returns the file text; `../` and an absolute path raise; a missing file raises. `verify_excerpt` returns a span for an exact substring, including one that only needed `strip`, and returns none for a mismatched excerpt and for a whitespace-folded excerpt. The highlight helper marks only a verified span.
- Manual: none yet.
- Depends on: nothing.

### Step 2 — Assessment callable

- Files: `discovery/assess.py`, `tests/test_discovery_assess.py`.
- Reuse: `_default_complete` and `_parse_json_object` from `requirements/extract/call.py`. Prompt text from `hunt.SCORE_PROMPT`, with Requirement id and joined law text.
- Tests: section 5 completer cases, exact and mismatched excerpts, cap, and resume. No live Ollama.
- Manual: none.
- Depends on: step 1.

### Step 3 — Job runs assessment and keeps retrieval on failure

- Files: `discovery/jobs.py`, `tests/test_discover_repos.py`.
- The job passes `assessment` and `assess_limit` into the run. After each file it calls `_advance` with `results`, which already persists the job. Resume copies matching rows from the newest prior job for the same repo, source, and timestamp before counting a call against the cap.
- Tests: two requirements, injected completer, both ids in `results` with scores; endpoint error leaves paths and omits scores; six candidates with limit 2 make two calls and keep four `not_assessed` rows; abort after the first `_advance` leaves that score on the job file; a second job with unchanged inputs makes no call for that path; Requirement bytes unchanged; no Claim directory.
- Manual: Discover on a copy of two fixture requirements with the injected completer is covered by the HTTP test in step 5. This step is the library.
- Depends on: step 2.

### Step 4 — Feedback file

- Files: `discovery/feedback.py`, `tests/test_discover_feedback.py`.
- Tests: vote then checks round-trip; bad `contents` probe does not change bytes; second Discover does not delete the file; unknown requirement id raises.
- Depends on: nothing. Can be written beside step 1.

### Step 5 — Overview and hit page

- Files: `claims/ui/pages.py`, `claims/ui/http.py`, a prefix dispatch in `app/server.py`, `tests/test_discover_claims_ui.py`.
- The list reads the latest job that has `results` for that repo, source, and timestamp, including `aborted`. Findings count is the candidate count. High count is rank `High` only. The hit page labels each row not assessed, model assessment, model assessment reused, or assessment failed. Score and why are shown only on assessed and reused rows, with the words model assessment. Checks and vote come from feedback.
- Tests: two Requirement ids; the other id is not on the first hit page; stale timestamp errors; no job shows the requirements with a blank findings cell, not `0`.
- Manual: open `/discover/claims` after a fixture job and confirm the ids match the working copy.
- Depends on: steps 3 and 4.

### Step 6 — File view

- Files: `claims/ui/pages.py`, `claims/ui/http.py`, the same UI test.
- The hit file name links to the file route. The page marks the excerpt in the returned text.
- Tests: a verified model excerpt is marked and labeled as found in the file; a mismatched model excerpt is named as not found, and a verified retrieval excerpt is the span that is marked; a missing path shows the read error, marks nothing, and writes nothing.
- Depends on: steps 1 and 5.

### Step 7 — Vote and checks popup

- Files: `claims/ui/pages.py`, `claims/ui/http.py`, `discovery/feedback.py`.
- Popup fields are the table in section 6. Save and vote POST to the feedback functions.
- Tests: Useful survives reload; invalid probe returns 400 and the feedback bytes are unchanged; `exist` save stores `paths` equal to the hit.
- Depends on: steps 4 and 5.

### Step 8 — Create claim and open the seal reading

- Files: `claims/ui/http.py` calls `build_claim` and, only when the id is absent, `write_claim`. It does not call `rebind`. The page lists each outcome and links to `/claims`.
- Tests: two checks on one path produce two Claim files, same `requirement_id`, args equal to feedback. The second submit reports both `unchanged` and the file bytes, including a signed file, stay equal. A pre-existing id whose `args` differ is `blocked`, and that file's bytes stay equal whether or not `signed` is present. One invalid check in a pair of three reports the created id and the blocked id, and leaves the created file in place. Requirement digest unchanged. `read_claim_seal` on an unsigned Claim is unsigned, and a tampered `signed` block is not verifiable.
- Depends on: step 7 and the existing Claim page.

### Step 9 — Open claims on the launcher, then the live walkthrough

- Files: `claims/ui/pages.py` link, `tests/test_discover_claims_ui.py`, and a written record of the manual walkthrough in this plan's checkpoint when it is executed.
- Depends on: steps 1–8.

Preserved throughout: `/requirements` edit and sign, `/claims` create/edit/retire/sign, `require_requirement_id`.

## 9. Final acceptance

One walkthrough on the existing CRA Annex VII working copy `poc2/data/workspace/cra-xml-baseline/2026-10-14T043810Z` and repo `/Users/DanielFl/Documents/aProjects/aslak/cyberready-test-product`. Ollama at `http://127.0.0.1:11434` with `qwen3-coder:30b`. If the model is down, the walkthrough stops at step 4 and is not called parity.

1. On `/discover`, select that repo, CRA Annex VII, section VII, that working copy. Discover. The popup finishes with one block per Requirement id in the copy.
2. Open claims. The overview lists those Requirement ids and locators, not `vii-1a` and not a claim slug. Findings counts match the job. High counts match rank High.
3. Open `CRA-ANNEX-VII-DESCRIPTION-PURPOSE` (VII.1(a)). The law text is the passage on that Requirement. Assessed rows show a score, a rank, and a why, labeled model assessment, with the model name from the job. Rows past the cap say not assessed and have no score. Failed rows say assessment failed and have no score. Abort during the run leaves the scores already logged still on the page after reopen. Run Discover again without changing the product files: those rows say reused and the log shows no new scoring line for them.
4. Open one of those files. The document text is the file in `cyberready-test-product`. A model excerpt is highlighted only when it occurs exactly in that text, and the page says it was found in the file. A model excerpt that does not occur is labeled not found, and a retrieval excerpt that does occur is the highlighted span. A path that is not in the repo shows the read error and no highlight.
5. Mark that row Useful. Reload. The mark is still there. `product/claims/` has no new file yet.
6. Open Checks. Choose `exist`. Save. Reload. The row shows `exist`. Choose `contents` with a `pattern` probe and an empty pattern. Save is refused and the file is unchanged.
7. Save a valid `contents` probe. Create claim. The page lists two created ids. Both files have `requirement_id` equal to that Requirement and `args` equal to the saved checks, with no retyped path. Submit Create again. The page lists both as unchanged, and the file bytes are the same. A Claim that already exists with different args is listed as blocked, and its bytes stay the same. Sign one of the new Claims in the editor, then submit Create again: that file stays signed and unchanged.
8. Open `/claims` for a created id. The Claim shows the check and args. Unsigned is the seal reading. Sign with the existing form. The reading is verifiable. Edit the args in the editor and confirm the save. The seal is gone. That edit is the editor's `rebind`, not Create.
9. Change the working-copy timestamp to one that does not exist. The overview errors and does not show another copy's feedback.
10. Open a Requirement id that is not in the copy. The hit page errors.

Negative cases covered above and in the unit tests: invalid check args, an existing Claim id, a signed Claim submitted again through Create, a partial create where one check is blocked, missing document, mismatched model excerpt, failed assessment, assessment past the cap, abort and resume, stale timestamp, unknown Requirement id, tampered signature.

Parity is not claimed if any of 1–10 is missing or if scores were typed in by hand.

## 10. Blockers found in the code

These are settled by the steps above. They are not open design questions.

- `common/store.py` `save_claim` writes `claims/<id>.json` whenever `write_claim` is called. There is no create-if-absent operation. Step 8 must see an existing file first and skip `write_claim`. The Editor's own save still uses `write_claim` after `rebind`.
- `discovery/jobs.py` persists `results` only when `_advance` is called, and today that happens once per Requirement, after retrieval. An abort during assessment of a Requirement would drop scores from that Requirement unless `_advance` runs after each file. The function already accepts `results`. Step 3 uses that.
- Resume has no store besides the job files in `workspace/jobs`. `start_discover_job` always allocates a new id. Step 3 reads the newest prior job for the same repo, source, and timestamp. It does not add a database.
- Claim ids cannot contain `/` (`_safe_id`). The suggested id replaces `/` with `__`. Two different paths can still slug to one id. That outcome is `blocked`, not a new suffix and not an update.
- `_default_complete` calls `/api/chat` and does not send Ollama `format: json`. A non-JSON reply is the `failed` state in section 5. The live walkthrough confirms that this model returns the four fields through that client.
- The walkthrough working copy is an unsigned draft. That is enough for Discover. It is not a published Pack.
- `assess_limit` default 5, over 13 Requirements, is at most 65 model calls on a cold run. Retrieval can still return up to 40 paths per Requirement; only the first 5 that are not reusable are scored. Reused rows do not count.

## Current checkpoint

Done: steps 1–9. `read_source_text`, exact excerpt verification, bounded assessment, job abort/resume, `feedback.json`, researcher pages, checks popup, explicit Claim creation that does not overwrite, and an Add action for a file plus a human rationale.

Tested: `cd poc2 && .venv/bin/python -m unittest tests.test_m2_discovery tests.test_discovery_assess tests.test_discover_repos tests.test_discover_feedback tests.test_create_configured_claims tests.test_discover_claims_ui tests.test_claims_binding_ui` — pass. Also `tests.test_ui_smoke tests.test_m4_checks tests.test_requirements_ui tests.test_pilot_pack_selection tests.test_m3_claims` — pass. The HTTP researcher test covers Discover, overview, legal text, model score, highlighted file, Useful reload, rejected empty pattern, saved `exist`, Create, repeated Create unchanged, Claim editor unsigned reading, an added finding, and a finding with no checks.

Live walkthrough, 2026-10-14, server `http://127.0.0.1:8771`, working copy `cra-xml-baseline/2026-10-14T043810Z`, product `/Users/DanielFl/Documents/aProjects/aslak/cyberready-test-product`, model `qwen3-coder:30b`:

- Job `discover-407528d0` finished with `assess_limit` 1. Overview lists the Annex VII Requirement ids. `CRA-ANNEX-VII-DESCRIPTION-PURPOSE` shows locator VII.1(a), 9 findings, High 1.
- The purpose page shows the law text, model score 0.8 High, and the model rationale. Other findings on that page say not assessed and have no score.
- `README.md` highlights the model excerpt and says it was found in the file.
- Useful reloads as `Vote: useful`. An empty `contents` pattern returns HTTP 400. `exist` with `{"paths": ["README.md"]}` persists.
- Create wrote `claims/CRA-ANNEX-VII-DESCRIPTION-PURPOSE-README.md-exist.json` with that requirement id, check, and args. A second Create reports unchanged. Findings with no checks stay on the page and were not written as Claims.
- `run_claim` on that unsigned file returns `pass`. The Claims editor, opened with `repo_id=cyberready-test-product`, reads it as an unsigned draft and shows the same check and args.
- Job `discover-a6acf7a5` with `assess_limit` 0 finished without a new scoring line. The purpose page then says `Model assessment, reused` and keeps score 0.8. The log says `reused: README.md`.
- A missing working-copy timestamp and an unknown Requirement id both return HTTP 400.
- Overview signing cell for the purpose row reads `unsigned draft`.

Covered by the automated tests rather than repeated on this product: abort leaving the scores already written, two checks creating two Claims, a signed file left unchanged by Create, and an editor save clearing a seal.

Blocker: none. No commit in this step. The Review appendix is recorded and not implemented.
