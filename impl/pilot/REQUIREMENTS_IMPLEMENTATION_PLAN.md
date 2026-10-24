# Requirements subsystem implementation plan

> **For agentic workers:** Execute one small task at a time, using the resumable checkpoint protocol below. If Superpowers is installed, its executing-plans workflow may be used; it is not a prerequisite. Do not start the next task without recording completion, tests, and the exact next action.

**Goal:** Extract several Annex VII provisions into a new timestamped working copy, edit those Requirements, and publish a valid Pack, then add working-copy selection, Compare, and Consolidator without a second persistent schema.

**Architecture:** Packs v2 JSON remains the only persisted Requirement and Pack shape. Extract writes a new dated directory of unsigned Requirements; editing, Compare, and Consolidator update only the selected writable copy; publication copies a validated, sealed copy to a new immutable release directory. `poc2/requirements/ARCHITECTURE.md` is the Requirements contract. The separate `poc2/extract/ARCHITECTURE.md` was removed on 2026-10-21 and does not override it. `poc/` is a functional and UX reference and is not imported.

**Tech Stack:** Python 3, existing `poc2/common` validation, canonical JSON, and Ed25519 signing, `unittest` launched from `poc2/`, current `http.server` entry in `poc2/app/server.py`.


## Resumable execution protocol (OptiCAP style — mandatory)

**Source of truth:** this tracked file at `impl/pilot/REQUIREMENTS_IMPLEMENTATION_PLAN.md`. The architecture files are authoritative for behavior; this plan is authoritative only for execution progress. No separate status database, chat memory, or hidden agent scratchpad.

**At the beginning of every Cursor session:**
1. Read the overall and Requirements architecture, the Packs v2 reference, and **this file**, starting with *Current checkpoint* below.
2. Inspect `git status --short` and recent commits; verify that the recorded completed checkpoint actually corresponds to code and passing tests. If state differs, update the checkpoint **before** further edits. Never assume a box is completed merely because it is checked.
3. Resume **only** the next named task or its smallest unfinished step. Do not refactor adjacent subsystems or execute the rest of the plan autonomously.

**At the end of each small task:**
1. Run the narrow test(s) specified for that task, then the relevant regression gate. Record the exact commands and PASS/FAIL; don't report green without executing them.
2. Commit local code/tests/documentation if authorized by the user's normal Git policy. Never push, open PR, tag, publish, release, or modify remotes without express permission. If a commit is unsafe or forbidden, record why and the uncommitted files instead.
3. Update the task's `[x]` checklist **and the Current checkpoint**: finished task/step, changed files, local commit SHA (or uncommitted state), test result, known issues, and **exact next task/step**. Commit the plan checkpoint along with the task, or immediately after if necessary.
4. Respond to the user with a short outcome: DONE / tests / next / blocker. Stop at the planned checkpoint.

**On interruption, context loss, shutdown, or token exhaustion:** update the checkpoint if possible before stopping. If not possible, the next session reconciles the checkpoint with the working tree, tests, and Git history. Never claim an interrupted step finished. Incomplete code stays labelled WIP. A checkpoint must be useful even when the chat history is unavailable.

**Scope and cadence:** prefer one verifiable behavior per task, with a test and a commit. If one task exceeds a reasonable single session, split it into numbered substeps in this document, preserving the acceptance criteria. After every milestone, demonstrate the functioning vertical slice rather than merely the directory layout.

### Current checkpoint (Cursor updates this in place)

| Field | Value |
| --- | --- |
| Plan state | IN PROGRESS — Task 20 walkthrough **not** complete. Annex VII quality experiment **stopped** after three prompt revisions. Conclusion: improved, not recovered. Local commits only. Branch `main`. Do not push. All `ARCHITECTURE.md` files are read-only, except the completed 2026-10-21 removal of `poc2/extract/`. |
| Current phase/task | Task 20 still open (human walkthrough). Quality experiment finished. Not Task 21. |
| Last completed task | Bounded CRA prompt experiment. Best guidance is revision r2, left in the cra-xml prompt files. Reference pack commit `d8c743ac2360bd232b326635ff2e66defcc62f8f`. |
| Last verified local commit | Experiment `e6ff438dd7ef6b1f3bdaa32a148f59c96108c2a1`. Reference JSON `d8c743ac2360bd232b326635ff2e66defcc62f8f`. Reference provenance `4dc03a25a4a9a5954b780f29fc0308a80b198c6e`. |
| Uncommitted files | Pre-existing unrelated: untracked `poc2/AGENTS.md`; dirty `poc/data/**`; `.DS_Store`, `daniel/`, `docs/superpowers/`, `poc2/poc2/`, `poc2.zip`, `poc2/requirements.zip`. New working copies stay gitignored under `poc2/data/workspace/`. |
| Last tests and result | `cd poc2 && .venv/bin/python -m unittest tests.test_requirements_produce tests.test_requirements_extract tests.test_xml_adapters` — PASS, 26 tests. `cd poc2 && .venv/bin/python -m unittest discover -s tests` — PASS, 96 tests (outside the sandbox; a sandboxed run failed 3 git-init tests). |
| Active blocker/decision | Task 20 human walkthrough still open. Do **not** mark Task 20 done; do **not** start Task 21. Do not continue prompt iteration. Hardware applicability and VII.5 `MUST` are still missing from the prompt experiment. The reference is not a certified gold standard. Side plan `impl/pilot/AGENT_LOOP_EXPERIMENT.md` recorded the revise-loop subset run. It did not add `agent_loop` and did not edit `ARCHITECTURE.md`. |
| **Exact next action** | Human Task 20 walkthrough. Do not start Task 21. Do not run a fourth prompt revision. |

**Architecture cleanup (2026-10-21):** removed `poc2/extract/` (`ARCHITECTURE.md` and the empty `__init__.py`). Extract stays a component of `poc2/requirements/`. Task 20 is not done. This is not Task 21. `cd poc2 && .venv/bin/python -m unittest discover -s tests` — 148 tests, 2 failures, 2 errors. The failures are `test_requirements_ui` and `test_ui_smoke` looking for old page text, and the errors are `test_discover_feedback` and `test_pilot_pack_selection`. None of them import `poc2/extract/`.

**Side task decision (2026-10-13) — home / active Pack / thin Discover:**

Approved thin integration (not Task 21, Task 20 stays open):

1. Reuse operational `selection.json` with unambiguous identity: working `{kind, pack_id, timestamp}` and published `{kind, pack_id, version}`. Legacy `{pack_id, timestamp}` remains a working selection. Explicit selection is stable; latest working copy (else published) is only the initial default when nothing resolves.
2. Home is a compact pilot hub (Requirements, Discover, Claims, Check, Review); Scaffold/Prepare are secondary. Selector lists real filesystem working copies and published Packs. Sample/demo pack is never the active pilot Pack unless explicitly chosen.
3. Pilot Discover loads Requirements only from the selected Pack directory; hunt config is read from existing `curbpack.json` without using or rewriting its Pack selection. Multi-Requirement Packs require an explicit Requirement choice (no silent default). Check/Review stay on authoritative `curbpack.json` / existing demo semantics.
4. No new Pack registry, no parallel design doc under `docs/superpowers/specs/`, no Discovery redesign (batch, voting, assessment). Browser verification uses existing real working copies; a new successful LLM extract is not a dependency.

**Side task result (2026-10-13):**

Implemented: `list_pack_options` / published selection on operational `selection.json`; home hub with Active Pack selector; Requirements opens selected Pack (`/requirements/copy`, published read-only); Discover loads Requirements only from selected Pack, requires explicit Requirement id, hunt from `curbpack.json` without using its `packs` list. Check/Review unchanged. Scaffold/Prepare under Developer.

Tests: `tests/test_pilot_pack_selection.py`, updated `test_cover_navigation.py` and `test_ui_smoke.py`. Full suite PASS, 96 tests.

Browser: temp workspace copied from real `cra-xml-baseline` `2026-10-13T134627Z` + `2026-10-13T141531Z` (no new LLM run). Default selected latest `141531Z`; Discover listed 13 Requirements and ran candidates for `CRA-PROVISION-3-RISK-ASSESSMENT` → `docs/risk-notes.md`; explicit switch to `134627Z` preserved; `curbpack.json` packs list stayed `["other"]`.

Limitation (honest): pilot Discover is thin (chooser + `discover_candidates` only). Full Discovery UX is not done. Sample `packs/cra-baseline` after Prepare is not listed as a pilot Pack (intentional).

### Phase 0 findings (2026-10-13)

No production code in this step. These readings are the limited scope for later tasks. They do not add a schema.

1. **Signing.** `curbpack/docs/reference/packs2.md` §2.2 requires `signed` on a published Requirement and omits `origin` on the publisher's Requirement. `poc2/common/validate.py` `validate_requirement(..., published=True)` already requires `signed`, rejects `origin`, and requires `source.edition`. `published=False` allows an unsigned draft. `validate_pack(..., sealed=True)` requires the pack `signed` block. `read_signature` does not consult Git; its unsigned reason text mentions a signed Git commit, but no lookup exists. Open contract 3 stays closed for implementation: no task adds a Git-path lookup. Task 6 publication uses `published=True` for each Requirement and requires the directory seal. An absent `signed` fails that publication check. It does not make a working-copy draft invalid.
2. **Paths.** Requirements owns path order. The overall architecture example that grouped timestamp then pack id was illustrative and disagreed with `requirements/ARCHITECTURE.md`. This step changes only that example in `docs/arch/ARCHITECTURE.md` to `<root>/<pack-id>/<YYYY-MM-DDTHHMMSSZ>/` and `published/<pack-id>/<version>/`. Diagnostics stay outside the sealed directory. The plan's sibling `<timestamp>.work/` and `jobs/` locations are the implementation choice the Requirements document leaves open. They are not Packs v2 fields.
3. **Coverage publication is decided.** See open contract 2. Coverage stays diagnostic. It is not a publication gate, and a release does not certify complete legal coverage.
4. **Ids.** Further CRA loci still have no naming convention. Tests pass `FIXTURE-VII-1A` and `VII.1(a)` as caller inputs.
5. **Baseline imports.** Tests run from `poc2/` with `.venv/bin/python`. Domain imports are `common.*`, `extract.pipeline`, `extract.atomize`, `requirements.editing`. `extract_annex_vii_risk` and `PUBLISHED_LOCUS` still publish only locus `3`.
6. **Task splits (acceptance unchanged).** Task 0 is the behavior-preserving Extract move and is the first implementation task. Task 6 is executed as 6a two signed Requirements publish and a repeat is refused, 6b an unsigned Requirement is refused, 6c a tampered `signed` block is refused, 6d coverage publication is not coded until open contract 2 is confirmed, 6e full `unittest discover -s tests`. Task 9 is executed as 9a catalog GET, 9b select, 9c editor GET and hint save, 9d extract POST until `done`, 9e browser walk of the new catalog and the old prepare-to-review path.

## Phase 0 — Contract and baseline gate (before Task 1)

- [x] Verify normative `packs2.md` vs implementation assumptions, especially whether publisher Requirements need individual `signed` blocks, pack directory seal behavior, `origin`, and published validation. Do **not** strengthen signing policy by accident.
- [x] Reconcile the one working-copy directory layout with the overall architecture; change misleading doc examples only, no application code.
- [x] Record the coverage/publication question as unresolved (open contract 2). Every discovered provision is accounted for as written, deliberately excluded, failed, or unprocessed. Whether any of those cases blocks publication is not decided. No approval schema and no blanket prohibition on deliberately excluded provisions.
- [x] Check all current tests and capture the baseline. Note current code/import paths.
- [x] Break any oversized task into small testable checkpoints in this file. Update *Current checkpoint* with the exact next action.

**Gate:** no production code before genuine specification contradictions are resolved or explicitly marked as limited scope with a human decision.

## Global Constraints

These apply to every task. Values are taken from the Requirements specification and `packs2.md`.

- Persist Pack, Requirement, `signed`, and `origin` only as `curbpack/docs/reference/packs2.md` defines them. A dated extraction directory is deployment storage, not a Packs v2 field.
- An extracted Requirement is unsigned and has no `origin`. `origin` is set only by the existing `working_copy` / `accept_published_version` operations on a published Requirement.
- The extraction timestamp is not `pack.version`, `origin.version`, or a Requirement version. There is no Requirement version counter.
- Do not read or write `decisions.json`. Do not implement replay, clean-rebuild-from-decisions, or `accept_assembled`.
- Do not persist `ClaimDraft`, `ConsolidationDecision`, a comparison object, or a job record inside a directory that will be sealed.
- Forbidden Requirement fields stay forbidden: top-level `law_text`, `search`, `claim`, `locus`, and the other names in `FORBIDDEN_REQUIREMENT_FIELDS`.
- `source.edition` is absent on adapter output and on a newly extracted draft. It is required when `validate_requirement(..., published=True)` runs.
- `references[].nr` is `1..n` in array order. The editor assigns it. The form does not submit it.
- A payload change drops `signed`. A no-op edit keeps `signed`.
- Stages 00, 01, and 04 do not call a model. Stages 02 and 03 are the only model stages.
- A stub adapter refuses stages 01–04. The product UI does not pass a developer pressure-test override.
- UI modules render and collect input. Filesystem traversal, validation, signing, and publication rules stay in ordinary Python functions.
- Do not import `poc/`. Do not modify `poc/`.
- Do not create empty component directories. Task 0 moves the existing Extract modules and their data. Later tasks add files under `poc2/requirements/extract/` rather than recreating `poc2/extract/` code.
- All `ARCHITECTURE.md` files are read-only during implementation, as `policies/development.md` requires. Record documentation conflicts in this plan. Do not edit an architecture file to remove one.
- Existing checks, claims, discovery, compile, and review keep reading a Pack directory of `pack.json` plus Requirement JSON files.
- Local signing stays Ed25519 via `common.keystore`. The UI sentence remains: "Local Ed25519 keys are created when someone signs. They are not X.509 certificates."

---

## What already works and stays

Reuse these. Do not rewrite them to fit a directory diagram.

| Existing code | Reuse for |
| --- | --- |
| `poc2/requirements/extract/atomize.py` | CRA stage 01, after Task 0. It already emits one provision per numbered point and lettered clause, with `locus` and wrapped `law_text`. |
| `poc2/requirements/extract/data/annex_vii.txt` | Controlled Annex VII fixture. The locus maps move with it and are not deleted in Task 0. |
| `poc2/requirements/extract/pipeline.py` `discovery_hints_from_search` | Shape conversion when a proposal still carries PoC1 string `sources`. New product code does not load the map files as an approval replay. |
| `poc2/requirements/extract/pipeline.py` `draft_pack` | Pack metadata for the current CRA sample (`id` `cra-baseline`, `version` `0.1.0`). Callers pass it in. Extract does not invent a second version. |
| `poc2/common/validate.py`, `store.py`, `jsonio.py`, `canonical.py`, `signing.py`, `errors.ModelError` | The only validation, IO, digest, and seal implementation. |
| `poc2/requirements/editing.py` `publish_requirement`, `approve_working_copy`, `working_copy`, `accept_published_version`, `seal_pack_directory`, `read_pack_seal` | Packs v2 signing. `working_copy` means "local copy with `origin`", which is a different operation from a dated extraction directory. |
| `poc2/tests/test_e2e_annex_vii.py`, `test_m2_discovery.py`, `test_m3_claims.py`, `test_m4_checks.py`, `test_ui_smoke.py` | Regression gate. They must pass at the end of every phase. |
| `poc2/demo_setup.py`, `poc2/workflow.py`, `poc2/app/server.py` | Current demo path. Phases 1–4 leave `data/workspace/packs/cra-baseline` as the pack that discovery, checks, and review already load. |

`poc2/requirements/extract/pipeline.py` `PUBLISHED_LOCUS` publishes only locus `3`. That gate is the behavior Phase 1 replaces for the new extract path. `poc2/requirements/extract/data/claims_by_locus.json` stores PoC1 claim slugs (`vii-3`, `vii-1a`). Those slugs are not Requirement ids. Task 0 moves these files and does not delete them. `poc2/app/pages.py` `requirement_page` shows one reference and drops `discovery_hints.sources[].args` on save. Phase 2 replaces that form.

PoC1 behavior to reimplement, without its files: catalog listing, extract progress modal (`running`, `done`, `failed`, `aborted`, last 200 log lines, Abort), and an editor that can show every reference and field. Source of the UX: `poc/components/requirement_manager/ui.py`, `cli_job.py`, and `edit_desk.py`. Do not import them.

## Storage layout used by this plan

`docs/arch/ARCHITECTURE.md` draws `internal/data/<timestamp>/<pack-id>/`. `poc2/requirements/ARCHITECTURE.md` draws `<root>/<pack-id>/<timestamp>/` plus `published/<pack-id>/<version>/`, and the overall document assigns path detail to the Requirements specification. This plan follows the Requirements specification.

The workspace root is a function argument. It is not stored on a Requirement.

```text
<root>/
  <pack-id>/
    <YYYY-MM-DDTHHMMSSZ>/
      pack.json
      <requirement-id>.json
    <YYYY-MM-DDTHHMMSSZ>.work/
      provisions.json
      coverage.json
      llm.json                 # only after a model stage has run
  published/
    <pack-id>/
      <version>/
        pack.json
        <requirement-id>.json
  jobs/
    <job-id>.json
```

`*.work/` and `jobs/` are operational files. `publish_pack` copies only `pack.json` and Requirement JSON files. Timestamp names use UTC with no colons, matching the Requirements example `2026-10-13T090000Z`. `create_extraction_copy` creates the directory with `mkdir` that fails if the name exists. It never opens an existing directory for writing. When the caller omits the timestamp, a same-second collision retries the next second, at most five times, and then raises `ModelError`.

`coverage.json` is **diagnostic run output**, not a new domain schema or a legal approval record. Its exact key layout is provisional: keep existing test assertions as examples until the coverage contract is agreed. It must account for every source provision (written, explicitly excluded, failed, or still unprocessed), with a reason for anything not written. A run with omissions must display **incomplete coverage**, not an unqualified success. Do not silently promote excluded provisions to published legal coverage.

## Open contracts

Do not invent a persistent schema or a Requirement id convention to close these. Implementation of the phases below does not depend on closing them, except where a task says it is blocked.

1. **Requirement `id` and `references[].locator` for Annex VII loci other than point 3.** `packs2.md` and the current code specify only `CRA-ANNEX-VII-RISK` / `VII.3`. The Requirements specification says to confirm the convention for further loci and not to guess from PoC1 claim slugs. Phase 1 assemble takes `id` and `locator` from the caller-supplied proposal. Tests that need a second Requirement use the literals `FIXTURE-VII-1A` and `VII.1(a)` and state in the test docstring that those literals are pipeline inputs, not the CRA naming convention. No adapter id table is added.

2. **Coverage and intentional scope exclusions. Decided 2026-10-13.** Coverage is diagnostic and must remain complete, truthful, and inspectable. Deliberately excluded, failed, and unprocessed source provisions must remain distinguishable. Coverage status alone is not a publication gate. Do not infer that publication certifies complete legal coverage. Do not invent an approval object or a new persistent domain schema.

   Reconciliation, not a contradiction: `requirements/ARCHITECTURE.md` §2 says a failed or partial extract is not a silently publishable Pack and must not be exposed as ready. That governs how the run is presented. §8 publication checks pack metadata, included Requirements, and Packs v2 seals. It does not say `coverage.json` status blocks `publish_pack`. `packs2.md` still requires `signed` on a published Requirement, no `origin` on the publisher's Requirement, and `source.edition` when published. Task 6 follows those rules. No architecture file was edited.

3. **Signed Git commit as a seal when `signed` is absent.** `packs2.md` §2.6 specifies the five facts. It does not say which repository or path `read_signature` should inspect. `common.signing.read_signature` does not consult Git today. No phase adds that lookup.

4. **Working-copy path order.** Keep the pack-first layout in `requirements/ARCHITECTURE.md`: `<root>/<pack-id>/<YYYY-MM-DDTHHMMSSZ>/` and `published/<pack-id>/<version>/`. The illustrative edit in `docs/arch/ARCHITECTURE.md` (`fd406a4`) is an accepted one-time exception. Further `ARCHITECTURE.md` edits are not allowed during implementation.

5. **Extract's old architecture file is removed.** `docs/arch/ARCHITECTURE.md` no longer points at `poc2/extract/ARCHITECTURE.md`. That file and `poc2/extract/` were removed on 2026-10-21. Do not implement its `decisions.json` or replay sections, and do not recreate the file.

`pack.version` on the working copy and the version passed to `publish_pack` must be the same string. The user saves that version onto the working copy, seals the directory, then publishes. Publication copies bytes. It does not rewrite `pack.version` inside the release, because a rewritten `pack.json` would no longer match the directory seal.

## File map

Task 0 moves existing code only:

- `poc2/extract/atomize.py` → `poc2/requirements/extract/atomize.py`
- `poc2/extract/pipeline.py` → `poc2/requirements/extract/pipeline.py`
- `poc2/extract/data/` → `poc2/requirements/extract/data/` (`annex_vii.txt`, `claims_by_locus.json`, `search_by_locus.json`)

Task 0 left `poc2/extract/ARCHITECTURE.md` in place. The 2026-10-21 cleanup removed that file with the directory. Do not recreate it.

Phase 1 creates:

- `poc2/requirements/extract/adapter.py` — load `adapter.json`, stage 00, refuse stubs.
- `poc2/requirements/extract/adapters/cra/adapter.json`
- `poc2/requirements/extract/adapters/nis/adapter.json`
- `poc2/requirements/extract/adapters/medtech/adapter.json`
- `poc2/requirements/assemble.py` — validate proposals and build unsigned Requirements.
- `poc2/requirements/workspace.py` — dated copies and `publish_pack`.
- `poc2/tests/test_requirements_extract.py`
- `poc2/tests/test_requirements_publish.py`

Phase 1 modifies `poc2/requirements/editing.py` and `poc2/requirements/extract/pipeline.py`. Atomize stays at `poc2/requirements/extract/atomize.py`.

Phase 2 creates `poc2/requirements/jobs.py` and `poc2/requirements/ui/pages.py`, and modifies `poc2/app/server.py` only to route. Phase 3 creates `poc2/requirements/compare.py`. Phase 4 creates `poc2/requirements/consolidate.py`. Phase 5 creates `poc2/requirements/produce.py` for model calls. Phase 6 does not repeat Task 0. It does not delete the map files and it does not edit `ARCHITECTURE.md`.

## Task 0 — Move existing Extract code without changing behavior

This is the first implementation task. It does not add adapters, assembly, working copies, or publication.

**Files:**

- Move: `poc2/extract/atomize.py`, `poc2/extract/pipeline.py`, and `poc2/extract/data/` to `poc2/requirements/extract/`
- Modify imports in `pipeline.py`, `poc2/demo_setup.py`, and the tests that import `extract.pipeline`
- Leave in place: `poc2/extract/ARCHITECTURE.md`, both locus map files, atomizer expressions, `PUBLISHED_LOCUS`, `draft_pack`, and `extract_annex_vii_risk`

The only code edit inside the moved modules is `from extract.atomize import atomize` becoming `from requirements.extract.atomize import atomize`. Call sites import `requirements.extract.pipeline`. Do not add an empty package file unless that import fails.

- [x] **Step 1: Move the modules and data, and update those imports.**

- [x] **Step 2: Run the existing suite**

Run from `poc2/`: `.venv/bin/python -m unittest discover -s tests -v`

Expected: PASS, 19 tests. The same assertions as before the move. Result: PASS, 19 tests.

- [x] **Step 3: Commit, update this checkpoint, and stop.**

Do not start Task 1 in this step.

```bash
git add poc2/requirements/extract poc2/extract/atomize.py poc2/extract/pipeline.py poc2/extract/data poc2/demo_setup.py poc2/tests/test_m1_requirement.py poc2/tests/test_m2_discovery.py poc2/tests/test_m3_claims.py poc2/tests/test_m4_checks.py poc2/tests/test_e2e_annex_vii.py impl/pilot/REQUIREMENTS_IMPLEMENTATION_PLAN.md
git commit -m "$(cat <<'EOF'
Move existing Extract code under Requirements without changing behavior.

The Annex VII fixture and locus maps move with the code, and the existing tests import the new path.
EOF
)"
```

### Documentation conflicts for human review

Do not edit these files while implementing.

1. `docs/arch/ARCHITECTURE.md` current-path table still lists Extract at `poc2/extract/` (+ `extract/ARCHITECTURE.md`). After Task 0 the code and data are at `poc2/requirements/extract/`. The target column already names that path. The current-path cell is stale until a human edits it.
2. `poc2/extract/ARCHITECTURE.md` stays in `poc2/extract/` and still describes that tree, including `decisions.json`. It is historical. Do not copy that contract into `requirements/ARCHITECTURE.md`, and do not replace the file with a pointer during implementation.
3. The uncommitted working copy of `poc2/requirements/ARCHITECTURE.md` still names `poc2/extract/data/annex_vii.txt` as the current fixture path. After Task 0 that file is `poc2/requirements/extract/data/annex_vii.txt`.
4. The old Phase 6 sentence that would add a line to `docs/arch/ARCHITECTURE.md` is not executed. Architecture files stay read-only under `policies/development.md`.

**Resolved 2026-10-21.** An authorised cleanup removed `poc2/extract/`, including `ARCHITECTURE.md`. Items 1 and 2 above record the conflict at Task 0. They are not an instruction to keep that file. The current-path row in `docs/arch/ARCHITECTURE.md` lists Extract at `poc2/requirements/extract/`. The fixture path in `poc2/requirements/ARCHITECTURE.md` is `poc2/requirements/extract/data/annex_vii.txt`. Item 4 still stands for other architecture edits.

## Phase 1 — Dated copy, several Requirements, edit, publish

This phase is the vertical slice. It is callable from tests without HTTP. The existing demo UI keeps serving the single prepared Requirement from `data/workspace/packs/cra-baseline`.

### Task 1: Adapter load and stage 00

**Files:**

- Create: `poc2/requirements/extract/adapter.py`
- Create: `poc2/requirements/extract/adapters/cra/adapter.json`
- Create: `poc2/requirements/extract/adapters/nis/adapter.json`
- Create: `poc2/requirements/extract/adapters/medtech/adapter.json`
- Test: `poc2/tests/test_requirements_extract.py`

**Interfaces:**

- Consumes: `common.errors.ModelError`, `common.jsonio.read_json`
- Produces:
  - `load_adapter(path: Path) -> dict`
  - `stage00(adapter: dict, *, dump_text: str | None = None) -> dict` returning `{ "sections": [ { "id", "in_scope", "ready", "text_file"? } ] }`
  - `section_text(adapter_dir: Path, adapter: dict, section_id: str) -> str`
  - `ADAPTERS = Path(__file__).resolve().parent / "adapters"`

CRA `adapter.json` uses the scope flags in `requirements/ARCHITECTURE.md` §4.1.2. `sections[].fixture` for VII is `../../data/annex_vii.txt` so the controlled file stays where it is. Optional `title` values may be copied from `poc/components/transform/adapters/cra/adapter.yml`. Do not copy PoC1 `hunt` flags. NIS2 and Medtech are `{ "id": "nis"|"medtech", "status": "stub", "sections": [] }`.

- [x] **Step 1: Write the failing test**

```python
def test_stub_adapter_refuses_section_text(self):
    adapter = load_adapter(ADAPTERS / "nis" / "adapter.json")
    with self.assertRaises(ModelError):
        section_text(ADAPTERS / "nis", adapter, "VII")

def test_cra_stage00_lists_annex_vii_ready(self):
    adapter = load_adapter(ADAPTERS / "cra" / "adapter.json")
    listed = stage00(adapter)
    vii = next(item for item in listed["sections"] if item["id"] == "VII")
    self.assertTrue(vii["in_scope"])
    self.assertTrue(vii["ready"])
    self.assertIn("cybersecurity risks", section_text(ADAPTERS / "cra", adapter, "VII"))
```

- [x] **Step 2: Run test to verify it fails**

Run from `poc2/`: `.venv/bin/python -m unittest tests.test_requirements_extract -v`

Expected: FAIL with `load_adapter` not defined. Result: FAIL, `ModuleNotFoundError: No module named 'requirements.extract.adapter'`.

- [x] **Step 3: Implement load and stage 00**

`load_adapter` checks the fields required by §4.1.1. Duplicate section ids, a non-boolean `in_scope` or `ready`, or a ready section with a missing fixture raise `ModelError` naming the adapter id and the field. `stage00` without `dump_text` returns the adapter sections and sets `text_file` from `fixture` when present. `stage00` with `dump_text` is not implemented in this task; raise `ModelError` whose message says full-dump split is not implemented. That keeps the full-act splitter out of the first slice. `section_text` reads the fixture for a ready, in-scope section and raises `ModelError` for a stub adapter, a missing section, or a section that is not ready.

- [x] **Step 4: Run the test**

Expected: PASS for the two tests above. Result: PASS, 2 tests. Full suite PASS, 21 tests.

- [x] **Step 5: Commit**

```bash
git add poc2/requirements/extract/adapter.py poc2/requirements/extract/adapters poc2/tests/test_requirements_extract.py
git commit -m "$(cat <<'EOF'
Add CRA, NIS2, and Medtech adapter files for Requirements extract.

Stage 00 can list the CRA sections and refuse a stub before any Requirement is written.
EOF
)"
```

### Task 2: Proposal checks and stage 04 assemble

**Files:**

- Create: `poc2/requirements/assemble.py`
- Test: `poc2/tests/test_requirements_extract.py`

**Interfaces:**

- Consumes: `validate_requirement`, `ModelError`, stage 01 provisions `{ "locus", "law_text" }`
- Produces:
  - `validate_interpret_proposal(proposal: dict, loci: set[str]) -> dict`
  - `validate_hints_proposal(proposal: dict, loci: set[str]) -> dict`
  - `assemble_requirements(provisions: list[dict], proposals: list[dict], *, adapter: dict) -> tuple[list[dict], list[dict]]`
  - Return value: `(requirements, exclusions)` where each exclusion is `{ "locus": str, "reason": str }`

A proposal's allowed interpret fields are `locus`, `id`, `locator`, `note`, `strength`, `responsible`, `applicability`, `exceptions`, `scope`. Allowed hints fields are `locus` and `discovery_hints`. `assemble_requirements` merges the two kinds by `locus`. One Requirement is emitted only when that locus exists in `provisions` and the merged proposal has non-empty `id` and `locator` and passes `validate_requirement(..., published=False)`. Otherwise the locus is an exclusion. Provisions with no proposal are exclusions with reason `no proposal`. Extra proposal loci are exclusions with reason `unknown locus`. Duplicate loci in either list raise `ModelError` before any Requirement is returned.

Each written Requirement is:

```python
{
    "id": proposal["id"],
    "pack_id": adapter["pack_id"],
    "source": dict(adapter["source"]),  # no edition
    "references": [{"nr": 1, "locator": proposal["locator"], "law_text": provision["law_text"]}],
}
```

Copy `note`, the five properties, and `discovery_hints` only when the proposal has them. Do not copy `signed`, `origin`, `locus`, `claim`, or `search`. `law_text` comes from the provision, not from the proposal.

- [x] **Step 1: Write the failing test**

The sample below used locus `9` both as a provision ("not in the proposals") and as an extra proposal (`unknown locus`). Those are different cases. The test uses provision `8` for `no proposal` and proposal `9` for `unknown locus`.

```python
def test_assemble_writes_valid_proposals_and_lists_the_rest(self):
    provisions = [
        {"locus": "3", "law_text": "an assessment of the cybersecurity risks"},
        {"locus": "1(a)", "law_text": "a statement of the intended purpose"},
        {"locus": "8", "law_text": "not in the proposals"},
    ]
    proposals = [
        {"locus": "3", "id": "CRA-ANNEX-VII-RISK", "locator": "VII.3",
         "discovery_hints": {"concepts": ["risk assessment"]}},
        # Pipeline fixture only. Not a CRA id convention.
        {"locus": "1(a)", "id": "FIXTURE-VII-1A", "locator": "VII.1(a)"},
        {"locus": "9", "id": "SKIP", "locator": "VII.9"},
    ]
    requirements, exclusions = assemble_requirements(provisions, proposals, adapter=self.cra)
    self.assertEqual([item["id"] for item in requirements], ["CRA-ANNEX-VII-RISK", "FIXTURE-VII-1A"])
    self.assertNotIn("signed", requirements[0])
    self.assertNotIn("origin", requirements[0])
    self.assertNotIn("locus", requirements[0])
    self.assertEqual(requirements[0]["references"][0]["law_text"], provisions[0]["law_text"])
    self.assertEqual(
        exclusions,
        [
            {"locus": "8", "reason": "no proposal"},
            {"locus": "9", "reason": "unknown locus"},
        ],
    )
```

Add a second test that a proposal containing `claim` or `search` raises `ModelError`, and a third that a missing `id` excludes that locus and still returns the valid sibling.

- [x] **Step 2: Run the test**

Expected: FAIL with `assemble_requirements` not defined. Result: FAIL, `ModuleNotFoundError: No module named 'requirements.assemble'`.

- [x] **Step 3: Implement assemble**

Use `validate_requirement` for the success path. Build exclusions for incomplete loci. Do not write files in this function.

- [x] **Step 4: Run the test**

Expected: PASS. Result: PASS, 5 tests in `tests.test_requirements_extract`. Full suite PASS, 24 tests.

- [x] **Step 5: Commit**

```bash
git add poc2/requirements/assemble.py poc2/tests/test_requirements_extract.py
git commit -m "$(cat <<'EOF'
Assemble unsigned Requirements from validated proposals.

Incomplete loci stay in the exclusion list instead of being replayed from an approval file.
EOF
)"
```

### Task 3: Dated working copies

**Files:**

- Create: `poc2/requirements/workspace.py`
- Test: `poc2/tests/test_requirements_extract.py`

**Interfaces:**

- Consumes: `save_pack`, `load_pack_directory`, `validate_pack`, `ModelError`
- Produces:
  - `list_working_copies(root: Path, pack_id: str) -> list[str]`
  - `create_extraction_copy(root: Path, pack_id: str, pack: dict, *, at: str | None = None) -> Path`
  - `select_working_copy(root: Path, pack_id: str, timestamp: str) -> Path`
  - `load_working_copy(directory: Path) -> tuple[dict, list[dict]]`
  - `work_directory(copy_dir: Path) -> Path` returning the sibling `<timestamp>.work` path

`list_working_copies` returns timestamp directory names sorted ascending. The latest is the last item. It ignores `*.work` directories and `published/`. `create_extraction_copy` checks `pack["id"] == pack_id`, writes `pack.json` with `save_pack`, and does not write Requirement files. `select_working_copy` returns the path only when that directory exists and its `pack.json` id matches. It does not create or modify files. A missing copy or a mismatched pack id raises `ModelError`.

- [x] **Step 1: Write the failing test**

```python
def test_two_extract_directories_do_not_overwrite(self):
    root = Path(self.tmp.name)
    pack = draft_pack()
    first = create_extraction_copy(root, "cra-baseline", pack, at="2026-10-13T090000Z")
    second = create_extraction_copy(root, "cra-baseline", pack, at="2026-10-13T143000Z")
    marker = first / "REQ-A.json"
    marker.write_text("keep\n", encoding="utf-8")
    with self.assertRaises(ModelError):
        create_extraction_copy(root, "cra-baseline", pack, at="2026-10-13T090000Z")
    self.assertEqual(marker.read_text(encoding="utf-8"), "keep\n")
    self.assertEqual(
        list_working_copies(root, "cra-baseline"),
        ["2026-10-13T090000Z", "2026-10-13T143000Z"],
    )
    self.assertEqual(select_working_copy(root, "cra-baseline", "2026-10-13T090000Z"), first)
    with self.assertRaises(ModelError):
        select_working_copy(root, "cra-baseline", "missing")
    self.assertNotEqual(first, second)
```

- [x] **Step 2: Run the test**

Expected: FAIL with `create_extraction_copy` not defined. Result: FAIL, `ModuleNotFoundError: No module named 'requirements.workspace'`.

- [x] **Step 3: Implement directory allocation**

Use `Path.mkdir(parents=True, exist_ok=False)` for the timestamp directory. On `FileExistsError`, raise `ModelError` when `at` was supplied. When `at` is `None`, format `datetime.now(timezone.utc)` as `%Y-%m-%dT%H%M%SZ`, and on collision compute a timestamp one second later, up to five attempts.

- [x] **Step 4: Run the test**

Expected: PASS. The first directory's marker file is byte-identical. Result: PASS, 6 tests in `tests.test_requirements_extract`. Full suite PASS, 25 tests.

- [x] **Step 5: Commit**

```bash
git add poc2/requirements/workspace.py poc2/tests/test_requirements_extract.py
git commit -m "$(cat <<'EOF'
Allocate a new timestamped Pack working copy per extraction.

A second run keeps the earlier directory intact instead of replacing it.
EOF
)"
```

### Task 4: Extract into the new copy

**Files:**

- Modify: `poc2/requirements/workspace.py`
- Modify: `poc2/requirements/extract/pipeline.py`
- Test: `poc2/tests/test_requirements_extract.py`

**Interfaces:**

- Consumes: `atomize`, `section_text`, `assemble_requirements`, `create_extraction_copy`, `save_requirement`, `write_json`
- Produces:
  - `extract_section(root, adapter_dir, adapter, section_id, proposals, pack, *, at=None, llm_notes=None) -> dict`
  - Return shape: `{ "copy": Path, "work": Path, "requirements": list[dict], "exclusions": list[dict] }`
  - `llm_notes` is `None` in this phase. Task 14 passes the stage 02/03 note list and then writes `llm.json`. Passing `None` writes no `llm.json`.

`extract_section` calls `section_text`, then `atomize`, then maps atoms to `{ "locus", "law_text" }` only. It creates the dated directory, writes each assembled Requirement with `save_requirement(..., published=False)`, and writes `provisions.json` and `coverage.json` under `work_directory`. A stub adapter raises before `create_extraction_copy`. If `save_requirement` raises, leave the copy and the work directory in place, write `coverage.json` with `"status": "failed"` and the error text, and re-raise. A finished **process** may report that execution ended, but `coverage` must explicitly be incomplete whenever `exclusions` are non-empty. Never label such coverage complete without an explicit, documented scope decision.

`extract_annex_vii_risk` remains the one-Requirement helper used by current tests. Reimplement it by calling `atomize` on the fixture, building one proposal for locus `3` with id `CRA-ANNEX-VII-RISK`, locator `VII.3`, and the discovery hints the existing test already asserts (`risk assessment`, `*risk*assessment*`, `*THREAT*`, `sources[0] == {"source": "documents"}`), then `assemble_requirements`, and return that Requirement. Do not read `claims_by_locus.json` or `search_by_locus.json` on this path. Delete `PUBLISHED_LOCUS` and `extraction_rows` once `tests/test_m1_requirement.py` no longer calls `extraction_rows`. Update `test_atomizer_still_finds_every_mapped_locus` to call `atomize` and expect the same locus list without `temporary_claim`.

- [x] **Step 1: Write the failing test**

```python
def test_extract_section_writes_two_requirements_in_a_new_copy(self):
    raw = (ADAPTERS / "cra").joinpath("../../data/annex_vii.txt").resolve()
    text = raw.read_text(encoding="utf-8")
    atoms = {item["locus"]: item["law_text"] for item in atomize(text)}
    proposals = [
        {"locus": "3", "id": "CRA-ANNEX-VII-RISK", "locator": "VII.3",
         "discovery_hints": {"concepts": ["risk assessment"],
                             "path_hints": ["*risk*assessment*", "*THREAT*"],
                             "sources": [{"source": "documents"}]}},
        {"locus": "1(a)", "id": "FIXTURE-VII-1A", "locator": "VII.1(a)"},
    ]
    result = extract_section(Path(self.tmp.name), ADAPTERS / "cra", self.cra, "VII",
                             proposals, draft_pack(), at="2026-10-13T090000Z")
    pack, requirements = load_working_copy(result["copy"])
    self.assertEqual(pack["id"], "cra-baseline")
    self.assertEqual({item["id"] for item in requirements}, {"CRA-ANNEX-VII-RISK", "FIXTURE-VII-1A"})
    by_id = {item["id"]: item for item in requirements}
    self.assertEqual(by_id["FIXTURE-VII-1A"]["references"][0]["law_text"], atoms["1(a)"])
    coverage = json.loads((result["work"] / "coverage.json").read_text(encoding="utf-8"))
    self.assertEqual(coverage["status"], "incomplete")
    written = [row["locus"] for row in coverage["loci"] if row["status"] == "written"]
    self.assertEqual(sorted(written), ["1(a)", "3"])
    self.assertTrue(any(row["status"] == "excluded" for row in coverage["loci"]))
```

Add `test_second_extract_leaves_the_first_copy_byte_identical`: run twice with different `at` values, snapshot the first copy's file bytes, and compare after the second run.

- [x] **Step 2: Run the test**

Expected: FAIL with `extract_section` not defined. Result: FAIL, `ImportError: cannot import name 'extract_section'`.

- [x] **Step 3: Implement extract_section and reimplement extract_annex_vii_risk**

Keep `draft_pack` and `discovery_hints_from_search`. The latter stays available for a caller that still has a PoC1 search object. The product extract path does not call it.

- [x] **Step 4: Run the Requirements tests and the existing M1 test**

Run: `.venv/bin/python -m unittest tests.test_requirements_extract tests.test_m1_requirement -v`

Expected: PASS. `extract_annex_vii_risk` still returns unsigned `CRA-ANNEX-VII-RISK` with locator `VII.3` and no `edition`. Result: PASS, 16 tests. Full suite PASS, 27 tests.

- [x] **Step 5: Commit**

```bash
git add poc2/requirements/workspace.py poc2/requirements/extract/pipeline.py poc2/tests/test_requirements_extract.py poc2/tests/test_m1_requirement.py
git commit -m "$(cat <<'EOF'
Write every valid Annex VII proposal into its own working copy.

The point-3 helper no longer depends on claim-slug maps or an approval replay.
EOF
)"
```

### Task 5: Edit rules required by the slice

**Files:**

- Modify: `poc2/requirements/editing.py`
- Test: `poc2/tests/test_requirements_publish.py`

**Interfaces:**

- Consumes: `version_digest`, `validate_requirement`, `common.store.save_requirement`
- Produces:
  - `apply_edits` (updated): drop `signed` only when `version_digest` changes
  - `assign_reference_numbers(references: list[dict]) -> list[dict]`
  - `save_working_requirement(directory: Path, requirement: dict, *, expected_digest: str) -> Path`

`save_working_requirement` loads the existing `<id>.json` when it is present. If `version_digest` of that file differs from `expected_digest`, raise `ModelError` and leave the file bytes unchanged. Then call `common.store.save_requirement`. Do not add this check to `common.store.save_requirement`; discovery, claims, and the current demo keep that function.

`assign_reference_numbers` sets `nr` to `1..n` and preserves `locator` and `law_text`.

- [x] **Step 1: Write the failing test**

```python
def test_same_value_edit_keeps_signed_and_stale_save_does_not_write(self):
    private, public = generate_keypair()
    requirement = publish_requirement(
        _with_edition(extract_annex_vii_risk()),
        name="Ada Jurist", private_key=private, at="2026-10-12T09:00:00Z",
    )
    again = apply_edits(requirement, {"remediation_hint": requirement["remediation_hint"]})
    self.assertEqual(again["signed"], requirement["signed"])
    changed = apply_edits(requirement, {"remediation_hint": "A different hint."})
    self.assertNotIn("signed", changed)
    self.assertEqual(changed["discovery_hints"], requirement["discovery_hints"])
    root = Path(self.tmp.name)
    save_pack(root, draft_pack())
    save_requirement(root, requirement, published=True)
    digest = version_digest(requirement)
    save_working_requirement(root, changed, expected_digest=digest)
    with self.assertRaises(ModelError):
        save_working_requirement(root, requirement, expected_digest=digest)
    self.assertEqual(load_requirement(root / "CRA-ANNEX-VII-RISK.json")["remediation_hint"], "A different hint.")
```

Add a test that two references saved through `assign_reference_numbers` reload as `nr` 1 and 2, and that `discovery_hints.sources[0].args` is unchanged when the edit dict omits `discovery_hints`.

- [x] **Step 2: Run the test**

Expected: FAIL because `apply_edits` currently removes `signed` whenever `edits` is non-empty, and `save_working_requirement` does not exist. Result: FAIL, `ImportError: cannot import name 'assign_reference_numbers'`.

- [x] **Step 3: Implement the digest check**

Apply field changes on a copy. If `version_digest` equals the input digest, return a deep copy of the input, including `signed`. Otherwise remove `signed` and validate with `published=False`.

- [x] **Step 4: Run M1 and the new publish tests**

Run: `.venv/bin/python -m unittest tests.test_m1_requirement tests.test_requirements_publish -v`

Expected: PASS. Existing tests that change a field still see `signed` removed. Result: PASS, 10 tests. Full suite PASS, 29 tests.

- [x] **Step 5: Commit**

```bash
git add poc2/requirements/editing.py poc2/tests/test_requirements_publish.py
git commit -m "$(cat <<'EOF'
Keep a Requirement signature when an edit does not change the payload.

A save into a working copy fails when the file changed since it was read.
EOF
)"
```

### Task 6: Publish an immutable release

**Files:**

- Modify: `poc2/requirements/workspace.py`
- Test: `poc2/tests/test_requirements_publish.py`

**Interfaces:**

- Consumes: `load_working_copy`, `read_pack_seal`, `read_signature`, `validate_requirement(..., published=True)`
- Produces: `publish_pack(root: Path, copy_dir: Path, *, version: str, trust: dict[str, bytes]) -> Path`

Behavior:

1. Load the working copy. Require `pack["version"] == version`.
2. Validate each included Requirement against the applicable `packs2.md` publishing rules and verify every **present** signature and the required Pack directory seal. Distinguish unsigned-but-valid Requirements from invalid signatures; do not invent a universal requirement that all Requirements be individually signed if Packs v2 allows them unsigned. Reject zero-Requirement publication for the PoC2 1.0 workflow unless explicit spec says otherwise. Do not implement a coverage publication rule in this task. Open contract 2 must be confirmed first. The run accounting still distinguishes deliberate exclusions from extraction failures.
3. Destination is `root / "published" / pack["id"] / version`. If it exists, raise `ModelError` and do not write.
4. Copy `pack.json` and Requirement files into `root / ".publish-tmp-<token>"`. Validate that temporary directory the same way. `os.rename` it to the destination. `os.rename` fails if the destination appeared in between; catch that, delete the temp directory, and raise `ModelError`.
5. On any failure before the rename, delete the temp directory if it exists. The destination path must be absent. The source copy's bytes stay as they were.

A Requirement missing a required `source.edition` or carrying an invalid publisher-side `origin` fails publication under the applicable Packs v2 rule. An absent `signed` field is **not by itself** evidence of an invalid Pack; follow `packs2.md` and verify the directory seal. Confirm the exact validation mode from the normative validator before coding.

- [x] **Step 1: Write the failing test**

Build a copy with two signed Requirements (point 3 and `FIXTURE-VII-1A`), both with `edition` set, seal the directory, and call `publish_pack(..., version="0.1.0", trust=trust)`. Assert the destination contains both ids, the source copy's file bytes are unchanged, and a second call with the same version raises while the destination bytes stay identical. A variant with the second Requirement left unsigned asserts behavior **according to the verified Packs v2 rule** (not an invented policy); a variant with a tampered existing signature must fail.

- [x] **Step 2: Run the test**

Expected: FAIL with `publish_pack` not defined. Result: ERROR, `ImportError: cannot import name 'publish_pack'`.

- [x] **Step 3: Implement publish_pack**

Copy bytes. Do not call `publish_requirement` inside `publish_pack`. Signing remains the existing function, invoked by the caller before publication.

- [x] **Step 4: Run the full PoC2 suite**

Run from `poc2/`: `.venv/bin/python -m unittest discover -s tests -v`

Expected: PASS, including `test_e2e_annex_vii` and `test_ui_smoke`. Those tests still use `extract_annex_vii_risk` and the demo pack directory. Result: PASS, 36 tests.

- [x] **Step 5: Commit**

```bash
git add poc2/requirements/workspace.py poc2/tests/test_requirements_publish.py
git commit -m "$(cat <<'EOF'
Publish a sealed working copy as a new immutable Pack directory.

An existing version or invalid signature leaves no release behind. An unsigned Requirement is handled according to Packs v2. Coverage publication waits for open contract 2.
EOF
)"
```

### Phase 1 acceptance

- Two `extract_section` calls with different timestamps produce two directories. The first directory's bytes match a snapshot taken before the second call. `published/` is absent until `publish_pack`.
- The CRA fixture's atomizer loci `1(a)` through `8` are listed in `coverage.json`. The two proposals in the Task 4 test become Requirement files. Other loci are `excluded`. No file named `decisions.json` is read or written.
- `apply_edits` of `remediation_hint` preserves `discovery_hints.sources[].args` when that key is omitted. An equal value keeps `signed`. A changed value removes it.
- `publish_pack` writes `published/cra-baseline/0.1.0/` containing only `pack.json` and the Requirement files, and refuses a repeat.
- `.venv/bin/python -m unittest discover -s tests` passes.
- NIS2 `section_text` raises, and no NIS2 working copy is created.

## Phase 2 — Catalog, selection, jobs, and the editor UI

Functional preservation of the PoC1 catalog, long-running job feedback, and editor. This phase calls Phase 1 functions. It does not move checks, claims, discovery, or review pages.

### Task 7: Working-copy selection API used by the UI

**Files:**

- Modify: `poc2/requirements/workspace.py`
- Test: `poc2/tests/test_requirements_extract.py`

**Interfaces:**

- Produces: `mark_selected(root: Path, pack_id: str, timestamp: str) -> Path` and `selected_copy(root: Path, pack_id: str) -> Path | None`

Selection is a small JSON file `root / "selection.json"` with `{ "pack_id", "timestamp" }`. It is operational state, like a job file. It is not copied into a Pack directory. `mark_selected` calls `select_working_copy` first and writes the file only when that call succeeds. `selected_copy` returns `None` when the file is missing or the directory has disappeared.

- [x] **Step 1: Test that marking `090000Z` then `143000Z` changes `selected_copy`, and that neither working-copy file changes bytes.**

- [x] **Step 2: Run the test and confirm failure.** Result: ERROR, `ImportError: cannot import name 'mark_selected'`.

- [x] **Step 3: Implement the two functions.**

- [x] **Step 4: Run `tests.test_requirements_extract`.** Result: PASS, 9 tests. Full suite PASS, 37 tests.

- [x] **Step 5: Commit** with message `Record which Requirements working copy the UI is editing.` Commit `0cb5534417380ccfe24ed03afaf0d7ec2bc1f4cc`.

### Task 8: Extract job record

**Files:**

- Create: `poc2/requirements/jobs.py`
- Test: `poc2/tests/test_requirements_jobs.py`

**Interfaces:**

- Consumes: `extract_section`
- Produces:
  - `start_extract_job(jobs_dir: Path, *, job_id: str, root: Path, adapter_dir: Path, section_id: str, proposals: list[dict], pack: dict) -> str`
  - `read_job(jobs_dir: Path, job_id: str) -> dict`
  - `request_abort(jobs_dir: Path, job_id: str) -> None`

The job file stores `status` (`running`, `done`, `failed`, `aborted`), `stage`, `progress` as a float that moves while work is happening, `log_tail` of at most 200 strings, and `error` when status is `failed` or `aborted`. `start_extract_job` runs `extract_section` on a daemon thread. The test does not open a socket and does not call a model. Pass the same two proposals as Task 4. Abort sets `aborted` and must not delete an older working copy created by an earlier job. A failed job writes `status: failed` and does not create `published/`.

Poll contract for the later page: the page reads this JSON twice per second. That loop lives in the page script in Task 9, not in `jobs.py`.

- [x] **Step 1: Test done, failed (stub adapter id), and abort. Assert a pre-existing copy's bytes.**

- [x] **Step 2: Run and confirm failure.** Result: ERROR, `ModuleNotFoundError: No module named 'requirements.jobs'`.

- [x] **Step 3: Implement the job file writer. Mirror the PoC1 rules that an abort already stored as `aborted` is not overwritten with `failed`, and that `log_tail` keeps the last 200 lines.**

- [x] **Step 4: Run `tests.test_requirements_jobs`.** Result: PASS, 4 tests. Full suite PASS, 41 tests.

- [x] **Step 5: Commit** with message `Record extract progress outside the Pack directory.` Commit `988849f6efadd03bd8b2a4adefe860c5294af406`.

### Task 9: Requirements pages

**Files:**

- Create: `poc2/requirements/ui/pages.py`
- Create: `poc2/requirements/ui/__init__.py`
- Create: `poc2/tests/fixtures/annex_vii_sample_proposals.json`
- Modify: `poc2/app/server.py` to add routes and call the functions below
- Test: `poc2/tests/test_requirements_ui.py`

**Interfaces:**

- Consumes: `list_working_copies`, `selected_copy`, `mark_selected`, `load_working_copy`, `extract_section` inputs via `start_extract_job`, `apply_edits`, `assign_reference_numbers`, `save_working_requirement`, `publish_requirement`, `seal_pack_directory`, `publish_pack`, `read_signature`, `read_pack_seal`
- Produces HTML callables:
  - `catalog_page(model: dict) -> bytes`
  - `editor_page(model: dict) -> bytes`
  - `job_fragment(job: dict) -> bytes` for the poll response

`app/server.py` parses forms, calls the operations, and passes the resulting view model to these functions. The page functions do not call `save_requirement`, `validate_requirement`, or `sign_object`.

Catalog shows the CRA adapter, the source URL, each timestamp, a latest marker on the last `list_working_copies` item, and the coverage `status`. Actions: select a copy, start extract for section `VII`. The extract action reads proposals from `poc2/tests/fixtures/annex_vii_sample_proposals.json`, a JSON array with the same two proposals as Task 4 (`CRA-ANNEX-VII-RISK` / `VII.3`, and `FIXTURE-VII-1A` / `VII.1(a)`). `FIXTURE-VII-1A` is a pipeline sample, not a CRA id convention. The button does not read `claims_by_locus.json` or `search_by_locus.json`. Extract opens the job panel. Phase 5 may pass producer output into `start_extract_job` instead of this file; until then the sample file is the UI input.

Editor, for one id in the selected copy, shows every `references[]` entry (`locator`, `law_text`, displayed `nr`), `source.framework`, `instrument`, `identifier`, `edition`, `language`, clickable `url`, `note`, `remediation_hint`, the five properties, and discovery-hint lists including each `sources[]` entry's `args` as JSON. Blank optional values remove the key. Omitted inputs are not posted as empty replacements: the server builds the edit dict from fields the form marks present. A signed Requirement renders inputs disabled until the page's Edit control enables them in the browser. Save posts `expected_digest`. The unsaved banner is client-side text: "Unsaved edits. The saved version is unchanged." Publish and seal forms are separate from the edit form and do not submit edit fields.

Job panel: status, stage, log tail, Abort. Escape and backdrop do not abort. Abort posts `request_abort`. On `done` or `aborted`, the page reloads. On `failed`, the log stays until Close.

Routes to add, leaving existing `/discover`, `/claims`, `/check`, `/review`, `/prepare` in place:

| Route | Calls |
| --- | --- |
| `GET /requirements` | `catalog_page` |
| `POST /requirements/select` | `mark_selected` |
| `POST /requirements/extract` | `start_extract_job` |
| `GET /requirements/jobs/<id>` | `read_job` as JSON |
| `POST /requirements/jobs/<id>/abort` | `request_abort` |
| `GET /requirements/requirement/<id>` | `editor_page` |
| `POST /requirements/requirement/<id>` | `apply_edits` then `save_working_requirement` |

The existing `/requirement` route stays so the prepared demo still edits `CRA-ANNEX-VII-RISK` in `packs/cra-baseline`. The cover link for the new catalog is added beside it. `workflow.snapshot` stays on the demo pack until a later change explicitly points checks at `published/`. Phase 2 does not make that switch.

- [x] **Step 1: Write a UI test that builds a copy with the two Requirements, GETs `/requirements`, selects it, GETs the point-3 editor, and asserts both would-be reference texts are present when the copy has two references. Post a `remediation_hint` change and assert `sources[0].args` in the saved file is unchanged. POST extract and assert the job reaches `done` and a new timestamp directory exists.**

Use `app.server.make_handler` the same way as `tests/test_ui_smoke.py`.

- [x] **Step 2: Run `tests.test_requirements_ui` and confirm failure.** Result: FAIL, `/requirements` returned "Unknown page."

- [x] **Step 3: Implement pages and routes.**

- [x] **Step 4: Run `unittest discover -s tests`.** Result: PASS, 42 tests. HTTP walk on a temporary workspace: prepare, save the demo requirement, discover, check, review, extract until `done`, edit `FIXTURE-VII-1A`. `packs/cra-baseline` bytes were unchanged. The browser showed the cover page and the catalog link. A browser click was blocked by the environment, so the click-path was repeated over HTTP.

- [x] **Step 5: Commit** with message `Add the Requirements catalog, extract job, and multi-field editor.` Commit `969852ef7e5db316e0456ec795ba4c094b0307ac`.

### Phase 2 acceptance

- The UI can select a timestamp, show both Requirements from Phase 1, edit a hint without dropping `sources[].args`, and publish only through the Phase 1 `publish_pack` function after the existing seal operations.
- A job file reaches `done` or `failed` without a `decisions.json` write. Abort does not change an older copy.
- `test_ui_smoke` and `test_e2e_annex_vii` still pass against the demo pack.
- Browser check covers the new catalog and the old prepare → review path. Record anything the browser could not exercise.

## Phase 3 — Compare

Compare is read-only until the user applies an explicit transfer. It does not create a dated directory.

### Task 10: Read-only compare

**Files:**

- Create: `poc2/requirements/compare.py`
- Test: `poc2/tests/test_requirements_compare.py`

**Interfaces:**

- Consumes: `load_working_copy`, `load_pack_directory`
- Produces: `compare_copies(left: Path, right: Path) -> dict`

Load both directories first and snapshot every file's bytes. Compute the diff. Return the snapshots' identities plus a transient dict. After return, byte-compare both directories to the snapshot and fail the test if any byte changed.

Match steps, in order:

1. Pair Requirements with the same `id`.
2. For unpaired Requirements, pair a left reference with a right reference when `source.identifier` is equal and `references[].locator` is equal. One left Requirement may pair with several right Requirements, and the reverse. Each such pair is `possible_consolidation` or `possible_split`, not an applied merge.
3. Remaining Requirements are `only_left` or `only_right`.
4. Paired same-id Requirements are `unchanged` or `changed`. Field diffs include every Requirement field and `discovery_hints.sources[].args`.

Ambiguous locator matches (one reference matching two candidates that the id step did not already pair) are listed as `ambiguous` and are not folded into a single pair.

- [x] **Step 1: Tests for identical copies, one changed hint, one added id, one removed id, and one Requirement whose two locators match two single-reference Requirements. Assert zero byte changes.**

- [x] **Step 2: Run and confirm failure.** Result: ERROR, `ModuleNotFoundError: No module named 'requirements.compare'`.

- [x] **Step 3: Implement `compare_copies` with no write calls.**

- [x] **Step 4: Run the compare tests.** Result: PASS, 5 tests. Full suite PASS, 47 tests.

- [x] **Step 5: Commit** with message `Compare two Pack snapshots without writing either one.` Commit `f1c5d992b3f61b169b8be3c9b6ad9490519714ff`.

### Task 11: Explicit transfer

**Files:**

- Modify: `poc2/requirements/compare.py`
- Modify: `poc2/requirements/ui/pages.py`
- Modify: `poc2/app/server.py`
- Test: `poc2/tests/test_requirements_compare.py`

**Interfaces:**

- Produces:
  - `preview_transfer(destination: Path, requirement_id: str, fields: dict) -> dict` returning `{ "requirement": dict, "errors": list[str] }` and writing nothing
  - `apply_transfer(source: Path, destination: Path, requirement_id: str, fields: dict, *, source_digest: str, destination_digest: str | None) -> None`

`destination` must be a dated working copy, not a directory under `published/`. `fields` is either `{ "requirement": <whole object> }` or a subset of editable fields. A whole-object copy drops `signed` always, sets `pack_id` from the destination `pack.json`, and refuses when that id already exists in the destination unless the field set is an in-place update of that same id. A field subset uses `apply_edits`, so an unchanged payload keeps `signed` and a changed payload drops it. `source_digest` and `destination_digest` use `version_digest`. A mismatch raises `ModelError` before any write. The source directory's bytes are compared in the test before and after.

Add `GET /requirements/compare` and `POST /requirements/compare/apply`. The page shows the transient diff and posts the selected fields. Opening the page does not call `apply_transfer`.

- [x] **Step 1: Test a one-field transfer, a stale destination digest, and a published directory used as destination.**

- [x] **Step 2: Run and confirm failure.** Result: ERROR, `ImportError: cannot import name 'apply_transfer'`.

- [x] **Step 3: Implement preview, apply, and the page.**

- [x] **Step 4: Run compare tests and `unittest discover -s tests`.** Result: compare and UI PASS, 9 tests. Full suite PASS, 50 tests.

- [x] **Step 5: Commit** with message `Apply a Compare transfer only to the selected working copy.` Commit `4c9a8dbb6326cee8e78c9e0ec2e53123f79a9636`.

### Phase 3 acceptance

- Comparing two copies and comparing a copy with `published/cra-baseline/0.1.0` changes no files.
- Transferring `remediation_hint` changes that field on the destination, preserves `discovery_hints.sources[].args`, and leaves the source copy byte-identical.
- A stale digest writes nothing.
- The Annex VII end-to-end test still passes.

## Phase 4 — Consolidator

No new persisted type. A confirmed merge is one Requirement file plus deletion of the redundant unsigned files in the selected copy.

### Task 12: Suggestions and preview

**Files:**

- Create: `poc2/requirements/consolidate.py`
- Test: `poc2/tests/test_requirements_consolidate.py`

**Interfaces:**

- Produces:
  - `suggest_consolidations(directory: Path) -> list[dict]`
  - `preview_consolidation(directory: Path, ids: list[str], retained_id: str, fields: dict, references: list[dict]) -> dict`

Suggestion rule, transient only: two Requirements are a candidate group when `source.identifier` matches and they share a `references[].locator`, or when their `law_text` strings are equal after whitespace collapse. Rank by the number of shared locators, then shared passages. Each suggestion includes the ids and a `reason` string. `suggest_consolidations` writes nothing.

`preview_consolidation` builds one Requirement with `assign_reference_numbers` on the supplied references, validates it, and lists conflicts: keys in `strength`, `responsible`, `applicability`, `exceptions`, `scope`, `note`, `remediation_hint`, `discovery_hints`, and `source` where the selected Requirements disagree and `fields` does not set the key. The preview writes nothing. It does not choose between conflicting values.

- [x] **Step 1: Test that two Requirements sharing locator `VII.3` are suggested, that the suggestion does not change files, and that a preview of disagreeing `note` values returns a conflict until `fields` supplies `note`.**

- [x] **Step 2: Run and confirm failure.** Result: ERROR, `ModuleNotFoundError: No module named 'requirements.consolidate'`.

- [x] **Step 3: Implement suggest and preview.**

- [x] **Step 4: Run the consolidate tests.** Result: PASS, 1 test. Full suite PASS, 51 tests.

- [x] **Step 5: Commit** with message `Suggest overlapping Requirements without writing the working copy.` Commit `949718e43a4d833383d10c7b5aea54bf57fd04c2`.

### Task 13: Confirmed merge

**Files:**

- Modify: `poc2/requirements/consolidate.py`
- Modify: `poc2/requirements/ui/pages.py` and `poc2/app/server.py`
- Test: `poc2/tests/test_requirements_consolidate.py`

**Interfaces:**

- Produces: `apply_consolidation(directory: Path, ids: list[str], retained_id: str, fields: dict, references: list[dict], *, digests: dict[str, str]) -> dict`

`digests` maps each id to the `version_digest` read by the user. Any mismatch writes nothing. Copy the affected Requirement files into `work_directory(directory) / "txn"` first. Write the retained Requirement with `save_working_requirement` semantics, then delete the other ids only when those objects have no `signed` key. If a listed id has `signed`, raise `ModelError` before any delete. If a delete or write fails, copy the `txn` files back and raise. The returned object is the retained Requirement. It is unsigned. Both source passages are in `references` with `nr` 1 and 2.

The page `GET /requirements/consolidate` and `POST /requirements/consolidate/apply` call these functions. Rejecting a suggestion is leaving the page; it does not post a save.

A split is not a separate operation. The editor can create the new Requirement and the user can delete an unsigned draft only through a later explicit delete. This phase does not add delete-by-split.

- [x] **Step 1: Test a merge of two unsigned Requirements, a conflict that writes nothing, a signed Requirement that is not deleted, and a digest mismatch that restores the original files.**

- [x] **Step 2: Run and confirm failure.** Result: ERROR, `ImportError: cannot import name 'apply_consolidation'`.

- [x] **Step 3: Implement apply and the page.**

- [x] **Step 4: Run consolidate tests and the full suite. Publish the merged copy and assert the redundant id is absent under `published/`.** Result: consolidate PASS, 3 tests. Full suite PASS, 53 tests. The merge test publishes `0.1.0` and asserts `FIXTURE-VII-1A.json` is absent.

- [x] **Step 5: Commit** with message `Merge confirmed Requirements into one unsigned draft in the selected copy.` Commit `2045bb1957f8b5031292e1e0eb6aa56245646f1c`.

### Phase 4 acceptance

- Suggestions and a rejected preview leave the copy byte-identical.
- A confirmed merge of two unsigned drafts yields one Requirement with both `law_text` values and removes the other unsigned file.
- A signed file in the group is still present after a refused apply.
- A new `extract_section` after the merge leaves that copy's bytes unchanged.
- Full `unittest discover -s tests` passes.

## Phase 5 — Model proposals

This is the functional improvement that lets two prompts produce two dated copies. Compare from Phase 3 is how those copies are inspected. No vector store and no experiment screen are added.

### Task 14: Stage 02 and 03 producers

**Files:**

- Create: `poc2/requirements/produce.py`
- Test: `poc2/tests/test_requirements_produce.py`

**Interfaces:**

- Consumes: `validate_interpret_proposal`, `validate_hints_proposal`
- Produces:
  - `interpret(provisions: list[dict], *, strategy: str, model: str, temperature: float, endpoint: str, guidance: Path, max_rounds: int | None = None, complete=None) -> tuple[list[dict], list[dict]]`
  - `discovery_hints(provisions: list[dict], *, same keyword arguments) -> tuple[list[dict], list[dict]]`
  - Defaults when the caller omits them: `strategy="single_call"`, `model="qwen3-coder:30b"`, `temperature=0.2`, `endpoint="http://127.0.0.1:11434"`, guidance path supplied by the caller.

`complete` is an injectable callable `(prompt_text: str, settings: dict) -> str` so tests do not open a network connection. The production callable that posts to `endpoint` is used only when `complete` is omitted. Tests pass `complete`.

Returned proposals must satisfy Task 2 validators: one result per input locus, no unknown locus, no `claim` or `search`. The second return value is the `llm` note list from §4.1.5. `extract_section` gains an optional `llm_notes` argument and writes `llm.json` in the work directory only when that list is non-empty. Notes are not copied onto the Requirement.

`strategy="single_call"` makes one `complete` call. `multi_prompt` and `propose_critique_revise` are implemented as further calls of `complete` that still reduce to one validated list. `max_rounds` is required for `propose_critique_revise` and absent otherwise. A test with a fake `complete` that returns an extra locus asserts rejection. A test that runs `extract_section` twice with different guidance paths asserts two timestamp directories and different `prompt_sha256` values in `llm.json`, and asserts the adapter file bytes did not change.

- [x] **Step 1: Tests for locus count, forbidden fields, and two runs writing two work directories.**

- [x] **Step 2: Run and confirm failure.**

Expected: FAIL with `requirements.produce` missing. Result: FAIL, `ModuleNotFoundError: No module named 'requirements.produce'`.

- [x] **Step 3: Implement the producers and the `llm.json` write.**

- [x] **Step 4: Run produce tests and the full suite.**

Result: `tests.test_requirements_produce` PASS, 6 tests. `unittest discover -s tests` PASS, 83 tests.

- [x] **Step 5: Commit** with message `Record model-call diagnostics outside the Pack working copy.`

The product catalog does not gain model or prompt fields in this phase. A test or a later CLI passes the arguments. That matches the specification: experiment settings are callable arguments, and a product experiment screen is not required.

### Phase 5 acceptance

- A fake model that invents a locus does not write a Requirement for it.
- Two guidance files produce two dated copies. `llm.json` sits in `*.work/`. The published directory of a later `publish_pack` does not contain `llm.json`.
- Existing Requirements in the earlier copy are byte-identical.

## Phase 6 — Residual placement

Do this only after Phases 1–5 are green. Task 0 already moved `atomize.py`, `pipeline.py`, and `data/`. Do not repeat that move, do not delete the locus maps, and do not edit any `ARCHITECTURE.md`.

### Task 15: Place later Extract modules with the moved code

**Files:**

- Move `poc2/requirements/assemble.py` and `produce.py` to `poc2/requirements/extract/` if they were created outside that directory, and update those imports together.
- Leave `poc2/requirements/editing.py` where later editor tests import it, or move it to `poc2/requirements/editor/editing.py` in this same task if every import is updated together.
- Do not delete `claims_by_locus.json` or `search_by_locus.json` here. Task 4 stops the new product path from using them as an approval replay. Deletion waits until no test reads them, as its own confirmed step.

Behavior checks: the Phase 1 extract test, M1, and the Annex VII end-to-end test pass with the import paths from Task 0. `publish_pack` output is still a Pack directory that `load_pack_directory` accepts. No function reads `decisions.json`.

- [x] **Step 1: Move only modules that were created outside `poc2/requirements/extract/`. Do not edit atomizer regular expressions.**

Moved `poc2/requirements/assemble.py` → `poc2/requirements/extract/assemble.py` and `poc2/requirements/produce.py` → `poc2/requirements/extract/produce.py`. Left `editing.py` in place. Did not delete locus maps.

- [x] **Step 2: Run `unittest discover -s tests`.**

Result: PASS, 83 tests.

- [x] **Step 3: Commit** with message `Place later Extract modules with the moved code.`

The current-path row in `docs/arch/ARCHITECTURE.md` and the historical `poc2/extract/ARCHITECTURE.md` stay unchanged. Those conflicts are listed under Task 0. Do not copy the old `decisions.json` contract into the Requirements specification. The 2026-10-21 cleanup later removed `poc2/extract/` and updated that current-path row. Task 15 itself did not.


## Phase 7 — Requirements 1.0 hardening and integration

This milestone is **Requirements subsystem v1.0 candidate**, not Curbpack/CTAM product v1.0. Use the checkpoint protocol and split the tasks as needed.

- [x] **Task 16: Complete real end-to-end extraction.** Replace sample-only proposal inputs in the normal UI with actual stages 02/03 and their validated output. Keep fixture-based tests and test doubles. Do not present a sample fixture run as a production LLM extraction.

**Task 16 substeps (acceptance unchanged):**

- [x] **16a:** Add adapter default guidance files `prompts/interpret.txt` and `prompts/discovery_hints.txt` (Packs v2 fields; `{provisions}` placeholder). No catalog model/prompt UI fields.
- [x] **16b:** Job/domain path runs stage 02 then 03 when `proposals` is omitted; merges validated proposals; passes `llm_notes` into `extract_section`. Optional `complete=` for tests. Explicit `proposals=` remains for fixture tests only.
- [x] **16c:** UI extract stops calling `_load_proposals` / sample JSON. Sample fixtures stay for tests that pass `proposals=` directly.
- [x] **16d:** Update job/UI tests with a `complete` double that covers every input locus (FIXTURE ids except known `CRA-ANNEX-VII-RISK` / `VII.3`). Run full suite and commit.

Result: PASS, 84 tests.
- [x] **Task 17: Demonstrate source coverage.** Verify every provision in the selected source is represented in the run accounting and inspectable in the UI; incomplete and intentionally excluded items must be visually distinct. Resolve the human-approved scope-exclusion gate before making publication claim. Do not silently skip invalid LLM output or use placeholder Requirements as production IDs.

Selected-copy catalog renders `coverage.json` loci with distinct written/excluded/failed classes. Open contract 2 already decided coverage is not a publication gate; the catalog keeps the diagnostic disclaimer. Invalid LLM output still fails producers (Task 14/16); FIXTURE ids remain test-only labels.
- [x] **Task 18: Source adapters.** Complete a tested CRA Annex VII adapter with stable locators and deterministic segmentation; explicitly verify current canonical source against fixture. Evaluate official Formex XML as a source-specific implementation option rather than an assumed dependency. NIS2 and Medtech remain honest stubs until separately scoped; do not advertise them as supported. **Parallel work:** official CRA/NIS2 Formex adapters are tracked in `impl/pilot/XML_SOURCE_ADAPTERS_PLAN.md` (does not mark this task done until that plan’s acceptance criteria pass and are reconciled here).

**Reconciliation (2026-10-13):** `XML_SOURCE_ADAPTERS_PLAN.md` is COMPLETE. CRA text fixture adapter remains; Formex is optional via `cra-xml`. NIS2 is no longer a stub: it is a **partial** Formex adapter (Art.1–46 ready; annexes I–III not ready with diagnostics). Medtech remains **stub**. Source dropdown shows `partial`/`stub` status so support is not overstated. Compare artifacts document `1(d)` as the only genuine wording difference.
- [x] **Task 19: Sign/publication semantics.** Test unsigned vs signed Requirements strictly as `packs2.md` allows; no-op edits, stale writes, invalid signatures, altered pack bytes, zero and partial coverage, duplicate version, and failure rollback. Check output directories are truly immutable to the product APIs. Verify a published version opens in downstream Claims/Checks without data conversion.

Existing publish tests cover seals, unsigned refusal, tamper, duplicate version, and coverage non-gating. Added: published path refuses `save_working_requirement` / `apply_consolidation`; release loads via `load_pack_directory` and binds a Claim without conversion.
- [ ] **Task 20: Human usability walkthrough.** Browser-run CRA: pick source → extract real multiple provisions → inspect coverage → edit (including `sources[].args` and multiple references) → Compare old/new → Consolidate with conflicting fields → sign/seal → publish → reopen published Pack. Verify job abort/recovery and no accidental edits to other copies. Record observations and fixed defects.

**Task 20 findings (2026-10-13, walkthrough start — not complete):**

1. Cover link **1. Extract / requirement** (`/requirement`) assumed `packs/cra-baseline/CRA-ANNEX-VII-RISK.json` from Prepare sample workspace. Empty workspace → `FileNotFoundError`. Correct extract entry is **Requirements catalog** (`/requirements`) with adapters (e.g. `cra-xml`). Fixed: `_require_demo_requirement` → clear `ModelError`; cover lists catalog first and labels link 1 as sample pack.
2. Handler swallowed access logs and returned raw OS errors with no traceback on stderr. Fixed: `_fail` logs `poc2.app` ERROR + traceback; browser gets ModelError text or a short generic message.

**Task 20 UX correction (2026-10-13, human walkthrough still open):**

PoC1 is the interaction reference (`poc/components/requirement_manager/ui.py`, `cli_job.py`, `edit_desk.py`). PoC2 keeps Packs v2, dated copies, Ed25519, and the job runner. Do not copy PoC1 YAML, `demo:` seals, or `sources.json`.

| PoC1 interaction | Existing PoC2 capability | UX gap |
| --- | --- | --- |
| Compact source table: identity, URL, adapter, status, Extract, Edit | `cra-xml` and `nis` Formex adapters, `list_working_copies`, `mark_selected` | Catalog opens on XML inventory, provision dumps, and one adapter at a time |
| Edit stays disabled until a package exists | Editor loads the selected copy | No empty-state; Edit is not a per-source action |
| Extract asks for the batch, then a modal: stage, log tail (200), Abort, Close; running state ignores dismissal | `start_extract_job`, states `running`/`done`/`failed`/`aborted` | Silent section default (`VII` / `Art.21`); modal shows numeric `progress`; done reloads `?job=` and reopens; success does not select the new copy |
| Requirement list, then a detail form, save flash, sign dialog | Editor already round-trips Packs v2 fields, including `references[]` and `sources[].args`; `publish_requirement` is Ed25519 | No list page; sign form is inline; save/sign flash is unused |
| — (PoC1 has no Packs v2 release) | `publish_pack` refuses unsigned, bad seals, and duplicate versions; coverage is not a gate | Publish/seal sit on the requirement form; blockers are not shown until a failed POST |

`requirements/ARCHITECTURE.md` §4.1.2 still calls NIS2 a stub. The checked-in `nis` adapter is partial Formex (Task 18). This correction shows that adapter. It does not edit `ARCHITECTURE.md`.

Known documentation conflict, not a model change: architecture §4.1.2 vs `adapters/nis/adapter.json`. UI follows the adapter file and the publication functions already in `requirements/workspace.py`.

**Correction result (2026-10-13, not a human acceptance):**

Implemented on the existing routes and functions. Catalog lists `cra-xml` and `nis` only. New extraction requires a ready section. The job modal shows stage activity and the last log lines, not a percentage. A successful job selects the new dated copy. Edit opens that copy's Requirement list. Publish lists the real seal/signature blockers and does not treat incomplete coverage as one.

Tests: `cd poc2 && .venv/bin/python -m unittest discover -s tests` — PASS, 87 tests.

Browser, temporary workspace: home → catalog (CRA copy selectable, NIS2 empty state disables Edit/Publish) → New extraction shows VII ready and the other annexes unavailable → Edit list → requirement form with `sources[].args` → Sign dialog (cancel writes nothing) → Publish disabled with edition, unsigned, and seal blockers, coverage called out as not a blocker → Source details holds the inventory.

Live model: POST `nis` / `Art.1` with the configured `qwen3-coder:30b` endpoint. Job reached stage 02/03, then failed: `requirement probe.discovery_hints: field expected_evidence: expected non-empty list of strings`. Modal showed that text and Close. No `nis2-baseline` copy, and the existing CRA copy was unchanged. This is the existing proposal check, not a new rule. A successful live multi-provision extract was not observed in this session.

**Task 20 quality check (2026-10-13, walkthrough still open — PoC1 usefulness not recovered):**

Reference files, read-only:

- `poc/components/transform/adapters/cra/prompts/02_claims.txt` and `03_search.txt`
- `poc/components/transform/steps/02_claims.py` and `03_search.py`
- `poc/components/transform/adapters/cra/maps/claims.yml` and `search.yml` (both marked human-reviewed)
- `poc/data/in/ctam_cra_requirements_search.yml` (gold package assembled from those maps)

The 13-requirement baseline is `poc2/data/workspace/cra-xml-baseline/2026-10-13T134627Z` with diagnostics in `2026-10-13T134627Z.work/llm.json`. It used `single_call`, `qwen3-coder:30b`, temperature 0.2, `http://127.0.0.1:11434`. Prompt hashes were interpret `c1621a64d475415d71e081f2c88bc9cb926d08af5d9778def6dfe6364c08d043` and discovery `22ced447da7648bd3b4411e8658b430e5f877c15e2f4e4daf99c45b6fa6c0f6a`.

Diagnosis: segmentation already keeps the parent preamble and the same 13 loci. Settings match PoC1. Validators did not drop hint fields. The discovery prompt's example omitted `expected_evidence` and called paths optional, and the model copied that thin shape: no `expected_evidence` on any Requirement, and no `path_hints` on VII.1(a)–(d), VII.4, or VII.7. The interpret prompt allowed `strength` "when the law_text supports it", which produced `MAY` on VII.8 although that passage has no "may". PoC1 `claim` slugs and string `search.sources` are intentional Packs v2 differences, not missing data.

Change: only `adapters/cra-xml/prompts/interpret.txt` and `discovery_hints.txt`. The discovery prompt asks for several concepts, filename globs, Packs v2 `sources` objects, and 1–3 evidence kinds from the PoC1 list. The interpret prompt limits `strength` to shall/should/may and puts a where-clause in `applicability`. No validator, schema, or strategy change.

Recorded producer defects, not redesigned. `tests/test_requirements_produce.py` shows them: `multi_prompt` keeps only the last guidance file's proposals; `propose_critique_revise` asks for a critique and then revises the original proposal without that critique text.

Live `qwen3-coder:30b` calls, same strategy and settings. Baseline bytes were unchanged after every attempt.

1. Interpret returned a bare JSON array, `MUST` on every locus, and `scope` as arrays. `ModelError: produce: field response: expected a JSON object`. No copy.
2. A leading example was copied back as two rows, including an unsupported `responsible`. `expected 13 results, not 2`. No copy.
3. Intermediate copy `2026-10-13T141407Z` (13 Requirements, no exclusions) restated law text into `scope` on most rows. Left in place. Not the final prompt.
4. Final copy `2026-10-13T141531Z`. Interpret hash `f9111c4c3949121230bf32b1e1c40bfd2f7fd8d9f7b4d92046fdd7924ceeac14`. Discovery hash `54ef07faf955f59a45211e59bd4a325911fc7149dd4687259cd928116dd2bb23`. 13 Requirements, no exclusions. The same discovery prompt as attempt 3 produced different hint wording. Temperature 0.2 has no seed.

Final copy versus baseline and the gold maps, for the hard points: hints now include globs and evidence kinds, and VII.3 names a threat model with source `requirements`. That is more useful than the baseline. It is not the gold. VII.2(b) still misses the bill of materials. VII.5 still misses alternative solutions, and it omits `MUST` even though the passage says "shall". VII.1(c) still has no `applicability` for the hardware condition. VII.8 sets `responsible` to "Manufacturer", which that passage does not name, and its concepts include update tracking. Equivalence is not established.

**Quality experiment reference (2026-10-14, Task 20 still open):**

`poc2/data/reference/poc1-annex-vii-unsigned/` holds 13 unsigned Requirements converted from the PoC1 maps plus cra-xml Formex passages. Mapping and the losses (PoC1 ids, claim slugs, hunt globs, gold URL, and the `1(d)` "the information" vs "user information" wording) are in `poc2/data/reference/POC1_ANNEX_VII_MAPPING.md`. SHA-256 of the inputs and the frozen JSON is in `poc2/data/reference/POC1_ANNEX_VII_PROVENANCE.md`. The Requirement JSON from `d8c743a` was not rewritten. Optional legal fields that are pointable in `law_text` but absent from the PoC1 maps were not invented on the reference. Label: a Cursor agent produced the PoC1 maps and this conversion; the user inspected it; it is not an independently legally certified or fully human-reviewed gold standard. Independent reload on 2026-10-14: `load_pack_directory` plus `validate_pack(..., sealed=False)` and `validate_requirement(..., published=False)` on all 13 files, exit 0.

**Quality experiment result (2026-10-14, stopped, Task 20 still open):**

Three prompt revisions, then two unchanged repeats of the best one. Record: `poc2/data/reference/ANNEX_VII_EXPERIMENT.md`. Adapter prompts are r2 (`interpret` `a31224405a7fa7f7af92e1421e984564aa980e98d8a5a37fad3b8c32434c4f82`, `discovery_hints` `cf06c24da7c33c755dc935c45163dec842e8989a8a3fad2c45771164579547ab`). Best copy `2026-10-14T043521Z`; repeats `2026-10-14T043741Z` and `2026-10-14T043810Z`. r1 wrote no copy (`locus` `3)`). r3 stamped `MUST`, `manufacturer`, and `Where applicable` on every row and was not kept as the live prompt. Conclusion: **improved, not recovered.** `VII.2(b)` artefacts, `VII.5` alternative solutions, and `VII.3` requirements applicability are stable. `VII.1(c)` hardware applicability and `VII.5` `MUST` never appear. `VII.8` hint contamination varies across the repeats.
- [ ] **Task 21: Documentation and packaging.** Replace obsolete Extract architecture with a pointer (or remove it after updating links), document standard CLI/launch, external model configuration, clean setup, example inputs, known limitations, error messages, and supported scope. No dead alternate decision replay or duplicate normative files.
- [ ] **Task 22: Regression and release candidate.** Run full suite plus focused security/integrity, coverage, failure and UI tests; fix blockers, rerun; produce a concise release-candidate report with PASS/FAIL and reproducible commands, supported features, exclusions, and known limitations. Do not self-certify legal correctness.

**Requirements 1.0 acceptance:** at least one real, multi-provision CRA extraction from a controlled source, traceability/coverage, edit/compare/consolidate, correct Packs v2 signing and immutable publication, UI and direct-call use, meaningful tests, and backward-compatible downstream Pack loading. No unresolved release blockers and no fabricated claims about NIS2/Medtech support.

## Phase 8 — Product 1.0 integration and release gate (cross-subsystem)

A *Curbpack/CTAM 1.0* label requires the other subsystems, not just this Requirements plan. This section is a **release integration checklist and handoff**, not permission for Cursor to invent or implement Claims, Checks, Compile or Review without their own agreed architecture and implementation plans.

- [ ] Requirements 1.0 accepted against its scope and tests.
- [ ] Claims/Discovery implementation complete and independently accepted against their own specifications.
- [ ] Checks, Compile, Review and shared signing/persistence independently accepted; real fail/pass/skipped semantics and traceable outputs verified.
- [ ] Integration: published Pack → product `curbpack.json` → Discovery → approved Claims → Checks → Compile → human Review, with both successful and failed runs.
- [ ] End-to-end demo with a real sample repository, at least two Requirements and multiple Claims, a failing evidence case, recheck, and signed final review.
- [ ] Installation/distribution, documented upgrade/recovery, security/data handling, error reporting, cross-platform or supported-platform smoke tests, and versioned release notes are complete for the declared support scope.
- [ ] Full automated regression, manual user acceptance and a release-candidate review have no unresolved blockers.
- [ ] Human authorizes release version and packaging; only then may an agent tag/push/create a PR/publish/distribute according to explicit instructions.

**Final deliverable:** a release-readiness report containing each gate's evidence and an explicit GO/NO-GO recommendation. **Do not claim or perform product 1.0 release without a separate human go-ahead.**

## Handoff template (use in every completed task response)

```text
DONE: Phase N / Task M / step K — <observable behavior>
CHANGED: <paths>
TESTS: <exact commands> — PASS / FAIL / NOT RUN (reason)
GIT: <local commit sha> or <uncommitted changes>
BLOCKERS: <none or exact decision>
NEXT: Phase N / Task M / step K — <one concrete next action>
CHECKPOINT: impl/pilot/REQUIREMENTS_IMPLEMENTATION_PLAN.md updated [yes/no + reason]
```

## Spec coverage

| Requirements specification | Task |
| --- | --- |
| §2 Working-copy operations and collision behavior | Tasks 3, 4, 6 |
| §4 Stages 00, 01, 04 and stub refusal | Tasks 1, 2, 4 |
| §4.2–4.3 Proposal validation, model notes, new copy per run | Tasks 2, 4, 14 |
| §5 Editor, no-op signature, stale save, reference numbers | Task 5, Task 9 |
| §6 Compare | Tasks 10, 11 |
| §7 Consolidator | Tasks 12, 13 |
| §8 Publication | Task 6 |
| §9 Catalog, job modal, editor UI | Tasks 8, 9 |
| §10 PoC1 catalog, jobs, editor; removal of replay | Tasks 4, 8, 9, 15 |
| §11 Acceptance items 1–8 and 11–13 | Phases 1–2 |
| §11 Acceptance items 9–10 and 14 | Phases 2–4 |
| §11 Acceptance item 15, downstream packs | Regression suite every phase |
| Full-dump CRA splitter | Not in this plan. `stage00(..., dump_text=)` raises until a later plan ports `poc/components/transform/split_annexes.py` behavior without importing it. |
| Further CRA ids, articles, NIS2, Medtech extraction | Blocked on open contract 1 and on adapter fixtures. Stubs refuse. |
| Signed Git commit fallback | Blocked on open contract 3. |

## Out of scope

This plan does not itself authorize implementing other subsystems or shipping a product release. Phase 8 tracks acceptance gates only; each subsystem has its own implementation plan.


Discovery, Claims, checks, compile, final review, scaffold, OIDC, FastAPI, a plugin framework, a vector store, and an adapter-editing screen. The demo pack path consumed by those subsystems stays until a separate change points `workflow.snapshot` at a selected published Pack.
