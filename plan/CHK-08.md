# CHK-08 — Studio Check and Review talk to the new curbcheck

## Summary

- **Story:** `docs/agile/epics/01-pack-editor/stories/CHK-08-studio-check-review-curbcheck.md`
- **Goal:** Studio Check and Review call the CHK-07 Python API (`run_repository` / `run_and_write` with `packs_root=None`, `created_curbpack`) so results land under `results_dir` as `run-result_<UTC>.json` and reports under `reports_dir` as `review-report_<UTC>.json`, with the pages showing those paths. Approved Check/Review UX stays.
- **Scope / exclusions:** Story CHK-R01–CHK-R04. Inventory and retarget Studio Check/Review tests listed below. Do **not** change CHK-07 CLI. Do **not** implement `unsigned_requirements` behaviour. Do **not** do SYS-03 Task 8. Do **not** redesign or gut Check/Review/Discover pages. Do **not** invent Packs v2 fields. Cover `workflow.py` / `Workspace.run_path` sample-product paths stay out (not those pages). `tests/test_m4_checks.py` and other curbcheck unit/package tests stay out (CHK-07).
- **Baseline:** Branch `main` at `c03cd85` (Close CHK-07). Unrelated dirty WIP preserved (not reset, not committed): `app/pages.py`, `app/server.py`, `checks/run.py`, `common/validate.py`, `docs/agile/DECISIONS.md`, `docs/concepts/packs.md`, `docs/reference/configuration.md`, `docs/reference/workspace.md`, `requirements/extract/assemble.py`, `requirements/ui/pages.py`, `requirements/ui/try_discovery.py`, `scripts/release/publish.py`, `tests/test_release_publish.py`, `tests/test_requirements_produce.py`, `tests/test_requirements_ui.py`, `tests/test_sys03_door.py`, untracked `requirements/extract/adapters/manual/`. Overlapping dirty hunks in `app/server.py` / `app/pages.py` / `checks/run.py` are Pack-edit CSS/adapter and an unversioned `pack.json` fallback — **not** Check/Review rewiring; fold only in-scope hunks. `python3 -m unittest tests.test_check_editor tests.test_review_compile tests.test_review_report_kept tests.test_review_replace_flow tests.test_review_discover_again tests.test_review_coverage_ui tests.test_review_coverage tests.test_ui_smoke tests.test_chk07_curbcheck.DefaultsFactoryTest tests.test_sys03_door.CheckIoTest tests.test_sys03_door.ReviewIoTest` — sandbox: Ran 25 tests, 4 errors (`git init -b main` in `prepare_demo`, sandbox). Unsandboxed (`required_permissions: ["all"]`): `tests.test_review_report_kept tests.test_review_discover_again tests.test_ui_smoke tests.test_sys03_door.CheckIoTest tests.test_sys03_door.ReviewIoTest tests.test_check_editor` — Ran 7 tests, OK. Current Check POST already calls `run_and_write(repo, None, out)` with `out = _new_run_result_path(results_dir(...))` and redirects `result=` to that path. Review compile already reads `_confined_run_result_path(results_dir)` and writes `_new_review_report_path(reports_dir)`. Door `created_curbpack` is `checks.defaults.created_curbpack`. Remaining: Studio still has a second dated-name helper `app/server.py` `_new_run_result_path`; `tests/test_e2e_annex_vii.py` still passes a packs **directory** as `packs_root` and writes undated `.curbpack/run-result.json`; `tests/test_check_editor.py` saves path fields only (Check-run evidence lives in `CheckIoTest`). `Workspace.run_path` / `workflow.py` still name the sample-product undated files — out of this story.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | APPROVED |
| Approved by | danielfl, 2026-10-29 (CHK-08 decided; “kör den” after CHK-07 closed — proceed Task 1–4; OPEN-1–OPEN-5 as this plan) |
| Current task | Close — move plan to impl/CHK-08.md |
| Last completed task | Task 4 |
| Last verified tests | 2026-10-29: `python3 -m unittest tests.test_chk08_studio tests.test_check_editor tests.test_e2e_annex_vii tests.test_review_compile tests.test_review_report_kept tests.test_review_replace_flow tests.test_review_discover_again tests.test_review_coverage_ui tests.test_review_coverage tests.test_ui_smoke tests.test_sys03_door.CheckIoTest tests.test_sys03_door.ReviewIoTest` — Ran 28 tests, OK |
| Last checkpoint commit | This commit. Resolve with `git log -1 --format=%H -- plan/CHK-08.md`. |
| Requirements | Story CHK-R01–CHK-R04 in `CHK-08-studio-check-review-curbcheck.md`. No new `docs/req/` row. Legacy `docs/req/checks.md` CHK-R01–CHK-R17 are CHK-05/CHK-06. CHK-07 story-local CHK-R01–CHK-R06 are the CLI contract. |
| Packs v2 | `docs/reference/workspace.md` owns path fields and dated names (§2.2, §2.3, §3). `docs/reference/packs2.md` §3.1 owns the run-result object. This plan edits neither. |
| Blockers | None |
| Exact next action | Close CHK-08: move `plan/CHK-08.md` to `impl/CHK-08.md`, then `python3 scripts/check_story_plan.py CHK-08 --phase done`. |

## Requirements and acceptance mapping

Requirements live in the story. This table only maps each id to its acceptance test.

| Requirement ID | Story | Test / observed evidence | Status |
| --- | --- | --- | --- |
| CHK-R01 | CHK-08 | `tests/test_chk08_studio.py` (Check POST → dated `results_dir` file, page shows path, `packs_root=None`); regression `tests.test_sys03_door.CheckIoTest` | VERIFIED |
| CHK-R02 | CHK-08 | `tests/test_chk08_studio.py` (blank body is `created_curbpack`; door is the same function); regression `tests.test_chk07_curbcheck.DefaultsFactoryTest` | VERIFIED |
| CHK-R03 | CHK-08 | `tests/test_chk08_studio.py` (compile reads that run, dated `reports_dir`, not workspace `product/`); regression `tests.test_sys03_door.ReviewIoTest` | VERIFIED |
| CHK-R04 | CHK-08 | Inventory below retargeted; listed suites green without a packs-directory `packs_root` | VERIFIED |

### CHK-R04 inventory (this plan)

| Path | What is wrong today | Task |
| --- | --- | --- |
| `tests/test_check_editor.py` | Saves the four path fields only; does not assert Check POST / dated `results_dir` | 1, 4 |
| `tests/test_sys03_door.py` `CheckIoTest` | Already asserts dated `results_dir` + no `product/` fallback. Keep as regression; do not rewrite SYS-03 WIP hunks | 1 |
| `tests/test_sys03_door.py` `ReviewIoTest` | Already asserts dated `reports_dir` + no `product/` compile. Keep as regression | 3 |
| `tests/test_review_report_kept.py` | Already uses `results_dir` / `reports_dir` + `run_and_write(..., None, ...)`. Keep | 4 |
| `tests/test_review_replace_flow.py` | Already dated `reports_dir`. Keep | 4 |
| `tests/test_review_discover_again.py` | Already dated `reports_dir`. Keep | 4 |
| `tests/test_review_coverage_ui.py` | Already dated `run-result_*.json` under `.curbpack`. Keep | 4 |
| `tests/test_review_compile.py` | Direct `compile_report`; `durable_report_path` is a unit-test write helper, not Studio HTTP. Do not retarget Cover. Keep | 4 |
| `tests/test_review_coverage.py` | Presentation hook only. Keep | 4 |
| `tests/test_ui_smoke.py` | Already asserts no `product/.curbpack/review-report.json`. Keep | 4 |
| `tests/test_e2e_annex_vii.py` | Incomplete `curbpack.json` (no §2.2 path fields); `run_and_write(repo, root / "packs", repo / ".curbpack" / "run-result.json")` — packs-directory `packs_root` and undated name | 4 |

Out of this story (do not retarget here): `tests/test_m4_checks.py` (CHK-07 curbcheck unit; still passes `packs_root`). `tests/test_chk07_curbcheck.py`, `tests/test_curbcheck_package.py`, `make test-curbcheck`. `workflow.py` / `Workspace.run_path` / `review.compile.durable_report_path` (Cover sample-product paths). SYS-03 Task 8. Unrelated dirty WIP listed in Summary.

## Tasks

### Task 0 — derive and approve requirements and plan

**Inputs / contracts:** CHK-08 story (decided 2026-10-29); `impl/CHK-07.md`; `docs/reference/workspace.md` §§2–3; `docs/reference/packs2.md` §2.3 and §3.1; `checks/run.py` `run_repository` / `run_and_write` / `new_run_result_path`; `checks/defaults.py` `created_curbpack`; `app/server.py` POST `/check` and `/review/compile`; `tests/test_sys03_door.py` CheckIoTest / ReviewIoTest; inventory above.
**Change files:** `docs/agile/epics/01-pack-editor/stories/CHK-08-studio-check-review-curbcheck.md`, `plan/CHK-08.md`.
**Acceptance / stop:** human approval recorded, including OPEN-1–OPEN-5. No product code in this task.

- [x] Independent plan review completed.
- [x] Baseline observed; OPEN items recorded.
- [x] Plan approved (record approver).

### Task 1 — Check POST uses the shared run entry and dated `results_dir` JSON

**Requirements:** CHK-R01
**Files:** `tests/test_chk08_studio.py` (new). `tests/test_check_editor.py` (add the Check-run assertion the inventory names: POST check writes `{results_dir}/run-result_<UTC>.json` and the page shows that path). `app/server.py` POST `/check` only: call `checks.run.new_run_result_path` instead of `_new_run_result_path`; delete `_new_run_result_path` if nothing else calls it. Keep `_new_review_report_path` / `_new_dated_json` for reports (no checks helper). Do not edit dirty Pack-edit / CSS hunks. Do not pass `pack_ids` / `requirement_ids` (Studio Check does not need CLI flags). Do not edit `checks/ARCHITECTURE.md` (still says Run uses a packs root) or Cover architecture paths.
**Test first:** Open repo, valid `curbpack.json` with distinct `results_dir`. POST `/check` `action=check` writes exactly one `{results_dir}/run-result_<YYYYMMDDTHHMMSSZ>.json`, the HTML contains that absolute path, and `run_and_write` was the write (file validates as a run-result). A second POST writes a second file and leaves the first bytes unchanged. Packs/claims come from the file’s directories (`packs_root=None`). Decoy pack: a sibling of the open repo (workspace `product/`, same pattern as `CheckIoTest`), not Studio’s workspace-root `packs/`. SYS-03 `CheckIoTest` already covers most of this — if the new test already PASSES, record already-present; still switch the dated helper if `_new_run_result_path` remains (OPEN-1). That helper switch is a same-name refactor, not a fake RED.
**Validation:** `python3 -m unittest tests.test_chk08_studio tests.test_check_editor tests.test_sys03_door.CheckIoTest`
**Stop if:** Check would need a new `curbpack.json` field, a packs-directory override, or a redesigned Check page.

- [x] RED observed for the intended behavior (or existing PASS demonstrated).
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

### Task 2 — Studio blank `curbpack.json` body is `created_curbpack`

**Requirements:** CHK-R02
**Files:** `tests/test_chk08_studio.py`. Confirm `discovery.door.created_curbpack is checks.defaults.created_curbpack`. Confirm `app/server.py` create/edit (`_documents_model` `curbpack_fields`, `_save_curbpack_form` empty-hints fallback) calls that function and does not contain a second created-file dict. If a leftover literal of a §2.2 created-file value remains in the Check/Review/create path (`app/server.py`, `discovery/door.py`, create-dialog seed), delete it. Do not rewrite `requirements/ui/pages.py` WIP; if that file still has a display fallback such as `or "reject"` and the dialog fields already come from `created_curbpack()`, that fallback is unused for create — change it only if it is a second created-file document (it is not, if it only names the same select default the factory already put in `fields`).
**Test first:** Create-dialog fields for a repo with no `curbpack.json` equal `created_curbpack()` path values (`packs_dir` `curbpack/packs`, `claims_dir` `curbpack/claims`, `results_dir` `.curbpack`, `reports_dir` `curbpack/reports`, `unsigned_requirements` `reject`). `discovery.door.created_curbpack is checks.defaults.created_curbpack`. CHK-07 `DefaultsFactoryTest.test_studio_calls_the_same_defaults_function` already PASSes — if this task’s test already PASSes and no second literal exists, record already-present; no production diff.
**Validation:** `python3 -m unittest tests.test_chk08_studio tests.test_chk07_curbcheck.DefaultsFactoryTest tests.test_sys03_door.StudioConfigTest`
**Stop if:** create/edit would need a key or created-file value that is not in workspace.md §2.2 / §2.3, or would change SYS-03 dialog UX.

- [x] RED observed for the intended behavior (or existing PASS demonstrated).
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

### Task 3 — Review compile reads that run and writes dated `reports_dir`

**Requirements:** CHK-R03
**Files:** `tests/test_chk08_studio.py`. `app/server.py` POST `/review/compile` only if it still reads workspace `product/` or an undated report path (today it does not: it uses `results_dir` / `reports_dir`). Do not change `durable_report_path` or Cover.
**Test first:** Check writes a dated run under the open repo’s `results_dir`. Compile reads that file and writes `{reports_dir}/review-report_<YYYYMMDDTHHMMSSZ>.json`. The page shows that path. A second compile leaves the first file. `<workspace>/product/` has a different Claim/run; the report does not contain it and does not write `product/docs/reports/` or `product/.curbpack/review-report.json`. SYS-03 `ReviewIoTest` already covers this — if the new test already PASSes, record already-present; no production diff unless a leftover `product/` read remains.
**Validation:** `python3 -m unittest tests.test_chk08_studio tests.test_sys03_door.ReviewIoTest tests.test_review_report_kept tests.test_ui_smoke`
**Stop if:** compile would need a new `curbpack.json` field or would redesign the Review page.

- [x] RED observed for the intended behavior (or existing PASS demonstrated).
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

### Task 4 — Inventory: retarget remaining Studio Check/Review / related e2e tests

**Requirements:** CHK-R04
**Files:** inventory rows above. Must retarget `tests/test_e2e_annex_vii.py`: write a complete workspace.md §2.2 `curbpack.json` via `created_curbpack` (keep that test’s custom `search_hints` as an override); copy the Annex VII pack into `<repo>/<packs_dir>/cra-baseline/<version>/` (`version` from `pack.json`; do not set `packs_dir` to an absolute path or `..`); after that copy, later `load_requirement` / `compile_report` reads use that versioned tree (do not delete `root/packs` until those reads move). `run_and_write(repo, None, out)`; `out` may stay an explicit `-o` path (`repo / ".curbpack" / "run-result.json"` is allowed as `-o PATH`, not as the page’s dated name). Claims already live at `curbpack/claims` (created-file `claims_dir`). Do not use or land the dirty unversioned `pack.json` fallback in `checks/run.py`. Confirm the other inventory rows already match CHK-R01/CHK-R03; only edit them if a leftover packs-directory `packs_root` or `product/` sample remains. Do not retarget `tests/test_m4_checks.py`. Do not edit architecture documents.
**Test first:** `tests.test_e2e_annex_vii` fails (or would fail) if `packs_root` is omitted against the current incomplete `curbpack.json` / sibling `root/packs` tree. After retarget, the scenario still PASSes with `packs_root=None`. A CHK-08 inventory assertion: listed files do not call `run_and_write` with a packs **directory** `packs_root` (except `tests/test_m4_checks.py`, which is out of inventory).
**Validation:** `python3 -m unittest tests.test_chk08_studio tests.test_check_editor tests.test_e2e_annex_vii tests.test_review_compile tests.test_review_report_kept tests.test_review_replace_flow tests.test_review_discover_again tests.test_review_coverage_ui tests.test_review_coverage tests.test_ui_smoke tests.test_sys03_door.CheckIoTest tests.test_sys03_door.ReviewIoTest`
**Stop if:** e2e would need a `curbpack.json` path that is absolute or contains `..`, or would require changing Check/Review UX.

- [x] RED observed for the intended behavior (or existing PASS demonstrated).
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

## Open decisions

Proposals below are this plan’s intended implementation. They are not a new Packs v2 field. Stop rather than invent a different contract if review or the maintainer rejects one.

**OPEN-1 — Studio Check always writes JSON.** The CLI writes JSON only with `-j`/`-o`. The Check page’s existing Run action already writes a run-result file (`checks/ARCHITECTURE.md` Run → `run_and_write`). **Proposal:** keep that page contract. Call `run_and_write(repo, None, new_run_result_path(results_dir(...)))`. Do not add a stdout-only Studio Check. Share `checks.run.new_run_result_path` so Studio does not keep a second dated-name helper. Keep `_new_review_report_path` in `app/server.py` (no checks helper for reports).

**OPEN-2 — `pack_ids` / `requirement_ids`.** CHK-07 added keyword-only overlays for CLI flags. **Proposal:** Studio Check does not send those overlays; selection is the open repo’s `curbpack.json`.

**OPEN-3 — Door import vs `checks.defaults`.** CHK-07 Task 4 made `discovery.door.created_curbpack` the same function. **Proposal:** Studio may keep importing from `discovery.door`. Do not force every caller onto `checks.defaults` if the object is the same function. Fail only a second literal dict of created-file values.

**OPEN-4 — Cover sample-product paths.** `workflow.py`, `Workspace.run_path`, and `durable_report_path` still name undated sample-product files. **Proposal:** out of CHK-08. Check/Review HTTP already uses `results_dir` / `reports_dir`. Do not retarget Cover in this story.

**OPEN-5 — Related e2e `packs_root`.** `tests/test_e2e_annex_vii.py` is the related e2e the story names. **Proposal:** retarget as Task 4 (complete §2.2 file, versioned pack copy into `packs_dir`, `packs_root=None`). Explicit `-o` out path may stay. `tests/test_m4_checks.py` stays on `packs_root` (CHK-07 unit tests, out of this story).

## Work log

- **2026-10-29 / Task 4:** CHK-R04. RED: `InventoryTest` failed on seven `run_and_write(repo, root / "packs", …)` lines in `tests/test_e2e_annex_vii.py`. GREEN: complete `created_curbpack` file; copy sealed pack into versioned `packs_dir`; `run_and_write(repo, None, out)`; later requirement reads use that tree. Command: `python3 -m unittest tests.test_chk08_studio tests.test_check_editor tests.test_e2e_annex_vii tests.test_review_compile tests.test_review_report_kept tests.test_review_replace_flow tests.test_review_discover_again tests.test_review_coverage_ui tests.test_review_coverage tests.test_ui_smoke tests.test_sys03_door.CheckIoTest tests.test_sys03_door.ReviewIoTest` — Ran 28 tests, OK. Review (`1f6da09a`) no Critical/Important. Minors: inventory is a same-line substring scan; search_hints override mutates a factory copy. `tests/test_m4_checks.py` left on `packs_root`.
- **2026-10-29 / Task 3:** CHK-R03. Already present: compile reads `results_dir` dated run and writes dated `reports_dir`; no `product/` fallback. New test PASSed on first run. No production diff. Command: `python3 -m unittest tests.test_chk08_studio tests.test_sys03_door.ReviewIoTest tests.test_review_report_kept tests.test_ui_smoke` — Ran 7 tests, OK. Review (`20658ac8`) no Critical/Important. Minors: import grouping (fixed); compare `report["run_result"]` to the Check file (added); confined `?result=` not used by Compile POST (recorded, no change).
- **2026-10-29 / Task 2:** CHK-R02. Already present: door is `checks.defaults.created_curbpack`; create dialog fields come from that function; no second created-file dict in `app/server.py` / `discovery/door.py`. New test PASSed on first run. No production diff. Command: `python3 -m unittest tests.test_chk08_studio tests.test_chk07_curbcheck.DefaultsFactoryTest tests.test_sys03_door.StudioConfigTest` — Ran 6 tests, OK. Review (`8d37836f`) no Critical/Important. Minor: unsigned_requirements HTML was tautological; tightened to `value="reject" selected`. Left `requirements/ui/pages.py` `or "reject"` (WIP, display fallback).
- **2026-10-29 / Task 1:** CHK-R01. Already present: Check POST `run_and_write(repo, None, dated path)`; new tests PASSed on first run (not a setup error). GREEN refactor: share `checks.run.new_run_result_path`; delete `_new_run_result_path`. Command: `python3 -m unittest tests.test_chk08_studio tests.test_check_editor tests.test_sys03_door.CheckIoTest` — Ran 3 tests, OK. Review (`40e33488`) no Critical/Important. Minors: decoy claim was `HIDDEN-REQ` (fixed to `CRA-PURPOSE`); unused `_get` (dropped).
- **2026-10-29 / Task 0:** Inspected HEAD `c03cd85`. Dirty WIP left uncommitted (see Summary). Check POST already `run_and_write(repo, None, _new_run_result_path(results_dir))`; Review compile already dated `reports_dir`; door is the defaults function. Baseline: sandbox 25 tests / 4 `git init` errors; unsandboxed 7 Check/Review HTTP tests OK. Expanded story GWT. Drafted this plan from `plan/TEMPLATE.md`. Independent plan review (`51b21d07`) Approved, no Issues. Advisory folded: Check-run assertion in `test_check_editor.py` (not a thin pointer); decoy is workspace `product/` sibling; e2e later reads use the versioned copy; do not land unversioned `pack.json` fallback; do not edit architecture docs; leave `test_m4_checks.py` out.
