# SYS-03 — One repository is the pilot door

## Summary

- **Story:** `docs/agile/epics/01-pack-editor/stories/SYS-03-one-repo-door.md`
- **Goal:** Pack Editor, Discover, Check, and Review open one chosen repository. Packs, Claims, the run, and the report are the files under the directory named by that repository's `curbpack.json`.
- **Scope / exclusions:** SYS-R01–SYS-R08 on `/requirements`, `/discover`, `/check`, and `/review`. The directory is the `curbpack` value in that repository's `curbpack.json`. Absent means `curbpack`. Resolved paths are `<directory>/packs/<pack-id>/pack.json`, `<directory>/claims/<claim-id>.json`, and `<directory>/reports/run-<YYYYMMDDTHHMMSSZ>.json` plus `review-<YYYYMMDDTHHMMSSZ>.json`. Candidates and extractions are not those files. A later run or report does not replace an earlier file. No version pin. Do not read or write `.curbpack.json`. Do not keep `registered_sources.json` as the Pack list. The chosen repository id is workspace state. The directory is not. Do not edit `export_pack`, `plan/PE-11.md`, or the Export Pack form in `_document_row`. The URL cell in that row gains the muted pack directory. `selection.json` stays the working-copy selection PE-11 uses. CHK-01 still owns a pedagogical include/exclude editor; this plan shows the lists the file already has and does not add a second id-list editor. Do not invent a Packs v2 field.
- **Baseline:** 2026-10-28, dirty worktree on `main` at `781f787`. Unrelated edits stay. `curbpack_directory` and `run_repository` already read the file and load `<directory>/packs` and `<directory>/claims`. `run_repository` still raises when a Claim's Requirement is not selected. Check still offers "Read it and tick the packs it names?", calls `run_pack_directories`, and writes `<repo>/.curbpack/run-result.json`. Pack Editor lists `registered_sources.json`. Discover without a named repo uses `Workspace.repo` (`<workspace>/product/claims`). Review `preview_report` reads `ws.run_path` and `ws.repo / "claims"`. `Workspace.report_path` is the sample product report path.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | DRAFT |
| Approved by | Pending human approval of this plan. The story behavior was decided by danielfl on 2026-10-28. |
| Current task | Task 0 — plan review, then maintainer approval |
| Last completed task | None |
| Last verified tests | Not run for this plan revision. Earlier the same day, `python3 -m unittest tests.test_curbcheck_package tests.test_m4_checks tests.test_e2e_annex_vii tests.test_requirements_export tests.test_review_report_kept` — Ran 48 tests, OK. |
| Last checkpoint commit | None. This plan is uncommitted. |
| Requirements | Story SYS-R01–SYS-R08. No new `docs/req/` row. |
| Packs v2 | `docs/reference/packs2.md` in the working tree. Allowed `curbpack.json` keys include `packs`, `requirements`, `exclude_requirements`, `search_hints`, and `curbpack`. The key `hunt` is rejected. |
| Blockers | None. The 2026-10-28 plan that stored a packs root in `pilot-door.json` and forbade a path in `curbpack.json` is replaced by this file. |
| **Exact next action** | Wait. danielfl is still correcting the story. Do not write door code and do not start another plan review until that list stops. |

## Requirements and acceptance mapping

Story criteria are authoritative. One test may cover several rows. Do not add a derived requirement in `docs/req/`.

| Requirement ID | Story | Test / observed evidence | Status |
| --- | --- | --- | --- |
| SYS-R01 | SYS-03 | `tests/test_sys03_door.py`: no open repo shows a repository picker and no Pack row from `registered_sources.json`. An open repo shows the absolute `curbpack.json` path, each id, the `curbpack` value or `curbpack`, a row only when `<directory>/packs/<id>/pack.json` exists, a missing id as missing, and the pack directory in muted text under the URL. No `curbpack.json` says the file is absent, shows no rows, and does not read `.curbpack.json`. | DRAFT |
| SYS-R02 | SYS-03 | The same test: missing or empty `<directory>/claims/` says there are no Claims. Add writes `<directory>/packs/<pack-id>/pack.json`, appends that id, and does not write `registered_sources.json`. | DRAFT |
| SYS-R03 | SYS-03 | Two registered repos. Saving `curbpack` on one writes only that repo's file. The other file is unchanged. Claims are read from `<that directory>/claims/`. A Claim whose Requirement is not in the resolved Packs is shown as not in those Packs. The Claim file and the report file keep their bytes. | DRAFT |
| SYS-R04 | SYS-03 | Discover names the same repository and directory and offers Requirements from `<directory>/packs/`. Existing Claims are the files in `<directory>/claims/`. A candidate stays in memory and is visibly not an existing Claim. Only the create-or-update process writes `<directory>/claims/<claim-id>.json` or updates that file. No other action creates `<workspace>/product/claims/` or `<repository>/claims/`. | DRAFT |
| SYS-R05 | SYS-03 | Check runs `run_repository`, writes `<directory>/reports/run-<stamp>.json`, leaves an earlier run file in place, shows that path, honors `requirements` and `exclude_requirements`, and a Claim for an unselected Requirement is absent from the result while a selected Claim still runs. The run does not raise for that extra Claim. | DRAFT |
| SYS-R06 | SYS-03 | Review compiles the dated run and `<directory>/claims/`, writes `<directory>/reports/review-<stamp>.json`, leaves an earlier report in place, and names the repository and the directory. It does not compile `<workspace>/product/`. | DRAFT |
| SYS-R07 | SYS-03 | Choosing the repo on any of the four pages makes the other three name it. With no open repo, Discover, Check, and Review say none is chosen and do not read `<workspace>/product/`. | DRAFT |
| SYS-R08 | SYS-03 | The Requirement view lists Requirement files that already sit beside `<directory>/packs/<pack-id>/pack.json` and distinguishes them from an extraction. Extraction leaves the result in memory or on temp disk. Only the accept process writes a new Requirement file beside `pack.json` or updates the existing one. | DRAFT |

## Tasks

### Task 0 — approve this plan

**Inputs / contracts:** SYS-03 story; `docs/reference/packs2.md` §2.3; `checks/run.py` `curbpack_directory` and `run_repository`; `discovery/repos.py` `product_repos.json`; `app/server.py` Pack Editor, Check, Discover, and `preview_report`.
**Change files:** `plan/SYS-03.md` only.
**Acceptance / stop:** human approval recorded. No product code in this task.

- [ ] Independent plan review completed.
- [ ] Plan approved (record approver).

### Task 1 — Remember which repository is open

**Requirements:** SYS-R07 storage rule. The directory stays in the product file.
**Files:** `discovery/door.py`, `tests/test_sys03_door.py`.
**Test first:** `<workspace>/open-repo.json` is `{"id": "<repo id>"}` and nothing else. The id must already be in `product_repos.json`. A missing file, an empty id, or an unknown id means no repository is open. Choosing repo A then repo B stores only B. The file is not written into either product repository. Neither `curbpack.json` is modified by choosing a repository. `selection.json` is not written. Resolving an open repo returns that repo path and `curbpack_directory(repo)`. Saving a relative `curbpack` value writes that key in that repo's file and leaves the other repo's file byte-for-byte unchanged. An absolute value or a `..` segment is rejected and the file is unchanged.
**Validation:** `python3 -m unittest tests.test_sys03_door`
**Stop if:** the directory would be stored in the workspace, or the open repo would be stored by adding a path key to `curbpack.json`.

- [ ] RED observed for the intended behavior.
- [ ] Minimal implementation and GREEN verified.
- [ ] Relevant regressions and review complete.
- [ ] Checkpoint saved and verified local commit created.

### Task 2 — Pack Editor opens that repository

**Requirements:** SYS-R01, SYS-R02, SYS-R03, SYS-R07 for `/requirements`.
**Files:** `app/server.py` GET/POST `/requirements` and `/requirements/documents`, `requirements/ui/pages.py` door block and the URL cell of `_document_row`, `tests/test_sys03_door.py`. Do not edit the Export Pack form or `export_pack`.
**Test first:** GET `/requirements` with no open repo shows the picker of registered repositories and does not list a Pack that exists only in `registered_sources.json`. POST `repo_id` writes `open-repo.json`. The chosen repo's `curbpack.json` lists `present` and `missing`. `present` has `<directory>/packs/present/pack.json`. The page shows the absolute file path and the directory. `present` has a row because that `pack.json` exists. The URL cell shows `source.url` and, under it in muted text, the pack directory. `missing` is shown as missing and has no Sections row. A repo with no `curbpack.json`, and with `.curbpack.json` containing `not-this`, shows the absent message and no Pack row. Empty `<directory>/claims/` says there are no Claims. POST `curbpack` saves the relative value in that repo's file only. POST Add writes `<directory>/packs/<id>/pack.json` and appends `<id>`. The id is the id `make_document_id` already computes from the document name. `pack.json` validates with `validate_pack`: `id`, `version` `0.1.0` (the draft version `draft_pack` already uses), `name`, and `source.url` from the dialog. It does not call `save_catalog`. A second repo's `curbpack.json` is unchanged. A Claim file under `<directory>/claims/`, including after the saved `curbpack` value changes, whose Requirement is not in the resolved Packs is still listed, labeled not in those Packs, and its bytes are unchanged. It is not read from `<repository>/claims/`. An existing report file's bytes are unchanged.
**Validation:** `python3 -m unittest tests.test_sys03_door tests.test_cover_navigation tests.test_requirements_ui tests.test_requirements_export tests.test_requirements_catalog`
**Add test:** `tests/test_requirements_catalog.py` `test_add_via_http` posts `/requirements/documents`. Update it in this task so Add is `<directory>/packs/<id>/pack.json` plus the appended id, and `save_catalog` is not called.
**Existing tests:** `tests/test_cover_navigation.py`, `tests/test_requirements_ui.py`, and the Pack Editor list assertions in `tests/test_requirements_export.py` open a registered repo and set `open-repo.json` before GET `/requirements`. The Pack they assert is `<directory>/packs/<id>/pack.json` listed in that repo's `curbpack.json`, not a row that exists only in `registered_sources.json`. A catalog-only row such as House Rules is asserted only after that pack file exists under the opened directory. Cover-page links and `/requirements/requirement/<id>` assertions that are not the Pack list stay. Section and export URLs keep `?document=<id>` once that id is the pack id. Do not delete those tests' coverage of Sections or Export Pack. Extract landing beside `pack.json` is Task 6, not this task.
**Stop if:** the row can be shown only by reading `registered_sources.json`, or Add needs a new field on `pack.json` or `curbpack.json` for the adapter. Record that stop. Do not add the field.

- [ ] RED observed for the intended behavior.
- [ ] Minimal implementation and GREEN verified.
- [ ] Relevant regressions and review complete.
- [ ] Checkpoint saved and verified local commit created.

### Task 3 — Check runs that repository

**Requirements:** SYS-R05, SYS-R07 for `/check`.
**Files:** `checks/run.py` `run_repository` only, for the unselected-Claim rule. `app/server.py` `/check`. `app/pages.py` `_curbpack_editor`. `tests/test_sys03_door.py`. `tests/test_check_editor.py`. Leave `run_pack_directories` unchanged.
**Test first:** With no open repo, GET `/check` says none is chosen and does not read `<workspace>/product/curbpack.json`. POST `repo_id` on `/check` writes `open-repo.json`, and GET `/requirements` then names that repo. The page shows the absolute `curbpack.json` path, the directory, the ids from the file, and present or missing against `<directory>/packs/`. It shows `requirements` and `exclude_requirements` as the file has them. Pack Editor and Check each have a field that saves the same `curbpack` value into that repo's file. That field is not an editor for the id lists. The page does not contain "Read it", "Start empty", or "Read it and tick the packs it names?", and it does not add an id that exists only as a workspace Pack. POST check calls `run_repository`. One Claim matches a selected Requirement and one does not. The result file is `<directory>/reports/run-<YYYYMMDDTHHMMSSZ>.json`, the page shows that path, the selected Claim is in the result, and the other is not. A second POST writes a second file and leaves the first byte-for-byte in place. The run does not raise. The same holds when `requirements` lists only the selected id, and when `exclude_requirements` names the other Requirement: that Claim is absent and the selected Claim is present. `tests/test_check_editor.py` is rewritten to this page in this task. `claims/ARCHITECTURE.md`, `review/ARCHITECTURE.md`, and `docs/arch/ARCHITECTURE.md` still describe `claims/`, `docs/reports/`, and `.curbpack/`. Those files stay for DOC-04. This task follows the story.
**Validation:** `python3 -m unittest tests.test_sys03_door tests.test_check_editor tests.test_m4_checks`
**Stop if:** honoring include/exclude or skipping an unselected Claim needs a new `curbpack.json` field.

- [ ] RED observed for the intended behavior.
- [ ] Minimal implementation and GREEN verified.
- [ ] Relevant regressions and review complete.
- [ ] Checkpoint saved and verified local commit created.

### Task 4 — Discover reads those Packs and writes those Claims

**Requirements:** SYS-R04, SYS-R07 for `/discover`.
**Files:** `app/server.py` `_discover_sections` (it currently loads `registered_sources.json` and a timestamped working copy), `claims/ui/http.py` (Claim save currently uses `context["repo"] / "claims"` and does not call `_claims_repo`), `tests/test_sys03_door.py`, `tests/test_discover_claims_ui.py`, `tests/test_discover_layout.py`.
**Test first:** POST `repo_id` on `/discover` writes `open-repo.json`. GET `/requirements` and GET `/check` then name that repository and that directory. GET `/discover` names that repository and that directory, shows a Claim already in `<directory>/claims/` as an existing Claim, and shows a candidate that is not that file as a candidate. The two are visibly distinct. Offering a Requirement uses the file beside `<directory>/packs/<pack-id>/pack.json`. It does not offer a Requirement that exists only in `registered_sources.json` or only in a timestamped working copy. Holding or editing a candidate writes no Claim file. The create-or-update process writes `<directory>/claims/<claim-id>.json` when no file exists, or updates that file when it does, and does not create `<workspace>/product/claims/` or `<repository>/claims/`. Saving a check, a vote, or a motivation does not write the catalog. With no open repo, GET `/discover` says none is chosen and does not read `product/claims`. `tests/test_discover_claims_ui.py` and `tests/test_discover_layout.py` move their Claim fixtures from `<repository>/claims/` to `<directory>/claims/` and their Requirement fixtures from the timestamped working copy to `<directory>/packs/<pack-id>/`. Setting `open-repo.json` alone is not enough. `tests/test_claims_binding_ui.py`, `tests/test_pilot_pack_selection.py`, and `tests/test_discover_browse.py` GET `/discover` with no open repository and still expect the catalog pack table or the add-repo browse controls. Retarget them to the open repository in this task. Keep the product-repo hunt for a copy the page names. Do not satisfy SYS-R04 by deleting that run. The stale layout sentences in `claims/ARCHITECTURE.md` stay for DOC-04.
**Validation:** `python3 -m unittest tests.test_sys03_door tests.test_discover_claims_ui tests.test_discover_layout`
**Stop if:** the Requirement list can be filled only from `registered_sources.json` or from a timestamped working copy the page did not name.

- [ ] RED observed for the intended behavior.
- [ ] Minimal implementation and GREEN verified.
- [ ] Relevant regressions and review complete.
- [ ] Checkpoint saved and verified local commit created.

### Task 5 — Review compiles that run

**Requirements:** SYS-R06, SYS-R07 for `/review`.
**Files:** `app/server.py` `preview_report`, report write, and `_review_view`, `tests/test_sys03_door.py`, `tests/test_ui_smoke.py`, `tests/test_review_report_kept.py`, `tests/test_review_replace_flow.py`.
**Test first:** POST `repo_id` on `/review` writes `open-repo.json`. GET `/review` names that repository and that directory. The directory has `reports/run-<stamp>.json`, `<directory>/packs/<pack-id>/pack.json`, and a Claim. `<workspace>/product/` has a different run and a different Claim. Compile reads that dated run and the directory's Claims. The report file is `<directory>/reports/review-<stamp>.json`. A second compile writes a second report file and leaves the first in place. It does not contain the workspace Claim and it is not written under `product/docs/reports/` or `product/.curbpack/`. With no open repo, GET `/review` says none is chosen and does not compile `product/`. `tests/test_ui_smoke.py`, `tests/test_review_report_kept.py`, and `tests/test_review_replace_flow.py` are updated in this task: register the product in `product_repos.json`, set `open-repo.json` to that id, put the Pack at `<directory>/packs/cra-baseline/`, put Claims in `<directory>/claims/`, expect the run at `<directory>/reports/run-<stamp>.json`, and expect the report at `<directory>/reports/review-<stamp>.json`. A later run or compile does not replace the earlier file. `prepare_demo` today writes `product/.curbpack/run-result.json` and `workspace/packs/cra-baseline`. Setting `open-repo.json` alone does not make those tests pass. `tests/test_review_discover_again.py` GETs `/review` with no `open-repo.json` and writes the report through `Workspace.report_path`. Retarget it to the open repository and `<directory>/reports/review-<stamp>.json`. Keep the assertions that the failed Claim stays visible and that Discover-again opens one Requirement. `tests/test_review_compile.py` calls `compile_report` directly and is not this task's evidence. The report path in `review/ARCHITECTURE.md` stays for DOC-04.
**Validation:** `python3 -m unittest tests.test_sys03_door tests.test_ui_smoke tests.test_review_report_kept tests.test_review_replace_flow`
**Stop if:** pointing the report at the directory requires a new `curbpack.json` field.

- [ ] RED observed for the intended behavior.
- [ ] Minimal implementation and GREEN verified.
- [ ] Relevant regressions and review complete.
- [ ] Checkpoint saved and verified local commit created.

### Task 6 — An extraction stays temporary; the Requirement view shows the Pack

**Requirements:** SYS-R08.
**Files:** `requirements/workspace.py` `extract_section`, the Requirement page that lists a Pack's Requirements, `app/server.py` extract POST and the accept action, `tests/test_sys03_door.py`, `tests/test_requirements_extract.py`. Do not edit `export_pack` or `selection.json`.
**Test first:** The door repo lists the pack. `<directory>/packs/<pack-id>/pack.json` and `<directory>/packs/<pack-id>/<requirement-id>.json` already exist. The Requirement view shows that existing Requirement and labels it as existing. POST extract writes the new extraction only in memory or in the timestamped working copy, and does not create or change a file under `<directory>/packs/<pack-id>/`. The page shows that extraction as distinct from the existing Requirement. The accept process then either updates `<requirement-id>.json` or writes a new Requirement file beside `pack.json`. Extract alone does not. `create_extraction_copy` still writes the timestamped copy PE-08 and PE-11 already read. `tests/test_requirements_compare.py` and the PE-11 export tests keep using that copy.
**Validation:** `python3 -m unittest tests.test_sys03_door tests.test_requirements_extract tests.test_requirements_compare`
**Stop if:** showing the existing Requirement or accepting an extraction needs a new field on `pack.json` or `curbpack.json`.

- [ ] RED observed for the intended behavior.
- [ ] Minimal implementation and GREEN verified.
- [ ] Relevant regressions and review complete.
- [ ] Checkpoint saved and verified local commit created.

## Work log

- **2026-10-28 / Task 0:** Replaced the blocked plan. That plan stored the packs root in workspace `pilot-door.json` and forbade a path in `curbpack.json`. The story now stores the directory in the `curbpack` key. `curbpack_directory` and the `curbcheck` defaults already follow that key. The four Studio pages do not. No product code in this revision.
- **2026-10-28 / Task 0 review:** First review of this revision found three issues. Task 4 now names `_discover_sections` and `claims/ui/http.py`, and the existing Discover tests move their fixtures to `<directory>/`. Task 5 now rewrites the three HTTP tests onto `<directory>/packs`, `<directory>/claims`, `<directory>/run-result.json`, and `<directory>/reports/review-report.json`, and GET `/review` names the repository. Task 6 writes the extracted Requirement beside `<directory>/packs/<pack-id>/pack.json` without removing the timestamped copy.
- **2026-10-28 / Task 0 re-review:** Approved the previous text. No blocking issues. Advisory test names were added to Tasks 2–5. That approval does not cover the three decisions below.
- **2026-10-28 / Task 0 decisions:** danielfl. Discover keeps candidates in memory, reads `<directory>/claims/`, and only the create-or-update process writes or updates a Claim file. Check writes a new `<directory>/reports/run-<UTC-stamp>.json` per run. Review writes `review-<UTC-stamp>.json` and does not replace an earlier file. An extraction stays in memory or on temp disk. The Requirement view shows Requirements already beside `pack.json` and distinguishes them from the extraction. The accept process writes or updates that file. No product code.
