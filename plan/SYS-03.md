# SYS-03 — One repository is the pilot door

## Summary

- **Story:** `docs/agile/epics/01-pack-editor/stories/SYS-03-one-repo-door.md`
- **Goal:** Rebind product and Studio I/O to `curbpack.json` and `curbpack-studio.json` ([workspace.md](../docs/reference/workspace.md)). Approved app behaviour stays.
- **Scope / exclusions:** SYS-R01–SYS-R09 as path/config wiring only. Do **not** redesign or remove approved Discover (choose existing Claim, diff, candidates), Check, Review, Extract, or Pack Editor flows. Add Save/Cancel dialogs/pages for the two config files. Path contract and created-file keys: workspace.md §§2 and §4. Open-repo id is workspace state; directory fields live in the product `curbpack.json`. No keys outside workspace §2.2 / §4.2. `unsigned_requirements` behaviour is later. **curbcheck CLI / `--defaults` / id-list `--packs`:** [CHK-07](../docs/agile/epics/01-pack-editor/stories/CHK-07-curbcheck-workspace.md), not this plan. SYS-03 create dialog uses that defaults API when present; until then write workspace §2.2 created-file values directly. Absent `curbpack-studio.json` keeps today’s pilot bind/model/temp until Save creates it.
- **Baseline:** Dirty worktree on `main`, pre-existing uncommitted edits to `app/server.py`, `requirements/ui/pages.py`, `requirements/ui/try_discovery.py`, `requirements/extract/assemble.py`, and other files already in progress toward a "Pack Sources" renaming, unrelated to this plan revision — preserved, not reset. `python3 -m unittest tests.test_curbcheck_package tests.test_m4_checks tests.test_e2e_annex_vii tests.test_requirements_export tests.test_review_report_kept` on that dirty tree: Ran 48 tests, 1 failure + 5 errors (`test_pack_sources_row_submits_export_for_that_document`, and `ModuleNotFoundError`/`git init` style errors from the in-progress rename and a sandboxed `git init -b main`). These are pre-existing, not introduced by this plan revision, and are not claimed as passing. `checks/run.py` `curbpack_directory`, `claim_catalog`, and `run_repository`, and `common/validate.py` `validate_curbpack_config`, still implement the withdrawn single `curbpack` key (`_reject_unknown` accepts only `packs`, `exclude_requirements`, `requirements`, `search_hints`, `curbpack`). No code anywhere resolves `packs_dir`, `claims_dir`, `results_dir`, or `reports_dir`; no `discovery/door.py` or `tests/test_sys03_door.py` exists yet. This plan's Tasks 1–7 are all still to do.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | APPROVED |
| Approved by | danielfl, 2026-10-29 (SYS-R01–R09 walkthrough OK; proceed Task 1–8; CHK-07/08 out of this plan) |
| Current task | Task 7 — IMPL-START |
| Last completed task | Task 6 |
| Last verified tests | 2026-10-29: `python3 -m unittest tests.test_sys03_door tests.test_ui_smoke tests.test_review_report_kept tests.test_review_replace_flow tests.test_review_discover_again tests.test_review_compile tests.test_review_coverage_ui` — Ran 31 tests, OK. |
| Last checkpoint commit | This commit. Resolve with `git log -1 --format=%H -- plan/SYS-03.md`. |
| Requirements | Story SYS-R01–SYS-R09 in `SYS-03-one-repo-door.md` (R01 rewritten 2026-10-29 walkthrough; R09 Studio config page). No new `docs/req/` row. |
| Packs v2 | `docs/reference/workspace.md` and `docs/reference/packs2.md` are both law. This plan edits neither. Workspace §2 owns `curbpack.json` keys, which of them are required, and the on-disk paths. Packs v2 §2.3 owns selection and the `search_hints` merge; §3.1 owns the run-result object. Allowed keys: `packs`, `requirements` XOR `exclude_requirements`, `search_hints`, `packs_dir`, `claims_dir`, `results_dir`, `reports_dir`, `unsigned_requirements`. `search_hints` and `unsigned_requirements` are required. The single key `curbpack`, and a `temp`/`tmp` key, are rejected. |
| Blockers | None |
| **Exact next action** | Task 7: Studio config page for curbpack-studio.json. |

## Requirements and acceptance mapping

Requirements live in the story (`docs/agile/epics/01-pack-editor/stories/SYS-03-one-repo-door.md`): one short description, then Given/When/Then. This table only maps each id to its acceptance test.

| Requirement ID | Story | Test / observed evidence | Status |
| --- | --- | --- | --- |
| SYS-R01 | SYS-03 | `tests/test_sys03_door.py` | Task 3 |
| SYS-R02 | SYS-03 | `tests/test_sys03_door.py` | Task 3 |
| SYS-R03 | SYS-03 | `tests/test_sys03_door.py` | Task 3 |
| SYS-R04 | SYS-03 | `tests/test_sys03_door.py` | Task 5 |
| SYS-R05 | SYS-03 | `tests/test_sys03_door.py` | Task 4 |
| SYS-R06 | SYS-03 | `tests/test_sys03_door.py` | Task 6 |
| SYS-R07 | SYS-03 | `tests/test_sys03_door.py` | Task 6 (Studio config page still Task 7) |
| SYS-R08 | SYS-03 | `tests/test_sys03_door.py` | DRAFT |
| SYS-R09 | SYS-03 | `tests/test_sys03_door.py` | DRAFT |

## Tasks

### Task 0 — approve this plan

**Inputs / contracts:** SYS-03 story (2026-10-29 revision); `docs/reference/workspace.md`; `docs/reference/packs2.md` §2.3 (unchanged); `common/validate.py` `validate_curbpack_config`; `checks/run.py` `curbpack_directory`, `claim_catalog`, `run_repository`; `discovery/repos.py` `product_repos.json`; `app/server.py` Pack Editor/Pack Sources, Check, Discover, and `preview_report`.
**Change files:** `plan/SYS-03.md` only.
**Acceptance / stop:** human approval recorded. No product code in this task.

- [x] Independent plan review completed. First pass Issues Found (`4efa6824`); fixes applied; re-review Approved (`241fee1a`).
- [x] Plan re-approved after walkthrough (danielfl, 2026-10-29).

### Task 1 — `curbpack.json` resolves `packs_dir`, `claims_dir`, `results_dir`, `reports_dir`

**Requirements:** Foundation for SYS-R01–SYS-R06, SYS-R08. Replaces the single `curbpack` key with the four directory fields `docs/reference/workspace.md` §2.2 names.
**Files:** `common/validate.py` `validate_curbpack_config` (accept only the keys in `docs/reference/workspace.md` §2.2; require every key that table marks required, including `search_hints` and `unsigned_requirements`; reject `curbpack` and any other unknown key; keep selection as exactly one of `exclude_requirements`, `requirements`, or neither, per workspace §2.1 and packs2 §2.3). Do not implement `unsigned_requirements` behaviour (workspace §2.4). Leave `search_hints` shape validation exactly as packs2 §2.3 already defines — requiring the four path fields does not invent new `search_hints` keys. `checks/run.py` (replace `curbpack_directory`/`claim_catalog` with field-name resolvers, e.g. `packs_dir(repo, config)`, `claims_dir(repo, config)`, `results_dir(repo, config)`, `reports_dir(repo, config)`; update `run_repository` to load Packs from `packs_dir` and Claims from `claims_dir`), `app/server.py` `_write_curbpack` (stop preserving `curbpack`; preserve/write `packs_dir`/`claims_dir`/`results_dir`/`reports_dir` so Task 3 Add and Task 4 Check-save do not reintroduce the withdrawn key), `tests/test_sys03_door.py` (new).
**Test first:** A `curbpack.json` with `packs_dir`, `claims_dir`, `results_dir`, and `reports_dir` set to four distinct relative directories resolves each to `<repo>/<value>`. The file also carries the other required keys from workspace §2.2 (`packs`, `search_hints`, `unsigned_requirements`) with the created-file values in §2.3. A file with the old `curbpack` key, or missing any required key from §2.2, is rejected before any run or report file is written — record the exact `ModelError` text, do not silently default. A file that sets both `requirements` and `exclude_requirements` is rejected. `run_repository` loads `<packs_dir>/<pack-id>/<pack-version>/pack.json` and Claims from `<claims_dir>/<claim-id>.json`, and no longer resolves `<curbpack>/packs` or `<curbpack>/claims`. A Claim whose Requirement is not selected is reported, not raised, and does not stop the run of the selected Claims (existing `selected_requirement_ids` behavior, unchanged).
**Validation:** `python3 -m unittest tests.test_sys03_door tests.test_curbcheck_package tests.test_m4_checks`
**Note:** Other suites still build `curbpack.json` fixtures without the four path fields; they may fail after this task until Tasks 3–6 retarget them. That mid-sequence breakage is expected — do not treat it as a new Task 1 defect when running a broader `make test`.
**Stop if:** a test or a resolver would need a key, a path, or a selection rule that is not in workspace §2 or packs2 §2.3. Record the step. Do not invent the value.

- [x] RED observed for the intended behavior.
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

### Task 2 — Remember which repository is open

**Requirements:** SYS-R07 storage rule. `packs_dir`/`claims_dir`/`results_dir`/`reports_dir` stay in the product repository's file; only the chosen repository id is Studio workspace state.
**Files:** `discovery/door.py` (new), `tests/test_sys03_door.py`.
**Test first:** `<workspace>/open-repo.json` is `{"id": "<repo id>"}` and nothing else. The id must already be in `product_repos.json`. A missing file, an empty id, or an unknown id means no repository is open. Choosing repo A then repo B stores only B. The file is not written into either product repository. Neither repository's `curbpack.json` is modified by choosing a repository. `selection.json` is not written. Resolving an open repo returns that repo path plus `packs_dir(repo, config)`, `claims_dir(repo, config)`, `results_dir(repo, config)`, `reports_dir(repo, config)` from Task 1. Saving a relative `packs_dir` (or the other three) value writes that key in that repo's `curbpack.json` and leaves the other repo's file byte-for-byte unchanged. An absolute value or a `..` segment is rejected and the file is unchanged.
**Validation:** `python3 -m unittest tests.test_sys03_door`
**Stop if:** the directory fields would be stored in the workspace, or the open repo would be stored by adding a path key to `curbpack.json`.

- [x] RED observed for the intended behavior.
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

### Task 3 — Door UI: empty views + `curbpack.json` dialog

**Requirements:** SYS-R01, SYS-R02, SYS-R03, SYS-R07 for product views / `/requirements`.
**Files:** `app/server.py` GET/POST door routes and `curbpack.json` dialog save/cancel; retire silent `_start_empty_folder` write-without-dialog (or rewrite it to open the dialog flow); `_write_curbpack` call sites; `requirements/ui/pages.py` (and shared door chrome on Discover/Check/Review); `tests/test_sys03_door.py`. Do not edit the Export Pack form or `export_pack`.
**Test first:** With no open repo, GET Pack Sources / Pack Editor / Discover / Check / Review show no product content and offer repo choice. Chosen repo without `curbpack.json` offers create; opening the dialog shows workspace §2.2 fields (paths included) with Save/Cancel; Cancel leaves no file; Save writes a complete §2.2/§2.3 file. Edit dialog Save updates the file; Cancel leaves bytes unchanged. Dialog presentation matches the Requirements dialog style (same interaction pattern). Open repo with `present`/`missing` packs: row only when `<packs_dir>/<id>/<version>/pack.json` exists. Empty `claims_dir` says no Claims. POST Add writes `<packs_dir>/<id>/<version>/pack.json` and appends id; version string `"0.1.0"` only from `draft_pack` (not its CRA id/source). Second repo’s `curbpack.json` unchanged when A’s paths are saved.
**Validation:** `python3 -m unittest tests.test_sys03_door tests.test_cover_navigation tests.test_requirements_ui tests.test_requirements_export tests.test_requirements_catalog`
**Add test:** `tests/test_requirements_catalog.py` `test_add_via_http` posts `/requirements/documents`. Update it in this task so Add is `<packs_dir>/<id>/<version>/pack.json` plus the appended id in `packs`, and `save_catalog` is not called.
**Existing tests:** `tests/test_cover_navigation.py`, `tests/test_requirements_ui.py`, and the Pack Editor list assertions in `tests/test_requirements_export.py` open a registered repo and set `open-repo.json` before GET `/requirements`. The Pack they assert is `<packs_dir>/<id>/<version>/pack.json` listed in that repo's `curbpack.json` `packs`, not a row that exists only in `registered_sources.json`. Cover-page links and `/requirements/requirement/<id>` assertions that are not the Pack list stay. Extract landing beside `pack.json` is Task 7, not this task.
**Stop if:** the row can be shown only by reading `registered_sources.json`, or Add needs a new field on `pack.json` or `curbpack.json` for the adapter. Record that stop. Do not add the field.

- [x] RED observed for the intended behavior.
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

### Task 4 — Check runs that repository

**Requirements:** SYS-R05, SYS-R07 for `/check`.
**Files:** `checks/run.py` `run_repository` only, for the unselected-Claim rule (behavior from Task 1, exercised here through the page). `app/server.py` `/check`. `app/pages.py` `_curbpack_editor`. `tests/test_sys03_door.py`. `tests/test_check_editor.py`.
**Test first:** With no open repo, GET `/check` says none is chosen and does not read `<workspace>/product/curbpack.json`. POST `repo_id` on `/check` writes `open-repo.json`, and GET `/requirements` then names that repo. The page shows the absolute `curbpack.json` path, `packs_dir`/`claims_dir`/`results_dir`/`reports_dir`, the ids from `packs`, and present or missing against `packs_dir`. It shows `exclude_requirements` or `requirements` as the file has them, never both. Pack Editor and Check each have fields that save the same four path values into that repo's file; that field set is not an editor for the id lists. The page does not contain "Read it", "Start empty", or "Read it and tick the packs it names?", and it does not add an id that exists only as a workspace Pack. POST check calls `run_repository`. One Claim matches a selected Requirement and one does not. The result file is `<results_dir>/run-result_<YYYYMMDDTHHMMSSZ>.json`, the page shows that path, the selected Claim is in the result, and the other is not. A second POST writes a second file and leaves the first byte-for-byte in place. The run does not raise. The same holds when `requirements` lists only the selected id, and when `exclude_requirements` names the other Requirement: that Claim is absent and the selected Claim is present.
**Validation:** `python3 -m unittest tests.test_sys03_door tests.test_check_editor tests.test_m4_checks`
**Stop if:** honoring `exclude_requirements`/`requirements` or skipping an unselected Claim needs a new `curbpack.json` field.

- [x] RED observed for the intended behavior.
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

### Task 5 — Discover I/O → `packs_dir` / `claims_dir`

**Requirements:** SYS-R04, SYS-R07 for `/discover`.
**Files:** path resolution call sites in Discover / `claims/ui/http.py`; fixture paths in Discover tests. **Do not remove** choose-existing-Claim, diff, candidate-vs-Claim, or create-or-update UI. `claims/ui/coverage.py` `load_run` still reads `<repo>/.curbpack/run-result.json`; retarget that to `results_dir` dated files in Task 6.
**Test first:** Discover reads Requirements from `packs_dir` and Claims from `claims_dir` on the open repo’s `curbpack.json`. Save writes `<claims_dir>/<claim-id>.json`. Existing Discover tests still pass after fixtures move to those dirs (behaviour preserved).
**Validation:** `python3 -m unittest tests.test_sys03_door tests.test_discover_claims_ui tests.test_discover_layout`
**Stop if:** the change would delete or disable approved Discover flows to make paths “simple”.

- [x] RED observed for the intended behavior.
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

### Task 6 — Review compiles that run

**Requirements:** SYS-R06, SYS-R07 for `/review`.
**Files:** `app/server.py` `preview_report`, report write, and `_review_view`, `claims/ui/coverage.py` `load_run` (Discover-from-review greying still reads `<repo>/.curbpack/run-result.json` after Task 5), `tests/test_sys03_door.py`, `tests/test_ui_smoke.py`, `tests/test_review_report_kept.py`, `tests/test_review_replace_flow.py`, `tests/test_review_discover_again.py`.
**Test first:** POST `repo_id` on `/review` writes `open-repo.json`. GET `/review` names that repository and `packs_dir`. The repository has `<results_dir>/run-result_<UTC>.json`, `<packs_dir>/<pack-id>/<pack-version>/pack.json`, and a Claim in `claims_dir`. `<workspace>/product/` has a different run and a different Claim. Compile reads that dated run-result file and `claims_dir`. The report file is `<reports_dir>/review-report_<UTC>.json`. A second compile writes a second report file and leaves the first in place. It does not contain the workspace Claim and it is not written under `product/docs/reports/` or `product/.curbpack/`. With no open repo, GET `/review` says none is chosen and does not compile `product/`. `tests/test_ui_smoke.py`, `tests/test_review_report_kept.py`, `tests/test_review_replace_flow.py`, and `tests/test_review_discover_again.py` are updated in this task: register the product in `product_repos.json`, set `open-repo.json` to that id, put the Pack at `<packs_dir>/cra-baseline/<version>/`, put Claims in `claims_dir`, expect the run at `<results_dir>/run-result_<UTC>.json`, and expect the report at `<reports_dir>/review-report_<UTC>.json`. A later run or compile does not replace the earlier file. `prepare_demo` today writes `product/.curbpack/run-result.json` and `workspace/packs/cra-baseline`; setting `open-repo.json` alone does not make those tests pass, so the fixtures move. Keep the assertions that a failed Claim stays visible and that Discover-again opens one Requirement. `tests/test_review_compile.py` calls `compile_report` directly and is not this task's evidence.
**Validation:** `python3 -m unittest tests.test_sys03_door tests.test_ui_smoke tests.test_review_report_kept tests.test_review_replace_flow tests.test_review_discover_again tests.test_review_compile tests.test_review_coverage_ui`
**Stop if:** pointing the report at `reports_dir`, or the run at `results_dir`, requires a new `curbpack.json` field beyond those two.

- [x] RED observed for the intended behavior.
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

### Task 7 — Studio config page (`curbpack-studio.json`)

**Requirements:** SYS-R09, SYS-R07 for the Studio config view.
**Files:** new page route under `app/server.py` + UI module; load/save `curbpack-studio.json` per workspace §4; `$ENV` substitution from `.env` on load; `tests/test_sys03_door.py`.
**Test first:** No open repo → empty product content + repo offer (same door rule). Open repo, file absent → offer create → editor with §4.2 fields, Save/Cancel; Cancel writes nothing; Save writes the file. File present → editor shows values; Save updates; Cancel leaves bytes unchanged. Absent file leaves today’s pilot bind/model wiring alone until Save creates the file.
**Validation:** `python3 -m unittest tests.test_sys03_door`
**Stop if:** the page would invent keys outside workspace §4.2.

- [ ] RED observed for the intended behavior.
- [ ] Minimal implementation and GREEN verified.
- [ ] Relevant regressions and review complete.
- [ ] Checkpoint saved and verified local commit created.

### Task 8 — An extraction stays temporary; the Requirement view shows the Pack

**Requirements:** SYS-R08.
**Files:** `requirements/workspace.py` `extract_section`, the Requirement page that lists a Pack's Requirements, `app/server.py` extract POST and the accept action, `tests/test_sys03_door.py`, `tests/test_requirements_extract.py`. Do not edit `export_pack` or `selection.json`. Prefer temp paths from Task 7’s `curbpack-studio.json` when that file exists; otherwise keep today’s pilot temp wiring.
**Test first:** The door repo lists the pack. `<packs_dir>/<pack-id>/<pack-version>/pack.json` and `<packs_dir>/<pack-id>/<pack-version>/<requirement-id>.json` already exist. The Requirement view shows that existing Requirement and labels it as existing. POST extract writes the new extraction only in memory or in Studio's existing temp/working-copy storage, and does not create or change a file under `<packs_dir>/<pack-id>/<pack-version>/`. The page shows that extraction as distinct from the existing Requirement. The accept process then either updates `<requirement-id>.json` or writes a new Requirement file beside `pack.json`. Extract alone does not. `create_extraction_copy` still writes the timestamped copy PE-08 and PE-11 already read. `tests/test_requirements_compare.py` and the PE-11 export tests keep using that copy.
**Validation:** `python3 -m unittest tests.test_sys03_door tests.test_requirements_extract tests.test_requirements_compare`
**Stop if:** showing the existing Requirement or accepting an extraction needs a new field on `pack.json` or `curbpack.json`.

- [ ] RED observed for the intended behavior.
- [ ] Minimal implementation and GREEN verified.
- [ ] Relevant regressions and review complete.
- [ ] Checkpoint saved and verified local commit created.

## Work log

- **2026-10-29 / Task 0:** Replaced the previous plan revision, which targeted a single `curbpack` key and one shared "Reports" directory for both the run result and the review report. `docs/reference/workspace.md` (recorded authoritative in `docs/agile/DECISIONS.md` on 2026-10-29) instead names four independent fields — `packs_dir`, `claims_dir`, `results_dir`, `reports_dir` — with no `curbpack` key and no `temp` field in `curbpack.json`; run output is `run-result_<UTC>.json` under `results_dir`, review output is `review-report_<UTC>.json` under `reports_dir`. The story `SYS-03-one-repo-door.md` was rewritten to the same contract in this revision. Tasks 1–7 retarget every path and file-name reference accordingly; Task 1 is new (the field-resolution groundwork the earlier plan assumed already existed under the single key). Baseline test run recorded above; it is pre-existing dirty-worktree WIP unrelated to this docs-only revision. No product code in this revision.
- **2026-10-29 / Task 0 plan review:** Independent review returned Issues Found: (1) SYS-R01 start-empty / `_start_empty_folder` omitted; (2) `_write_curbpack` not named. Fixed; re-review **Approved**.
- **2026-10-29 / walkthrough:** Maintainer: all product views empty without repo; `curbpack.json` create/edit via Save/Cancel dialog (Requirements-dialog style); new Studio config page for `curbpack-studio.json` with Save/Cancel. Story SYS-R01 rewritten; SYS-R07 broadened; SYS-R09 added. Plan status back to **DRAFT** pending re-approval after the walkthrough finishes. Task 3 retargeted to the dialog; Task 7 = Studio config page; former extraction task renumbered Task 8.
- **2026-10-29 / walkthrough:** SYS-R02 GWT: `claims_dir` / `packs_dir` explicitly from the open repo’s `curbpack.json`.
- **2026-10-29 / walkthrough:** Scope narrowed: SYS-03 is I/O binding to `curbpack.json` / `curbpack-studio.json` only. Approved app behaviour (Discover choose/diff/etc.) must not be removed. Story rewritten; plan Goal/Task 5 updated.
- **2026-10-29 / walkthrough:** Maintainer OK on SYS-R01–SYS-R09. Added R07: each view shows the concrete paths in use. General directory/pack-compare tool deferred — idea parked in DECISIONS under EP-09 (or EP-11 if version-lifecycle).
- **2026-10-29 / walkthrough:** Maintainer: separate story CHK-07 — curbcheck uses `curbpack.json` path fields, owns defaults factory + CLI docs rewrite. SYS-03 create dialog consumes that API; until CHK-07, write §2.2 values directly. `curbcheck-cli.md` marked pending CHK-07 (`--packs`/`--requirements` = id filters, not dirs).
- **2026-10-29 / Task 0:** Plan APPROVED by danielfl. `open-repo.json` is Studio workspace state for SYS-R07 (not a product file). Task 1 IMPL-START.
- **2026-10-29 / Task 1:** `validate_curbpack_config` requires workspace.md §2.2 keys and rejects `curbpack`. Resolvers `packs_dir`/`claims_dir`/`results_dir`/`reports_dir`. `run_repository` loads `<packs_dir>/<id>/<version>/pack.json` and `claims_dir`; unselected Claims omitted (`checks/ARCHITECTURE.md` updated). `_write_curbpack` preserves the four path fields. CLI default out is `<results_dir>/run-result.json`. `curbpack_directory`/`claim_catalog` left for Studio WIP (Task 3+). Review Important: `_write_curbpack` test + architecture omit-unselected; re-review Approved (`2f52e822`). Command: `python3 -m unittest tests.test_sys03_door tests.test_curbcheck_package tests.test_m4_checks` — Ran 28 tests, OK. Minor left: leftover helpers.
- **2026-10-29 / Task 2:** `discovery/door.py` stores `open-repo.json` as `{"id": ...}` only. `open_repo_id` works with no curbpack.json. Extra keys / empty / unknown id mean not open. `save_directory_fields` validates relative dirs. First review Important: write-side tests; re-review Approved (`ed5a41af`). `python3 -m unittest tests.test_sys03_door` — Ran 10 tests, OK.
- **2026-10-29 / Task 3:** Door UI. Empty Pack Sources / Pack Editor / Discover / Check / Review without open repo. `curbpack.json` Save/Cancel dialog (Requirements-dialog style). Start empty registers+opens, does not write the file. Add writes `<packs_dir>/<id>/<version>/pack.json` (`version` from `draft_pack` only). Empty `claims_dir` says No Claims. Paths shown. Pack Editor prefers the open repo's packs_dir row. Review Compile hidden until Task 6 and POST compile does not write the workspace product. First review Important (`45f1f31a`): Pack Editor catalog-first, missing claims_dir chrome, adapter drop, Review workspace preview, old `curbpack_directory` lookup, section-V test removed. Re-review Important leftovers (`372c0f7b`): adapter_id+non-adapter URL still accepted; Compile still wrote workspace — both closed in this step. No third review. Minor left: comma-separated packs field (CHK-07 checkboxes), three pickers, `created_curbpack` until CHK-07. Command: `python3 -m unittest tests.test_sys03_door tests.test_cover_navigation tests.test_requirements_ui tests.test_requirements_export tests.test_requirements_catalog` — Ran 45 tests, OK.
- **2026-10-29 / Task 4:** Check I/O. POST `/check` opens the chosen repo, saves the four path fields without rewriting `packs`, and writes `<results_dir>/run-result_<UTC>.json` via `run_and_write`. A second run leaves the first file unchanged. GET `/check` does not fall back to workspace `product/`. `?result=` is confined to that repo's `results_dir`. First review Important: `?result=` confinement + include-list HTTP case. Re-review Important leftover (`4a846ca2`): outsider named `foreign-run-result_…` never reached the directory bound — closed by writing a valid `run-result_*.json` outside `results_dir`. No third review. Minor left: unused `_repo_claims` / `_pack_directory_for_check` helpers, leftover `ask_read`, same-second `time.sleep(1)` in `_new_run_result_path`. Command: `python3 -m unittest tests.test_sys03_door tests.test_check_editor tests.test_m4_checks` — Ran 21 tests, OK.
- **2026-10-29 / Task 5:** Discover I/O. Requirements from `packs_dir` for packs named in the open repo's `curbpack.json`; Claims read/write `<claims_dir>/<id>.json`. Working-copy timestamp stays as Discover job identity only. First review Important (`42019176`): working-copy fallback, `repo/claims` default, Claim-editor lookup, git-seal relative path. Re-review Important leftovers (`1281d823`): Claim POST still used working-copy ids — closed via `_claims_lookup`; silent empty Discover run without `curbpack.json` — closed (`repo_pack_requirements` raises, `_start_discover` validates the file). Coverage `load_run` of `<repo>/.curbpack/run-result.json` deferred to Task 6 (recorded on that task). No third review. Command: `python3 -m unittest tests.test_sys03_door tests.test_discover_claims_ui tests.test_discover_layout tests.test_claims_binding_ui` — Ran 26 tests, OK.
- **2026-10-29 / Task 6:** Review I/O. Compile writes `<reports_dir>/review-report_<UTC>.json`; a second compile leaves the first file. GET `/review` with no saved report previews the latest `results_dir` run and does not write. Discover-from-review greying `load_run` reads dated `results_dir` files. `prepare_demo` registers `sample-product`, copies the pack into `packs_dir`, and sets `open-repo.json`. First review Important (`cf7cf3c1`): missing preview after Check; `tests.test_review_coverage_ui` still wrote `product/claims` and undated `run-result.json`. Re-review Approved (`25708dae`). No third review. Minor left: confirm-class names in `test_review_report_kept.py`; Cover/`Workspace.run_path` still `docs/reports/review-report.json`; unused `report_exists` on `review_page`. Command: `python3 -m unittest tests.test_sys03_door tests.test_ui_smoke tests.test_review_report_kept tests.test_review_replace_flow tests.test_review_discover_again tests.test_review_compile tests.test_review_coverage_ui` — Ran 31 tests, OK.
