# Requirements: minimal auditable Qwen agent experiment

Status: recorded. Human chose to repair `propose_critique_revise`. The subset run is in the checkpoint below. Not a legal verdict. Not Task 21. Task 20 stays open.

### Current checkpoint

| Field | Value |
| --- | --- |
| Plan state | RECORDED. Human chose to repair `propose_critique_revise` and not add `agent_loop`. No `ARCHITECTURE.md` edit. The subset run is recorded below. This file stays in `poc2/doc/PLAN/` because the original acceptance named `agent_loop`, which was not added. Local commits only. Branch `main`. Do not push. |
| Source | Copied from `/Users/DanielFl/Downloads/AGENT_IMPLEMENTATION_PLAN.md` on 2026-10-14 after the user said to run it. `poc2/AGENTS.md` was read first. |
| Last completed task | Subset run `2026-10-14T052026Z`, copy `2026-10-14T052102Z`. Code commits `214a1da`, `d0d1480`, `03e6612`. |
| Uncommitted files | Pre-existing unrelated files stay unstaged: `daniel/`, `docs/superpowers/`, the PoC feedback JSON, and the `poc2/requirements.zip` deletion. Trace and the dated copy are gitignored under `poc2/data/workspace/`. |
| Last tests and result | `cd poc2 && .venv/bin/python -m unittest discover -s tests` — PASS, 110 tests, before the propose-wrapper sentence. After that sentence: `cd poc2 && .venv/bin/python -m unittest tests.test_revise_loop tests.test_requirements_produce` — PASS, 24 tests. |
| Active blocker/decision | None for this experiment. Do not treat the subset copy as a full Annex VII extract or as legally correct. Task 20 stays open in the Requirements plan. |
| **Exact next action** | None in this plan. Do not start Task 21. |

## Conflict

The plan below adds optional `strategy='agent_loop'` and `max_rounds=10` only for that strategy.

`poc2/requirements/ARCHITECTURE.md` §4.1.5 limits diagnostic `strategy` to `single_call`, `multi_prompt`, or `propose_critique_revise`. `max_rounds` is required only when `strategy` is `propose_critique_revise`, and absent otherwise. §4.2 names the same three strategies. `poc2/requirements/extract/produce.py` enforces `_STRATEGIES` and rejects `max_rounds` on any other strategy.

The same plan says the existing `propose_critique_revise` path must not be silently rebranded as the agent. In `produce.py` the critique return value is discarded (`_critique_text`); the revise call still sends the previous proposal JSON. `REQUIREMENTS_IMPLEMENTATION_PLAN.md` records that as a known defect, not redesigned.

`poc2/doc/POLICIES/DEVELOPMENT.md` says an implementation plan that conflicts with the architecture stops the affected task. Permission to run this plan is not permission to edit `ARCHITECTURE.md`.

A separate trace directory outside any sealed Pack does not conflict with Packs v2, provided `llm` notes keep the existing fields and raw responses stay out of those notes. That part waits on the strategy decision.

Resolutions, one of which a human must pick:

1. Authorize an architecture edit that adds `agent_loop` to the diagnostic strategy set and allows `max_rounds` on it. Then implement this plan as written. `poc2/extract/ARCHITECTURE.md` stays historical.
2. Authorize a focused repair of the existing `propose_critique_revise` strategy so critique text reaches revise, with the plan's stop, regression, and trace rules. Do not add `agent_loop`.

**Decision (2026-10-14):** resolution 2. The strategy name stays `propose_critique_revise`. `max_rounds` remains the integer bound the caller passes. The subset experiment passes 10, which the tests treat as that bound, not as a second hidden cap. Trace files are written only when `trace_dir` is a new directory. `single_call` still rejects `trace_dir`, `should_abort`, and `max_rounds`.

## Subset run (2026-10-14)

Not a legal verdict. The frozen reference was not modified (`reference_unchanged: true`).

First attempt `poc2/data/workspace/traces/2026-10-14T051852Z` failed in 4.3s. Three propose calls for locus `2(b)` each returned one bare object, so the existing `{"provisions":[...]}` parser never started critique. No copy.

The propose call now repeats that wrapper in one sentence. Tests: `tests.test_revise_loop` and `tests.test_requirements_produce`, 24 tests, PASS. Commit `03e6612`.

Second attempt wrote copy `poc2/data/workspace/cra-xml-baseline/2026-10-14T052102Z` (3 Requirements, not a full Annex VII extract). Trace `poc2/data/workspace/traces/2026-10-14T052026Z`. Model `qwen3-coder:30b` digest `06c1097efce0431c2045fe7b2e5108366e43bee1b4603a7aded8f21689e90bca`. 26 calls, 36.3s, 11883 prompt tokens, 3366 completion tokens. Ten rounds were available. The longest interpret loop used 3 critique rounds. Nothing ran all 10.

Stop reasons: interpret `2(b)`, `5`, and `8` stopped `no_actionable_change`. Discovery `2(b)` stopped the same way. Discovery `5` and `8` stopped `invalid_response` and kept the last schema-valid hints. Critique text did reach revise. On the interpret side the critique named passage phrases as if they were fields, and the following revise usually returned the same candidate. The loop did not remove unsupported fields.

Against the frozen reference and the passage text:

- `2(b)` hints name the bill of materials, the coordinated disclosure policy, the reporting contact, and secure update distribution, with `documents` and `git`. That is useful for search. The draft also sets `strength: MUST` and `applicability: where applicable`. This passage has no shall, should, may, or "where". `responsible` is `manufacturer`; that word is in the passage, and the reference leaves `responsible` unset.
- `5` hints name harmonised standards, common specifications, certification schemes, and alternative solutions. The passage does contain shall, and the draft sets `MUST`. The locator is `I.5` and the id says Annex I. The passage is Annex VII point 5. `responsible` is `the manufacturer`, which this passage does not contain.
- `8` hints stay on the bill of materials and the reasoned request. They do not add the reference's CycloneDX, SPDX, SOUP, or dependency-inventory labels. The locator is `VIII.8`. Two accepted interpret revisions lengthened `applicability` and left `VIII.8` and `MUST` in place. This passage has no shall, should, or may.

The self-stop is `no_actionable_change` or an invalid revise. It is not legal approval.

## Goal and boundaries

Add a bounded `agent_loop` producer for stages 02 (interpret) and 03 (discovery hints). Preserve existing deterministic stages 00-01, stage 04 assembly, Packs v2, Requirements editing/signing/publishing, and the default `single_call` behavior. No new agent framework, UI, provider adapter, persistent domain type or architecture rewrite. PoC1 and reference outputs stay read-only.

The core control flow must fit in a short, readable Python module with explicit `propose`, `critique`, `revise`, `validate`, `stop` operations. Model calls remain injectable for tests. The existing validators are authoritative for shape, not legal correctness.

## Verified integration points (requirements.zip snapshot)

- `requirements/extract/produce.py`: `interpret`, `discovery_hints`, `_produce`, `proposals_from_producers` and injectable `complete(prompt, settings)`.
- `requirements/jobs.py`: `_run_extract` calls `proposals_from_producers`, then `workspace.extract_section` with its `(proposals, llm_notes)` outputs.
- `requirements/extract/assemble.py`: stage 04 validates and assembles Packs v2 Requirements.
- Existing `propose_critique_revise` discards critique content when revising; its use should not silently be rebranded as a working agent.
- `proposals_from_producers` does not currently accept/forward `max_rounds`; the job path fixes producer defaults.

## Work items in dependency order

### 1. Define one small strategy boundary

Keep `proposals_from_producers(provisions, *, adapter_dir, ...) -> (proposals, llm_notes)` unchanged in shape. Add optional `strategy='agent_loop'`, `max_rounds=10` only for that strategy, `trace_dir=None`, and `should_abort=None` as explicit keyword-only runtime parameters. Keep default strategy `single_call`. Reuse the existing `complete` injection and validation methods; no second Ollama client. Avoid changing existing strategies except focused bug fixes separately authorized.

The agent may operate one provision at a time, but both stages must return the same complete validated per-locus lists required by the existing assembler. Preserve every input locus exactly once, never invent IDs/locators or edit source passages. Keep interpret and hint outputs in their separate allowed formats.

### 2. Implement simple loop

For each provision and stage:

1. `propose`: render the existing stage guidance + source passage; obtain raw model response; parse and validate.
2. `critique`: compare current candidate with the ORIGINAL law passage; request structured, concrete missing/unsupported evidence aspects or fields, with source quotation/locator where possible. Critique is advisory, not validation.
3. `stop`: if critique has no actionable findings, stop with `no_issues_reported` (not `legally_correct`).
4. `revise`: send current candidate AND critique AND original passage; parse and validate.
5. `accept/reject`: accept a schema-valid revision unless a defined explicit regression gate rejects it; if rejected retain last valid candidate. Never treat a self-reported numeric LLM score as proof of improvement.
6. Continue at most 10 critique/revise rounds per provision/stage. Stop on user abort, exhausted budget, persistent invalid responses or lack of actionable change. Preserve the last valid candidate and outstanding issues.

Do not allow unbounded self-calls, recursive agent spawning or autonomous tool execution. Keep prompts as versioned, human-editable `.txt` files adjacent to the current adapter guidance or in a clearly named agent guidance directory. Never embed reference answers in guidance.

### 3. Complete experiment trace: append-only, outside Packs v2

Create one unique trace directory per run (including failures); do NOT place trace files in a sealed Pack directory. Use an append-only `events.jsonl` and immutable numbered artifacts. At minimum record:

- Run ID, start/end times, source ID/version, adapter/section/locus, model name/digest if available, endpoint identifier, strategy, generation settings, max rounds, prompt hashes and exact sanitized prompt snapshots, input provision snapshots.
- For EVERY model call: chronological call number, stage, role, round, full rendered prompt, full raw response (even invalid), parse outcome, validation messages, start/end/duration and token counts when available.
- Critique issues, revision acceptance/rejection and reason, remaining issues, stop decision and reason, final candidate reference, errors/abort.
- A machine-readable manifest mapping all stage outputs to trace artifacts plus SHA-256 for data integrity; references to copy/Pack outputs without changing the Requirements schema.

Never log API keys, auth headers, home-directory secrets or other credentials. Keep raw responses separate from validated Requirements. Flush writes after every step so a crash leaves inspectable history. Trace directory is diagnostic data, not legal evidence or a sign-off record. If tracing cannot be initialized, fail explicitly instead of silently discarding the audit trail in agent mode.

### 4. Failures, cancellation and resource limits

- Each model call has a finite timeout; expose errors and do not destroy the last schema-valid candidate.
- Check `should_abort` before each call and after it returns. Abort stops new calls and leaves a complete terminal event, but an in-flight blocking HTTP call may need timeout/cancellable transport; do not falsely claim immediate network cancellation.
- `max_rounds` is a hard cap; also cap invalid-retry attempts per call and total calls per provision. Count all retries in logs. Keep run output incomplete/failed if the required validated locus outputs cannot be produced; never silently publish partial work.
- Never overwrite existing dated copies, published Packs, gold references or previous trace runs.

### 5. Verification and experiment

Unit tests (injected deterministic completion): critique really reaches revise; rounds limited to 10; correct stop reasons; schema-invalid revision never overwrites valid candidate; all loci returned; malformed responses logged; prompt and output hashes stable; abort between calls; no mutation of previous copies or reference materials. Include a trace replay/inspection test that reconstructs accepted decision history without trusting `llm_notes` alone.

Run existing `single_call` tests and full PoC2 suite unchanged. Execute a real local Qwen run on a small difficult CRA subset (VII.2(b), VII.5, VII.8), preserving independent dated outputs and all traces. Compare with the frozen agent-produced PoC1-derived reference. Report missing aspects, invented aspects, usefulness, number of calls, elapsed time and token data. Do not claim legal correctness because the agent self-approved.

NIS2 Article 21 is later held-out evaluation, not prompt-training material.

## Checkpoints and acceptance

Implement in small verified steps: (A) producer boundary + injected tests, (B) loop + tests, (C) trace + recovery/cancel tests, (D) real CRA evaluation. Record each in the existing active plan/checkpoint workflow, make local commits only. No push/PR/release/history rewriting. Do not edit architecture documents unless a separate human authorization is given; report precise conflicts.

Acceptance: existing single_call behavior and contracts untouched; agent strategy selectable programmatically; valid output accepted by existing assembly; all intermediate work/decisions reconstructable after failure; ten rounds are a strict maximum, not a required count; user can read and modify the loop and the `.txt` guidance without agent framework knowledge.
