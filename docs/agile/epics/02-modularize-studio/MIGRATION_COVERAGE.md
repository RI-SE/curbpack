# EP-02 — Migration coverage and verification

**MIG-00 baseline:** recorded 2026-11-06 against git `90ba3a0d6aa72c71f2a63c4ef1f27886fda6c485` (`agile: updated to more structured refactor`, 2026-11-06 14:33 +0100) on branch `daniel/post-pilot-fixes-1`.

The attached `curbpack-review.zip` (511 files) is byte-identical to those same paths in that revision. It omits 86 tracked files (reference fixtures, official Formex XML, and `app/icons/`). It also contains 37 untracked files under `daniel/`, including `daniel/split/inventory.md`. That note is **not** this inventory: it points at paths that do not exist (`studio/claim/studio/claim/claims/ui/pages.py`) and it proposes `app/pages/*.py`, which is not the EP-02 destination. Destinations below come from `docs/arch/ARCHITECTURE.md` and `CURBPACK_ARCHITECTURE.md`.

Labels used below:

- **Fact** — observed in this revision's source, or in the `make test` run recorded here.
- **Judgment** — an owner or extraction order inferred from the target architecture. Not a license to implement.
- **Open** — a gap or ambiguity. Not decided here.

Every row is **not started**, except that MIG-01 extracted the Home renderer, MIG-02 extracted the demo requirement renderer, MIG-03 extracted the Studio renderer, MIG-04 extracted the Check renderer, MIG-05 extracted the Claims editor renderer, MIG-06 extracted the Review renderer, MIG-07 extracted the Scaffold renderer, MIG-08 extracted the Pack sources view-model, and MIG-09 extracted the requirement editor GET model and save, and MIG-10 extracted the Pack export GET model and write, and each extract gate passed. `VERIFIED` still means a finished checkpoint for that operation, not a file move. None of those operations is VERIFIED as a completed migration. Scaffold, try-discovery, authentication, and compare/consolidate apply have decided owners under [Decided ownership](#decided-ownership). Those decisions do not start their implementation in the current extract.

## Required checkpoint record for each bounded change

Do not use a whole functional-area row as an implementation batch. For each **individual page, handler or backend operation**, add a record with:

| Field | Required information |
| --- | --- |
| Identifier | Old page/route/operation, HTTP method and visible user action |
| Baseline | Revision, source file/function, representative input and actual output, focused test and result |
| Extract | New Python file, old dispatcher/delegation preserved, same test result |
| Move | Owning component and new path, same test result |
| Separate | Backend `impl/` callable, direct test plus old HTTP/UI regression result |
| Boundary | Approved Pydantic model and compatibility test, when applicable |
| HTTP | Owning FastAPI router, direct request tests and remaining old callers |
| UI | TypeScript page, browser-to-REST test and old Python page retirement |
| Gate | Latest passing commands/results, known failures, local checkpoint commit, status OPEN or VERIFIED |

**Order:** baseline → extract Python page → test → move module → test → separate backend → test → Pydantic boundary → test → FastAPI/component router → test → TypeScript page → test → remove obsolete code → full regression. One bounded change at a time. A stage may be recorded as N/A only with an explanation.

**No mass `git mv`, import-only success, test skipping or blanket parity claims.** The old `ThreadingHTTPServer` and Python rendering remain the working integration path until their specific replacements pass. Preserve existing behavior and files; any new EP-11 feature is separate work.

## Baseline command

**Fact.** Command: `make test` (runs `scripts/ci/checks/tests.py`, `unittest` discovery of `tests/test*.py`). Result: **416 PASS, 0 FAIL**. No skip lines were printed. Elapsed about 86 seconds. Exit code 0. This run did not execute `make cicd`, `make package`, `make package-studio`, `make package-curbcheck`, or the modules under `tests/cs/`.

`tests/cs/path_boundary.py`, `tests/cs/review_signature.py`, `tests/cs/check_result_integrity.py`, `tests/cs/git_provenance.py`, and `tests/cs/workspace_selector.py` define `unittest.TestCase` classes. Their filenames do not match `test*.py`. No other module imports them. They are **not** part of the 416.

## Where behavior lives today

**Fact.** One HTTP server: `http.server.ThreadingHTTPServer` in `app/server.py` (`make_handler`, `serve`, `main`). `python -m app` calls that `main`. There is no FastAPI application, no `studio/` package, and no `models/pydantic/` package.

| Concern | Where it is now | What it does not do |
| --- | --- | --- |
| HTTP dispatch, redirects, open-project gate, most form orchestration | `app/server.py` `Handler._get` / `Handler._post` and the `_…_model` / `_apply_…` helpers | Not a thin adapter. Several branches validate and choose files before calling a domain function. |
| Discover-claim and feedback HTTP | `claims/ui/http.py` `handle_get` / `handle_post`, called before the other GET/POST branches | `claims/ui/researcher.py` and `claims/ui/pages.py` do not write files. `http.py` does (`write_claim`, `save_vote`, `save_check`, `add_finding`). `_check_from_form` maps picker fields onto Check args. |
| Shared HTML chrome | `app/pages.py` `page`, `_flash`, `_reading`, `progress_dialog`, `repo_config_panel` | No file writes. `page()` also emits the shared CSS. |
| Scaffold HTML | `app/scaffold_page.py` `scaffold_page` | No file writes. Calls `page` and `_flash` in `app/pages.py`. GET and POST `/scaffold` stay in `app/server.py`. POST calls `write_stub` in `scaffold/stub.py`, which is unmoved. |
| Pack sources view-model | `app/documents_model.py` `_documents_model` | Does not write pack files, claim files, or `curbpack.json`. When the query names a repo id that is already registered, `_sync_open_repo` still writes `open-repo.json`. An unknown id raises `ModelError` and does not write. GET `/requirements` without `document` stays in `app/server.py` and calls this, then `documents_page`. `?document=` and the Pack POST routes stay in `app/server.py`. |
| Requirement editor | `app/requirement_editor.py` `_editor_model`, `_save_requirement_form` | GET does not write files. POST writes the working requirement through `save_working_requirement`. It does not sign. GET and POST `/requirements/requirement/{id}` stay in `app/server.py`. Sign and try-discovery stay there. |
| Pack export | `app/pack_export.py` `_export_model`, `_export_selected` | Both GET and POST call `_export_document`, which calls `ensure_catalog`. That writes `registered_sources.json` only when the file is missing. POST also writes `destination/<pack-id>/` through `export_pack`, or redirects on a conflict and leaves the existing directory. It does not publish a release. The URL stays in `app/server.py`. |
| Review HTML | `app/review_page.py` `review_page` | No file writes. Calls `page`, `_flash`, `_reading`, and `repo_config_panel` in `app/pages.py`. The private review helpers moved with it. GET `/review`, `_review_view`, and `_door_chrome` stay in `app/server.py`. |
| Claims editor HTML | `app/claims_page.py` `claims_page` | No file writes. Calls `page`, `_flash`, and `repo_config_panel` in `app/pages.py`. `_claim_context`, `_claim_seal_html`, and `_passages_html` are in this module. GET `/claims` and the claim POST routes stay in `app/server.py`. |
| Home HTML | `app/cover.py` `cover` | No file writes. Calls `page` and `_flash` in `app/pages.py`. GET `/` and `_home_model` stay in `app/server.py`. |
| Demo requirement HTML | `app/requirement_page.py` `requirement_page` | No file writes. Calls `page`, `_flash`, and `_reading` in `app/pages.py`. GET `/requirement`, `load_requirement`, `snapshot`, and `_require_demo_requirement` stay in `app/server.py`. |
| Studio config HTML | `app/studio_page.py` `studio_page` | No file writes. Calls `page`, `_flash`, and `_current_project_label` in `app/pages.py`. `_review_path_chrome` is in this module. GET and POST `/studio`, `_studio_model`, `_studio_message`, and `save_studio_config` stay in `app/server.py`. |
| Check HTML | `app/check_page.py` `check_page` | No file writes. Calls `page`, `_flash`, and `repo_config_panel` in `app/pages.py`. `_curbpack_editor` is in this module. GET and POST `/check`, `_check_editor_model`, `_check_report`, and `_check_message` stay in `app/server.py`. |
| Project page | `app/project_selector.py` `project_page`, `handle_project_post` | Selection writes repo registration through `discovery` helpers. |
| Pack-editor HTML | `requirements/ui/pages.py`, `requirements/ui/try_discovery.py` | No file writes. |
| Discover list HTML | `claims/ui/pages.py` `discover_page` | No file writes. |
| Review presentation data | `review/present.py`, called from `app/server.py` `_raw_presentation` and `_report_presentation` | `review/view_html.py` `render_review_board` has **no importer**. The live Review HTML is `app/review_page.py` `review_page`. |
| Pack / Requirement rules and files | `requirements/workspace.py`, `requirements/editing.py`, `requirements/catalog.py`, `requirements/compare.py`, `requirements/consolidate.py`, `requirements/jobs.py`, `requirements/extract/` | |
| Claim rules and files | `claims/bind.py`, `claims/ui/coverage.py` (read-only coverage) | |
| Discovery search, jobs, repos, feedback | `discovery/` | |
| Check execution and run-result files | `checks/run.py`, `checks/dispatch.py`, `checks/schema.py`, `checks/filecheck.py`, `checks/gitcheck.py`, `checks/nodecheck.py`, `checks/commands.py` | There is no `curbcheck/api.py`. Studio calls `checks.run.run_and_write`. |
| Report assembly, decision, report signature | `review/compile.py` (all three) | Target splits assembly from decision/signature. |
| PDF | `compile/pdf.py`, entered by `compile/cli.py` and `compile-pdf.py` | No HTTP route calls `compile_pdf`. |
| JSON read/write | `common/jsonio.py`, `common/store.py` | |
| Config and claim shape checks | `common/validate.py`, `checks/schema.py`, `requirements/extract/assemble.py`, `review/compile.py` `validate_report` | Not Pydantic. |
| Keys and signatures | `common/keystore.py`, `common/signing.py`, `review/gitseal.py` | |
| Path confinement for review/check files | `app/server.py` `_confined_review_report_path`, `_confined_run_result_path`, `_requested_dated` | |
| Open-project gate | `app/server.py` `_requires_open_project` | Not authentication. No login, session, or OIDC handler exists. |

## Pages

Each row is a function that returns HTML bytes for a GET. Owner is a **judgment** from the target architecture unless marked Open. Verification describes assertions inspected in this revision, not a coverage percentage.

| Page | GET | Renderer | Called from | Target owner | Verification |
| --- | --- | --- | --- | --- | --- |
| Home / cover | `/` | `app/cover.py` `cover` | `Handler._get` still builds `_home_model`, then calls `cover` | Shell. Not a Pack operation. Extract only; not moved into `studio/`. | Extract gate passed. Same assertions as the baseline: `test_ui_smoke.py` asserts Pack Editor, Discover, and the absence of `/claims` and `/scaffold` links. `test_cover_navigation.py` and `test_pilot_pack_selection.py` assert nav links. Without an open project, `_requires_open_project` in `app/server.py` still redirects `/` to `/project`; `test_cover_navigation.py` follows that and asserts "Registered projects". |
| Project | `/project` | `app/project_selector.py` `project_page` | `Handler._get` | Shell / workspace selection. `studio/app.py` must not grow this logic; the epic's shell row is the destination, not `studio/pack/`. | Asserted. `test_project_page.py` posts `action=select` and asserts the open repo id and "Pack Editor". `test_discover_browse.py` asserts "Add project" on GET `/project`. |
| Pack sources | `/requirements` without `document` | `requirements/ui/pages.py` `documents_page` | `Handler._get` calls `app.documents_model._documents_model`, then `documents_page`. `?document=` still uses `_catalog_model` in `app/server.py`. | `studio/pack/`. Extract only; not moved into `studio/`. | Extract gate passed. `test_cover_navigation.py` `test_opening_an_existing_catalog_shows_the_pack_and_does_not_change_it` asserts `<h1>Pack Sources</h1>` and `House Rules`. `test_requirements_export.py` `test_pack_sources_row_submits_export_for_that_document` asserts `action="/requirements/export"`. `test_sys03_door.py` `test_start_empty_then_save_lists_bundled_adapters` asserts `cra-xml` is absent before save. Without an open project, `_requires_open_project` still redirects `/requirements` to `/project`. |
| Pack sections | `/requirements?document=` | `requirements/ui/pages.py` `catalog_page` | `_catalog_model` | `studio/pack/` | Asserted. `test_requirements_ui.py` `test_catalog_edit_sign_publish_and_extract` asserts `action="/requirements/extract"` on the sections page. `test_cover_navigation.py` asserts the extract dialog keeps the pack link. |
| Source inspect | `/requirements/inspect` | `requirements/ui/pages.py` `source_page` | `_inspect_model` | `studio/pack/` | **None** for this URL. No test contains `/requirements/inspect`. Adapter behavior is asserted in `test_requirements_extract.py` and `test_xml_adapters.py` against `requirements.extract`, not this page. |
| Extract review | `/requirements/extract/review` | `requirements/ui/pages.py` `extract_review_page` | `_extract_review_model` | `studio/pack/` | Asserted. `test_requirements_compare.py` `test_page_leaves_unchecked_fields_and_updates_the_chosen_one` asserts "Use the new definition", the unchecked note checkbox, and after POST that `note` changed while `remediation_hint` did not. |
| Copy / working copies | `/requirements/copy` | `requirements/ui/pages.py` `copy_page` | `_copy_model` | `studio/pack/` | Asserted. `test_pilot_pack_selection.py` GETs this page after POST `/select-pack` and asserts the timestamp `2026-10-13T090000Z` and `REQ-A`. `test_requirements_ui.py` also asserts whether `action="/requirements/copy"` is present. |
| Export | `/requirements/export` | `requirements/ui/pages.py` `export_page` | `Handler._get` calls `app.pack_export._export_model`, then `export_page`. POST calls `_export_selected` there. | `studio/pack/`. Extract only; not moved into `studio/`. | Extract gate passed. `test_requirements_export.py` `test_export_page_names_the_selected_copy_and_unsigned_readings` and the POST tests assert destination bytes, refusal, and overwrite. |
| Publish (legacy) | `/requirements/publish` | `requirements/ui/pages.py` `publication_page` | `_publication_model` | `studio/pack/` for the existing flow. Do not add a new Publish service. | Asserted. `test_requirements_ui.py` GETs the page and POSTs version `0.1.0`, including a refusal before seal. `test_requirements_publish.py` asserts `publish_pack` directly (unsigned refused, tampered seal refused, repeat refused). |
| Compare | `/requirements/compare` | `requirements/ui/pages.py` `compare_page` | `_compare_model` | `studio/pack/` | Smoke only for the URL. `test_cover_navigation.py` asserts `<h1>` and no traceback on GET when no project is open. Diff behavior is asserted on `compare_copies` / `apply_transfer` in `test_requirements_compare.py`, not on POST `/requirements/compare/apply`. |
| Consolidate | `/requirements/consolidate` | `requirements/ui/pages.py` `consolidate_page` | `_consolidate_model` | `studio/pack/` | Smoke only for the URL (`test_cover_navigation.py`, same `<h1>` / no traceback check). Merge behavior is asserted on `suggest_consolidations` / `apply_consolidation` in `test_requirements_consolidate.py`. |
| Requirement editor | `/requirements/requirement/{id}` | `requirements/ui/pages.py` `editor_page` | `Handler._get` calls `app.requirement_editor._editor_model`, then `editor_page`. POST save calls `_save_requirement_form` there and still redirects with `saved=1`. Sign and try-discovery stay in `app/server.py`. | `studio/pack/`. Extract only; not moved into `studio/`. | Extract gate passed. `test_requirements_ui.py` drives edit, sign, and publish through this page. `test_requirement_field_errors.py` asserts a missing edition redirects to this editor and marks the field. |
| Try-discovery file | `/requirements/requirement/{id}/try-discovery/file` | `requirements/ui/try_discovery.py` `file_page` | `_try_discovery_file_model` | `studio/claim/` Discovery. The requirement editor only calls it. See Decided ownership. Not moved yet. | Asserted. `test_try_discovery_ui.py` asserts the back link, `<mark>`, and `risk assessment` on this GET. |
| Demo requirement | `/requirement` | `app/requirement_page.py` `requirement_page` | `Handler._get` still calls `load_requirement` of `packs/cra-baseline/CRA-ANNEX-VII-RISK.json` and `snapshot`, then `requirement_page` | `studio/pack/` as preserved demo behavior, not a second editor design. Extract only; not moved into `studio/`. | Extract gate passed. Same assertions as the baseline: `test_ui_smoke.py` asserts "cybersecurity risks" and `CRA-ANNEX-VII-RISK`. Without an open project, `_requires_open_project` in `app/server.py` still redirects `/requirement` to `/project`; `test_cover_navigation.py` follows that and asserts "Registered projects". |
| Discover packs | `/discover` and `/discover/repo` | `claims/ui/pages.py` `discover_page` | `_discover_model` (`product=True` for `/discover/repo`) | `studio/claim/` | Asserted. `test_ui_smoke.py` asserts the Pack and Claims columns and the absence of "Add repo" on `/discover`. `test_discover_layout.py` GETs `/discover/repo` and asserts the product view hides choices. |
| Discover claims overview | `/discover/claims` | `claims/ui/researcher.py` `overview_page` | `claims/ui/http.py` `handle_get` | `studio/claim/` | Asserted. `test_discover_claims_ui.py` and `test_claims_binding_ui.py` assert overview links. `test_rev03_review.py` asserts `return_to` survives onto this URL. |
| Discover one requirement | `/discover/claims/{id}` | `claims/ui/researcher.py` `requirement_page` | `handle_get` | `studio/claim/` | Asserted. `test_discover_claims_ui.py` asserts "law passage" on this GET and asserts HTTP errors for an unknown requirement and a bad timestamp. |
| Discover source file | `/discover/claims/{id}/file` | `claims/ui/researcher.py` `file_page` | `handle_get` | `studio/claim/` | Asserted inside `test_discover_claims_ui.py` `test_researcher_workflow_from_discover_to_claim` (file view of a candidate). The same test asserts the requirement page; the file GET is part of that method. |
| Claims editor | `/claims` | `app/claims_page.py` `claims_page` | `Handler._get` still builds the saved/cleared/signed/retired message and `_claims_model`, then calls `claims_page` | `studio/claim/`. Extract only; not moved into `studio/`. | Extract gate passed. Same assertions as the baseline: `test_claims_binding_ui.py` GETs `/claims` and asserts created claims, rejection of an unknown requirement, sign, and reopen. `test_cover_navigation.py` GETs `/claims` with no open project and still gets a heading. Cover tests assert the nav link is absent. |
| Scaffold | `/scaffold` | `app/scaffold_page.py` `scaffold_page` | `Handler._get` calls `scaffold_page()` with no arguments. POST still calls `write_stub` and redirects to `/scaffold?wrote=1`. The query is not read. | Its own Studio component and page, created as late as possible. See Decided ownership. Current stub behavior stays. Not created in this extract. | Extract gate passed. `test_ui_smoke.py` `test_open_project_scaffold_page_shows_the_stub_form` GETs `/scaffold` with an open project and asserts `<h1>Scaffold</h1>`, `action="/scaffold"`, and "The stub is not approved evidence." `test_cover_navigation.py` asserts `<h1>` and "Registered projects" on GET `/scaffold` with no open project. The same smoke file POSTs `/scaffold` and does not assert the stub file. |
| Check | `/check` | `app/check_page.py` `check_page` | `Handler._get` still builds `_check_editor_model` and `_check_report`, then calls `check_page`. `_check_message` stays in `app/server.py`. | `studio/check/` UI, calling future `curbcheck/api.py`. The engine stays in Curbcheck. Extract only; not moved into `studio/`. | Extract gate passed. Same assertions as the baseline: `test_ui_smoke.py` asserts `claim-risk` and `fail` after POST. `test_check_editor.py` and `test_sys03_door.py` assert named packs, directory fields, and dated run-result files. Without an open project, `_requires_open_project` in `app/server.py` still redirects `/check` to `/project`; `test_cover_navigation.py` follows that and asserts "Registered projects". |
| Review | `/review` | `app/review_page.py` `review_page` | `Handler._get` still calls `_review_view` and `_door_chrome`, then `review_page`. On a missing `curbpack.json` it still renders the same function with `error`. | `studio/review/`. Extract only; not moved into `studio/`. | Extract gate passed. Same assertions as the baseline: `test_ui_smoke.py` asserts "not saved" and "Compile writes the report" before compile, and asserts POST `/review` is HTTP 400 until a report file exists. `test_rev03_review.py` asserts grouping, seals, path dialogs, and decisions. `test_review_compile.py` calls `review_page` directly. Without an open project, `_requires_open_project` still redirects `/review` to `/project`; `test_cover_navigation.py` follows that and asserts "Registered projects". |
| Studio settings | `/studio` | `app/studio_page.py` `studio_page` | `Handler._get` still builds `_studio_model` and `_studio_message`, then calls `studio_page` | Shell configuration, not Check and not Review. Extract only; not moved into `studio/`. | Extract gate passed. Same assertions as the baseline: `test_sys03_door.py` `test_studio_page_creates_and_edits_curbpack_studio_json` asserts create, cancel, and edit of `curbpack-studio.json`. Without an open project, `_requires_open_project` in `app/server.py` still redirects `/studio` to `/project`; `test_cover_navigation.py` follows that and asserts "Registered projects". |
| Error / not found | any other GET | `app/pages.py` `page` | `Handler._fail` and the final `else` of `_get` | Shell | Partial. Unknown discover-claim ids raise and become HTTP errors in `test_discover_claims_ui.py`. No test was found that asserts the literal "Unknown page." body. |
| Job dialogs (fragments, not top-level pages) | polled from extract, discover, and try-discovery pages | `requirements/ui/pages.py` `job_fragment`, `progress_dialog` in `app/pages.py` | pages embed `data-poll` | Same owner as the page that embeds them | The fragment URLs are covered with the job handlers below. |

Shared HTML helpers that later page extractions must keep importable from `app.pages`: `page`, `_flash`, `_reading`, `_current_project_label`, `progress_dialog`, and `repo_config_panel`. **Fact.** `app/cover.py` imports `page` and `_flash`. `app/requirement_page.py` imports `page`, `_flash`, and `_reading`. `app/studio_page.py` imports `page`, `_flash`, and `_current_project_label`. `app/check_page.py` imports `page`, `_flash`, and `repo_config_panel`. `app/claims_page.py` imports `page`, `_flash`, and `repo_config_panel`. `app/review_page.py` imports `page`, `_flash`, `_reading`, and `repo_config_panel`. `app/scaffold_page.py` imports `page` and `_flash`. `requirements/ui/pages.py`, `claims/ui/pages.py`, `claims/ui/researcher.py`, and `requirements/ui/try_discovery.py` import `page` and, for some of them, `progress_dialog` or `repo_config_panel`. `tests/test_review_compile.py` imports `review_page` from `app.review_page`.

## HTTP handlers

Dispatcher: `app/server.py` `Handler.do_GET` / `do_POST`. Discover-claim and feedback paths return from `claims/ui/http.py` before the generic branches. Methods are the methods that branch handles. A path that is not listed falls through to "Unknown page." (GET) or `ModelError` "a known action" (POST).

Verification words: **Asserted** means a test issues that request and a later assertion checks the body, status, or a file that request writes. **Domain** means the underlying function is asserted and this URL is not. **Smoke** means the assertion is only a heading or the absence of a traceback. **None** means no such assertion was found.

| Method and path | Handler behavior (fact) | Domain functions used | Target owner (judgment) | Tests whose assertions were inspected |
| --- | --- | --- | --- | --- |
| GET `/vendor/jsondiffpatch.js`, `/vendor/jsondiffpatch.css`, `/icons/curbpack-icon.svg` | `_send_vendor` reads the mapped file | none | `studio/pack/` pages for the diff assets; the icon is shell chrome | **Partial.** `test_requirements_compare.py` asserts the JS path is in the extract-review page, GET returns 200, and the body contains `jsondiffpatch`. **None** for the CSS or the SVG. The SVG file is tracked but omitted from the ZIP. |
| GET `/requirements/jobs/{id}` | `_send_job` → JSON `read_job` | `requirements/jobs.py` `read_job` | `studio/pack/` | **Asserted.** `test_requirements_ui.py` `_wait_job` GETs this URL and `test_catalog_edit_sign_publish_and_extract` asserts `failed["status"] == "failed"`. |
| POST `/requirements/jobs/{id}/abort` | `request_abort`, redirect back to `/requirements` | `requirements/jobs.py` `request_abort` | `studio/pack/` | **Domain only.** `test_requirements_jobs.py` calls `request_abort` and asserts status `aborted` and that the older copy is unchanged. No test contains this URL. |
| GET `/discover/jobs/{id}` | `_send_discover_job` | `discovery/jobs.py` `read_job` | `studio/claim/` | **Asserted.** `test_sys03_door.py` asserts `job["status"] == "done"` after GET. `test_discover_claims_ui.py` polls the same URL. |
| POST `/discover/jobs/{id}/abort` | `abort_discover_job`, redirect to `/discover?job=` | `discovery/jobs.py` `request_abort` | `studio/claim/` | **Domain only.** `test_discover_repos.py` calls `request_abort` and asserts the next requirement is not scored. No test contains this URL. |
| GET `/requirements/try-discovery/jobs/{id}` | `_send_try_job` | `discovery/try_run.py` `read_try_job` | `studio/claim/` Discovery. See Decided ownership. Not moved yet. | **Asserted.** `test_try_discovery_ui.py` asserts `status == "done"`. |
| GET `/discover/browse` | JSON `list_directories` | `discovery/browse.py` | `studio/claim/` | **Asserted.** `test_discover_browse.py` asserts `payload["path"]` and the child directory name. `test_lists_child_dirs_and_parent` asserts `list_directories` directly. |
| GET `/project` | `project_page` | `project_selector.project_model` | Shell | **Asserted.** See the Project page row. |
| POST `/project` | `handle_project_post`, redirect. `ModelError` re-renders the page with the error. | `app/project_selector.py` | Shell | **Asserted.** `test_project_page.py` asserts the selected repo id after `action=select`. |
| GET `/` | `app/cover.py` `cover` | `_home_model` in `app/server.py` | Shell | **Asserted.** Handler unchanged. See MIG-01 and the Home row. |
| POST `/prepare` | `prepare_demo`, redirect `/?prepared=1` | `demo_setup.py` | Shell demo fixture. Not a Pack lifecycle operation. | **None** for this URL. `test_ui_smoke.py` calls `prepare_demo` directly, then uses the resulting files. |
| POST `/select-pack` | `_apply_pack_selection`, redirect `/?selected=1` | `requirements/workspace.py` selection helpers | `studio/pack/` | **Asserted.** `test_pilot_pack_selection.py` asserts Home does not contain `/select-pack`, then POSTs a working copy and asserts GET `/requirements/copy` contains that timestamp and `REQ-A`. A second POST of the published ref asserts `curbpack.json` bytes are unchanged. |
| GET `/requirements` | Without `document`, `Handler._get` calls `app.documents_model._documents_model`, then `documents_page`. With `document`, it still calls `_catalog_model` in `app/server.py`. | catalog, workspace, door. The view-model still calls `_sync_open_repo`, `_registered_repo_path`, `_adapter_for_url`, `_catalog_job`, and `_catalog_message` in `app/server.py`. | `studio/pack/`. Extract only; not moved into `studio/`. | **Asserted.** See the Pack sources and Pack sections rows. |
| POST `/requirements/source` | `mark_source_adapter`, redirect to inspect | `requirements/workspace.py` `mark_source_adapter`, `requirements/extract/adapter.py` `load_adapter` | `studio/pack/` | **None** for this URL. |
| POST `/requirements/start-empty` | `_start_empty_folder`, redirect to `/requirements?repo=` | `discovery` repo registration | `studio/pack/` together with shell repo registration | **None** for this URL. The similarly named `test_start_empty_then_save_lists_bundled_adapters` POSTs `/requirements/curbpack`, not this path. |
| POST `/requirements/curbpack` | `set_open_repo`; optional `_save_curbpack_form` | `discovery/door.py`, `common/validate.py` | Shell for the open repo; path fields are workspace config (`docs/reference/workspace.md`), not a new schema | **Asserted.** `test_sys03_door.py` asserts `cra-xml` appears after save and that saving one path field leaves the other file unchanged. |
| POST `/requirements/documents` | add or update pack metadata on the repo | `_add_pack_to_repo`, `_update_pack_info` | `studio/pack/` | **Asserted.** `test_requirements_catalog.py` `test_add_via_http` and `test_sys03_door.py` post this path. `test_requirements_ui.py` asserts the saved pack URL/name. |
| POST `/requirements/catalog` | add a section to the workspace catalog or to a repo pack | `requirements/catalog.py` `add_section` or `_add_pack_section` | `studio/pack/` | **Asserted.** `test_requirements_catalog.py` `test_add_via_http` POSTs section `V` on `cra-annex-v` and asserts HTTP 400 with body containing "can be extracted". The same test asserts POST `/requirements/documents` writes `pack.json` and does not put that id in `registered_sources.json`. |
| POST `/requirements/select` | `mark_selected` for a dated copy; redirect to copy, publish, or sources | `requirements/workspace.py` | `studio/pack/` | **Asserted.** `test_requirements_ui.py` posts `/requirements/select` as part of the edit/sign/publish flow. |
| POST `/requirements/extract` | Server checks the section is ready and in scope, then `start_extract_job` | `requirements/jobs.py`, adapter JSON | `studio/pack/` | **Asserted.** `test_requirements_ui.py` starts extract through this POST and asserts job failure leaves the published copy unchanged. Ready-section refusal is inline in the handler; a dedicated assertion for the "not ready" `ModelError` on this POST was not found. |
| POST `/requirements/requirement/{id}` | `app.requirement_editor._save_requirement_form`, then redirect with `saved=1`. The redirect stays in `app/server.py`. | `requirements/editing.py` `apply_edits`, `save_working_requirement` | `studio/pack/`. Extract only; not moved into `studio/`. | **Asserted.** `test_requirements_ui.py` and `test_requirement_field_errors.py`. Direct edit/reload is also `test_m1_requirement.py` and `test_requirements_publish.py` (`apply_edits`, stale save does not write). |
| POST `/requirements/requirement/{id}/sign` | `_sign_requirement` | `requirements/editing.py`, `common/keystore.py` | `studio/pack/` | **Asserted** as part of `test_requirements_ui.py` (sign then publish). Direct seal invalidation is `test_m1_requirement.py` and `test_requirements_publish.py`. |
| POST `/requirements/requirement/{id}/try-discovery` | `_run_try_discovery` → `start_try_job` | `discovery/try_run.py` | `studio/claim/` Discovery. The editor only calls it. See Decided ownership. Not moved yet. | **Asserted.** `test_try_discovery_ui.py` asserts the progress dialog and a done job. |
| POST `/requirements/seal` | `_seal_selected`, redirect to publish | `requirements/editing.py` `seal_pack_directory` | `studio/pack/` | **Asserted.** `test_requirements_ui.py` posts the seal, then publish. `test_m1_requirement.py` asserts a directory seal breaks when a file changes. |
| POST `/requirements/consolidate/apply` | `_apply_consolidation_form` | `requirements/consolidate.py` `apply_consolidation` | `studio/pack/` | **Domain only.** `test_requirements_consolidate.py` asserts merge deletes the unsigned sibling and that conflict, signed, and stale digest do not delete. The URL is absent from tests. |
| POST `/requirements/extract/review` | `_apply_extraction_review` | `requirements/compare.py` `apply_extraction_choices` | `studio/pack/` | **Asserted.** See the extract-review page row. |
| POST `/requirements/compare/apply` | `_apply_compare_form` | `requirements/compare.py` `apply_transfer` | `studio/pack/` | **Domain only.** `test_requirements_compare.py` asserts one-field transfer, stale digest writes nothing, and a published directory is not a destination. The URL is absent from tests. |
| GET `/requirements/export` | `app.pack_export._export_model`, then `export_page`. The URL stays in `app/server.py`. | `requirements/catalog.py` `ensure_catalog`, `requirements/workspace.py` `selected_copy` | `studio/pack/`. Extract only; not moved into `studio/`. | **Asserted.** See the Export page row. |
| POST `/requirements/export` | `app.pack_export._export_selected` writes the directory or redirects on conflict. The URL stays in `app/server.py`. | `requirements/workspace.py` `export_pack` | `studio/pack/`. Extract only; not moved into `studio/`. | **Asserted.** `test_requirements_export.py` asserts loadable output, no diagnostics in the export, overwrite, and failed overwrite restoring the previous directory. |
| GET/POST `/requirements/publish` | publication page; POST `_publish_selected` | `requirements/workspace.py` `publish_pack` | `studio/pack/` existing behavior only | **Asserted.** See Publish page. |
| GET `/discover`, GET `/discover/repo` | `discover_page` | `_discover_model` | `studio/claim/` | **Asserted.** See Discover packs. |
| POST `/discover/repos` | `add_repo`, `save_repos`, optional `next` redirect | `discovery/repos.py` | `studio/claim/` | **Asserted.** `test_discover_claims_ui.py` posts it before the researcher flow. `test_discover_repos.py` asserts duplicate and non-directory rejection on `add_repo` directly. |
| POST `/discover/run` | `_start_discover` | `discovery/jobs.py` `start_discover_job` | `studio/claim/` | **Asserted.** `test_sys03_door.py` asserts the poll URL and `status == "done"`. `test_discover_claims_ui.py` asserts `action="/discover/run"` and runs a job. |
| GET `/discover/claims`, `/discover/claims/{id}`, `/discover/claims/{id}/file` | `handle_get` | `discovery/present.py`, `discovery/search.py` `read_source_text`, `claims/bind.py` `read_claims` | `studio/claim/` | **Asserted.** See the three discover-claim page rows. |
| POST `/discover/feedback/vote` | `save_vote` | `discovery/feedback.py` | `studio/claim/` | **Asserted** in `test_discover_claims_ui.py` and `test_rev03_review.py` (return-to and take/keep). Direct round-trip: `test_discover_feedback.py` asserts a bad probe does not write. |
| POST `/discover/feedback/checks` | maps the form to a Check, then `save_check` and/or `rebind` | `claims/ui/http.py` `_check_from_form`, `discovery/feedback.py`, `claims/bind.py` | `studio/claim/` | **Asserted.** `test_discover_claims_ui.py` `test_researcher_workflow_from_discover_to_claim` posts this path and later asserts exactly one claim JSON under the product claims directory. `test_claims_binding_ui.py` asserts the path binds the requirement the user picked when two ids exist. |
| POST `/discover/feedback/add` | `add_finding` | `discovery/feedback.py` | `studio/claim/` | **Asserted** in `test_discover_claims_ui.py` and `test_review_replace_flow.py`. `test_discover_feedback.py` asserts a finding needs a file and a rationale. |
| POST `/discover/feedback/motivation` | keep dismisses; take copies the sentence onto the Claim | `dismiss_why`, `rebind`, `write_claim` | `studio/claim/` | **Asserted.** `test_discover_claims_ui.py` `test_clicking_keeps_the_claim_or_copies_the_sentence`. |
| POST `/discover/claims/create` | `create_configured_claims` when the finding has checks and a description; otherwise re-renders the page with a notice | `claims/bind.py` | `studio/claim/` | **None** for this URL. No test contains `/discover/claims/create`. `test_create_configured_claims.py` asserts the function: one claim for two checks, a repeat is unchanged, a signed claim is not overwritten, an invalid check blocks the write. |
| GET `/requirement` | `app/requirement_page.py` `requirement_page` | `common/store.py` `load_requirement`, `workflow.py` `snapshot`, both still called from `app/server.py` | `studio/pack/` demo. Extract only; not moved into `studio/`. | **Asserted.** Handler unchanged. See MIG-02 and the Demo requirement row. |
| POST `/requirement` | `edits_for_requirement` + `apply_edits` + `save_requirement` on the demo file | `requirements/editing.py` | `studio/pack/` demo | **None** found for this URL. Demo edit/save is not the pack-editor POST. |
| POST `/publish` | `publish_requirement` on the demo file, `published=True` | `requirements/editing.py`, keystore | `studio/pack/` demo. Not a new Publish product. | **None** for this URL. |
| POST `/seal-pack` | `seal_pack_directory` on `packs/cra-baseline` | `requirements/editing.py` | `studio/pack/` demo | **None** for this URL. |
| GET `/claims` | `app/claims_page.py` `claims_page` | `claims/bind.py` `read_claims`, still called from `app/server.py` | `studio/claim/`. Extract only; not moved into `studio/`. | **Asserted.** Handler unchanged. See MIG-05 and the Claims editor row. |
| POST `/claims` | parse JSON args/checks, `build_claim`, refuse an existing id, `write_claim` | `claims/bind.py` | `studio/claim/` | **Asserted.** `test_claims_binding_ui.py` asserts two claims and rejects an unknown requirement id. `test_ui_smoke.py` posts a claim and later asserts the check failure names it. `test_m3_claims.py` asserts rebind leaves the requirement and an unknown check is rejected, without HTTP. |
| POST `/claims/{id}` | `rebind_from_fields`, clear seal when the signed payload changes | `claims/bind.py` | `studio/claim/` | **Asserted.** `test_claims_binding_ui.py` `test_sign_edit_reopen_and_direct_create` asserts the cleared seal. |
| POST `/claims/{id}/retire` | `retire_claim` | `claims/bind.py` | `studio/claim/` | **Asserted.** `test_review_replace_flow.py` posts `/claims/claim-old/retire` and asserts the file is gone. `test_m3_claims.py` and `test_review_coverage.py` also assert `retire_claim` directly. |
| POST `/claims/{id}/sign` | `sign_claim` | `claims/bind.py`, keystore | `studio/claim/` | **Asserted** in `test_claims_binding_ui.py` (signed page). `test_claim_workflow.py` asserts a signature survives a check run, without this URL. |
| GET/POST `/scaffold` | GET calls `app/scaffold_page.py` `scaffold_page()`; POST calls `write_stub` | `scaffold/stub.py`, still called from `app/server.py` | Own Studio component, as late as possible. See Decided ownership. Current routes stay. | **Asserted** for the GET body. `test_ui_smoke.py` `test_open_project_scaffold_page_shows_the_stub_form` asserts the heading, form action, and the not-approved-evidence sentence. POST in that file still does not assert the stub file. `test_e2e_annex_vii.py` calls `write_stub` / `is_stub` directly. `test_cover_navigation.py` asserts the closed-project redirect. |
| GET `/check` | `app/check_page.py` `check_page` of the selected run | `checks/run.py` readers, `checks/defaults.py`, still called from `app/server.py` | `studio/check/`. Extract only; not moved into `studio/`. | **Asserted.** Handler unchanged. `test_check_editor.py`, `test_chk08_studio.py`, `test_sys03_door.py`. See MIG-04 and the Check page row. |
| POST `/check` | `set_open_repo`; `action=check` validates `curbpack.json` and `run_and_write`. This handler stays in `app/server.py`. | `checks/run.py` `run_and_write` | `studio/check/` adapter. Engine: future `curbcheck/`. | **Asserted.** Handler unchanged. `test_ui_smoke.py` asserts `fail`. `test_sys03_door.py` `test_check_runs_the_open_repository_and_keeps_dated_results` asserts a second run keeps the first file. `test_chk07_curbcheck.py` asserts the CLI writes the same kind of dated file and that stdout-only writes nothing. |
| GET `/review` | `app/review_page.py` `review_page` | `review/present.py`, `review/compile.py` loaders, `review/gitseal.py`, still called from `app/server.py` | `studio/review/`. Extract only; not moved into `studio/`. | **Asserted.** Handler unchanged. See MIG-06 and the Review row. |
| POST `/review/compile` | loads the selected run result, claims, and requirements; `compile_report`; `write_report` to a new dated path | `review/compile.py` | `studio/compile/` for assembly. The route may stay a Review action that calls Compile. | **Asserted.** `test_ui_smoke.py` asserts exactly one new `review-report_*.json` and that the decision text is still absent. `test_rev03_review.py` asserts compile without a selected result writes nothing, and a missing or changed claim does not write. `test_review_compile.py` asserts the embedded run omits stored legal sentences. |
| POST `/review` | `save_report_decision` on a confined report path | `review/compile.py` | `studio/review/` | **Asserted.** `test_ui_smoke.py` asserts HTTP 400 before a file exists and asserts the decision text after compile. `test_review_report_kept.py` asserts a later check run does not delete a signed report. |
| POST `/review/sign` | `save_report_signature` | `review/compile.py`, keystore | `studio/review/` | **Asserted.** `test_review_replace_flow.py` and `test_rev03_review.py` `test_decision_and_seal_stay_separate_from_check_status`. `test_compile_pdf.py` asserts the PDF does not call a recorded signature verified. |
| GET/POST `/studio` | GET calls `studio_page`; POST `save_studio_config` | `discovery/studio.py`, still called from `app/server.py` | Shell. Extract only; not moved into `studio/`. | **Asserted.** Handler unchanged. See MIG-03 and the Studio settings row. |

Open-project gate, **fact:** `_requires_open_project` is true for `/`, `/requirements`, `/studio`, `/discover`, `/discover/repo`, `/check`, `/review`, `/requirement`, `/scaffold`, `/discover/run`, `/discover/jobs/…`, `/discover/claims…`, `/discover/feedback…`, and `/review/…`, `/studio/…`. It is false for `/requirements/…` subpaths other than exact `/requirements`, for `/project`, `/claims`, `/prepare`, `/select-pack`, and the demo `/publish` and `/seal-pack`. Failure redirects to `/project`. `test_project_page.py` asserts GET `/discover` with no open repo shows the project list. `test_cover_navigation.py` asserts `/check`, `/review`, `/studio`, `/requirement`, and `/scaffold` show "Registered projects" in that situation, and asserts `/claims`, `/requirements/compare`, and `/requirements/consolidate` still return a heading rather than a traceback.

The previous unverified route table in this file listed `/abort*` and `/try-discovery/file*` as if they were top-level paths. **Fact:** abort is only a suffix of the two job collections above. The try-discovery file page is `/requirements/requirement/{id}/try-discovery/file`.

## CLI and other entry points

| Command | Call path | Target | Tests inspected |
| --- | --- | --- | --- |
| `make start` / `python -m app` | `app/__main__.py` → `app.server.main` → `--workspace` (default workspace), `--host` `127.0.0.1`, `--port` `8770` → `serve` | `studio/app.py` eventually starts the process and registers routers. Flags stay until a separate change. | `test_stop_app.py` asserts stop against a listener. No test asserts `main()`'s argparse itself. |
| `make stop` | `scripts/stop_app.py` | scripts, not a product component | **Asserted.** `test_stop_app.py` asserts lsof/ss/netstat naming and that a free port stays quiet. |
| `python -m checks` | `checks/__main__.py` `_cli`: `--defaults`, `--repo`, `--packs`, `--requirements`, `-j/--json`, `-o/--out`, `--skip` | `curbcheck/cli.py` → `curbcheck/api.py` | **Asserted.** `test_chk07_curbcheck.py` asserts defaults JSON, dated results, both `-j` and `-o`, exit 2 when a pack id is a path, and no file written for invalid `curbpack.json`. |
| `curbcheck-exist`, `curbcheck-contents`, `curbcheck-git`, `curbcheck-node` | `checks/bin/*` or argv0 dispatch in `checks/__main__.py` → `checks/toolmain.py` → `checks/commands.py` | `curbcheck/checks/` | **Asserted.** `test_curbcheck_package.py` asserts exist/contents through the tool entry, git fresh/author, and dep_ban. `test_check_dispatch.py` asserts a separate executable receives check id, repo, and args, and a missing tool fails closed while the next check still runs. `test_git_checks.py` and `test_m4_checks.py` assert the check results. |
| `compile-pdf.py` / `python -m` is not wired; the script calls `compile.cli.main` | `--report`, `--out` → `compile.pdf.compile_pdf` | `studio/compile/` | **Asserted.** `test_compile_pdf.py` asserts a readable PDF, an unchanged source report, no write when the parent is missing, and rejection of a changed claim. |
| `scripts/release/publish.py`, `verify.py`, `smoke.py` | CI release of built artifacts | scripts. Not Pack Publish. | **Asserted** in `test_release_publish.py` (tag, checksum notes, refusal of a run that has not passed). This is not the in-app `/requirements/publish` flow. |
| `scripts/check_story_plan.py` | plan-file structure check | not a product runtime | **Asserted** by `test_story_plan_contract.py`. Out of EP-02 product migration. |

No Pack, Claim, or Review CLI exists. EP-09 would add thin CLIs later. That is not this stage.

## Module → responsibility → target → tests

This is the current implementation map. It is not a move list. One later change takes one page or one handler.

| Current module | Responsibility observed | Target component | Tests that assert this module's behavior |
| --- | --- | --- | --- |
| `app/server.py` | Dispatch, gate, view-models, several validations and writes | Temporary adapter, then delete per route | Most HTTP tests import `make_handler`. `test_requirement_field_errors.py` imports `_requirement_editor_for_error`. `test_sys03_door.py` imports `_write_curbpack`. |
| `app/pages.py` | Shared chrome (`page`, `_flash`, `_reading`, `_current_project_label`, `progress_dialog`, `repo_config_panel`) | Stays importable until each consumer has moved. | Importers are the extracted pages and the requirements and claims UI modules. |
| `app/cover.py` | Home HTML only | Shell, after a later move. Not `studio/` yet. | `test_cover_navigation.py`, `test_ui_smoke.py`, `test_pilot_pack_selection.py` assert GET `/`. |
| `app/requirement_page.py` | Demo `/requirement` HTML only | `studio/pack/` after a later move. Not `studio/` yet. | `test_ui_smoke.py` asserts GET `/requirement`. `test_cover_navigation.py` GETs `/requirement` when no project is open. |
| `app/studio_page.py` | Studio `/studio` HTML only | Shell, after a later move. Not `studio/` yet. | `test_sys03_door.py` `test_studio_page_creates_and_edits_curbpack_studio_json` asserts create, cancel, and edit. `test_cover_navigation.py` GETs `/studio` when no project is open. |
| `app/check_page.py` | Check `/check` HTML only | `studio/check/`, after a later move. Not `studio/` yet. | `test_check_editor.py` asserts named packs and directory fields. `test_sys03_door.py` `test_check_runs_the_open_repository_and_keeps_dated_results` asserts dated run-result files. `test_ui_smoke.py` POSTs `/check`. `test_cover_navigation.py` GETs `/check` when no project is open. |
| `app/claims_page.py` | Claims editor `/claims` HTML only | `studio/claim/`, after a later move. Not `studio/` yet. | `test_claims_binding_ui.py` GETs `/claims`. `test_cover_navigation.py` GETs `/claims` when no project is open. `test_ui_smoke.py` and `test_review_replace_flow.py` post claim actions. |
| `app/review_page.py` | Review `/review` HTML only | `studio/review/`, after a later move. Not `studio/` yet. | `test_rev03_review.py`, `test_review_compile.py` (imports `review_page`), `test_ui_smoke.py`, `test_cover_navigation.py`. |
| `app/scaffold_page.py` | Scaffold `/scaffold` HTML only | Own Studio component and page, as late as possible. See Decided ownership. Not created yet. | `test_ui_smoke.py` `test_open_project_scaffold_page_shows_the_stub_form` asserts the heading, `action="/scaffold"`, and "The stub is not approved evidence." `test_cover_navigation.py` GETs `/scaffold` when no project is open. |
| `app/documents_model.py` | Pack sources view-model for GET `/requirements` without `document` | `studio/pack/`, after a later move. Not `studio/` yet. | `test_cover_navigation.py` `test_opening_an_existing_catalog_shows_the_pack_and_does_not_change_it`, `test_requirements_export.py` `test_pack_sources_row_submits_export_for_that_document`, `test_sys03_door.py` `test_start_empty_then_save_lists_bundled_adapters`. |
| `app/requirement_editor.py` | Requirement editor GET model and save POST | `studio/pack/`, after a later move. Not `studio/` yet. | `test_requirements_ui.py` drives edit, sign, and publish. `test_requirement_field_errors.py` asserts a missing edition redirects to the editor and marks the field. |
| `app/pack_export.py` | Pack export GET model and write | `studio/pack/`, after a later move. Not `studio/` yet. | `test_requirements_export.py` asserts the export page, destination bytes, refusal, and overwrite. |
| `app/project_selector.py` | Project list, add, select | Shell | `test_project_page.py` (`ensure_repos_populated` writes once; select opens the cover). |
| `requirements/catalog.py` | Document/section catalog | `studio/pack/impl/` | `test_requirements_catalog.py` |
| `requirements/workspace.py` | Working copies, selection, publish, export | `studio/pack/impl/` | `test_requirements_publish.py`, `test_requirements_export.py`, `test_requirements_extract.py`, `test_pilot_pack_selection.py` |
| `requirements/editing.py` | Edits, requirement publish, directory seal | `studio/pack/impl/` | `test_m1_requirement.py`, `test_requirements_publish.py`, `test_e2e_annex_vii.py` |
| `requirements/compare.py` | Copy diff, field transfer, extraction review | `studio/pack/impl/` | `test_requirements_compare.py` |
| `requirements/consolidate.py` | Locator suggestions and explicit merge | `studio/pack/impl/` | `test_requirements_consolidate.py` |
| `requirements/jobs.py` | Extract job process, abort, log cap | `studio/pack/impl/` | `test_requirements_jobs.py` |
| `requirements/extract/` | Adapters, Formex, producers, revise loop, assembly | `studio/pack/impl/` | `test_requirements_extract.py`, `test_requirements_produce.py`, `test_revise_loop.py`, `test_xml_adapters.py`, `test_formex_*.py`, `test_cra_vii_compare.py` |
| `requirements/ui/` | Pack-editor HTML and try-discovery HTML | `studio/pack/` pages, try-discovery ownership **open** | `test_requirements_ui.py`, `test_try_discovery_ui.py`, `test_requirements_compare.py` (extract-review page) |
| `claims/bind.py` | Build, rebind, retire, sign, configured create | `studio/claim/impl/` | `test_m3_claims.py`, `test_claim_workflow.py`, `test_create_configured_claims.py`, `test_claims_binding_ui.py` |
| `claims/ui/http.py` | Researcher HTTP and Check-picker mapping | `studio/claim/router.py` then `impl/` for the mapping | `test_discover_claims_ui.py`, `test_claims_binding_ui.py`, `test_rev03_review.py` |
| `claims/ui/researcher.py`, `claims/ui/pages.py` | HTML | `studio/claim/` pages | same HTTP tests |
| `claims/ui/coverage.py` | Which paths a passed claim covers | `studio/claim/impl/` or `studio/review/impl/` when used from Review. **Judgment:** the function answers a Claim/run question; Review only displays it. Owner `studio/claim/`. | `test_review_coverage.py` |
| `discovery/` | Repos, browse, jobs, feedback, search, assess, try-run, studio config file, door paths | `studio/claim/impl/` for search/jobs/feedback/repos. `discovery/studio.py` and `discovery/door.py` open-repo and `curbpack-studio.json` are shell/workspace, not Claim rules. | `test_discover_*.py`, `test_m2_discovery.py`, `test_discovery_assess.py`, `test_sys03_door.py` |
| `checks/` | Registry, subprocess checks, run results, CLI | `curbcheck/` | `test_check_dispatch.py`, `test_chk07_curbcheck.py`, `test_m4_checks.py`, `test_git_checks.py`, `test_curbcheck_package.py`, `test_curbcheck_action.py` |
| `review/compile.py` | Assemble report, validate, decision, signature, dated path | Split: `studio/compile/impl/` for `compile_report` / `validate_report` / `write_report`; `studio/review/impl/` for `record_decision` / `sign_report` and their save wrappers | `test_review_compile.py`, `test_rev03_review.py`, `test_compile_pdf.py`, `test_e2e_annex_vii.py` |
| `review/present.py` | Review read model | `studio/review/impl/` | Asserted through Review HTTP tests and `test_rev03_review.py` `test_seal_label_mapping` |
| `review/gitseal.py` | Git commit signature and claim signature reading | `studio/review/impl/` for review display; signature primitives can stay shared | `test_rev03_review.py`, `test_e2e_annex_vii.py`, `tests/cs/git_provenance.py` (not in `make test`) |
| `review/view_html.py` | Second Review renderer | No owner until something calls it. It is unused. | **None** |
| `compile/pdf.py`, `compile/cli.py` | PDF from a saved report | `studio/compile/` | `test_compile_pdf.py` |
| `scaffold/stub.py` | Write a stub file | Same late Studio component as the scaffold page. See Decided ownership. | `test_e2e_annex_vii.py` |
| `common/jsonio.py`, `common/store.py`, `common/validate.py`, `common/signing.py`, `common/keystore.py`, `common/canonical.py`, `common/paths.py`, `common/errors.py` | Shared IO, validation, signing, digests | `models/` only for the future Pydantic shapes of Packs v2. IO and signing stay callable from component `impl/`. Do not invent a service layer. | `test_jsonio.py`, `test_m1_requirement.py`, `test_requirements_publish.py`, `test_delivery.py` (paths) |
| `demo_setup.py`, `workflow.py` | Sample workspace and demo requirement reading | Keep with the demo routes they serve. Not new features. | `test_ui_smoke.py` uses `prepare_demo` |
| `scripts/build/`, `Makefile`, `.github/workflows/` | Package and CI | Stay scripts. Entrypoints change only when the process entry moves. | `test_delivery.py`, `test_installers.py`, `test_curbcheck_package.py` (unit-level; this baseline did not build native binaries) |

## Architecture deviations (verified)

These are differences between this tree and the target. They are expected before migration. They are not defects to fix in MIG-00.

1. **Fact.** Dispatch is still `app/server.py`. Extracted renderers (`app/cover.py`, `app/requirement_page.py`, `app/studio_page.py`, `app/check_page.py`, `app/claims_page.py`, `app/review_page.py`, `app/scaffold_page.py`), the Pack sources view-model (`app/documents_model.py`), and the requirement editor (`app/requirement_editor.py`), and the Pack export (`app/pack_export.py`) live beside `app/pages.py` until a later move. Shared chrome is still in `app/pages.py`. The target shell only starts the app and registers component routers.
2. **Fact.** Check execution is `checks/`, invoked by Studio as `run_and_write`. The target public API is `curbcheck/api.py`, with `studio/check/` as a thin adapter.
3. **Fact.** `review/compile.py` both assembles the report and records the human decision and signature. The target gives assembly and PDF to `studio/compile/` and the decision/signature to `studio/review/`.
4. **Fact.** `compile/pdf.py` is headless CLI only. Review's HTTP compile writes JSON, not PDF.
5. **Fact.** `claims/ui/http.py` encodes Check-picker rules (`exist`, `contents`, `fresh`, `owned`, `dep_ban`, and the legacy choice names) and writes Claims. That is domain behavior in the HTTP module.
6. **Fact.** `review/view_html.py` duplicates Review card markup and is unreferenced. Live markup is `app/pages.py`.
7. **Fact.** There is no authentication or authorization component. The only gate is "an open project", and it does not cover every POST.
8. **Fact.** Persistent validation is hand-written (`common/validate.py` and the extract/review validators). Packs v2 is not implemented as Pydantic, and JSON Schema is not generated from Pydantic.
9. **Fact.** Legacy Publish, demo `/requirement`, `/publish`, `/seal-pack`, `/prepare`, `/claims`, and `/scaffold` are still routed. Cover tests assert that `/claims` and `/scaffold` are not linked from Home. The handlers still exist.
10. **Fact.** `discovery/door.py` and `discovery/studio.py` hold workspace selection and Studio settings, inside a package whose other modules are Claim discovery.

## Missing test coverage

"Missing" means no assertion for that behavior was found. It does not mean the behavior is wrong.

**HTTP paths with no assertion:**

- GET `/vendor/jsondiffpatch.css`
- GET `/icons/curbpack-icon.svg`
- GET `/requirements/inspect`
- POST `/requirements/source`
- POST `/requirements/start-empty`
- POST `/requirements/jobs/{id}/abort`
- POST `/discover/jobs/{id}/abort`
- POST `/discover/claims/create` (`create_configured_claims` is tested directly)
- POST `/requirements/compare/apply` (domain apply is tested)
- POST `/requirements/consolidate/apply` (domain apply is tested)
- POST `/prepare`
- POST `/requirement` (demo save)
- POST `/publish` (demo requirement publish)
- POST `/seal-pack`
- The literal "Unknown page." response

**Pages with only a smoke assertion:** GET `/requirements/compare` and GET `/requirements/consolidate` (heading and no traceback, or redirect to the project list).

**Suites not in the baseline run:** `tests/cs/*` (path boundary, review signature, check-result integrity, git provenance, workspace selector). Native `make package*` was not run. `test_curbcheck_package.py` and `test_installers.py` did run as part of the 416; they mock or stop before a real host install. They are not a substitute for a packaged binary smoke test.

**Not claimed:** line coverage, branch coverage, or that every assertion in a long test (for example `test_rev03_review.py`) was re-executed against a reading of all 1,400 lines. The runner executed them. The matrix cites the assertions that identify each route.

## Proposed order to extract Python pages

**Items 1–7 are extracted.** Stage 1 page extraction for this list is complete. Each step moved one rendering function out of `app/pages.py`, left the URL and the handler in `app/server.py`, and kept `page`, `_flash`, `_reading`, `_current_project_label`, `progress_dialog`, and `repo_config_panel` importable from `app.pages`. `scaffold_page` also imports `page` and `_flash`. Do not combine the later handler slices. Do not start the next one after a failure.

Pages already in `requirements/ui/` and `claims/ui/` are not in this list. Splitting them again would not remove them from `app/pages.py`. Their server view-models follow this list, still one handler at a time.

1. `cover` — **extracted** in MIG-01 to `app/cover.py`. GET `/` and the redirect to `/project` when no project is open stay in `app/server.py`.
2. `requirement_page` — **extracted** in MIG-02 to `app/requirement_page.py`. GET `/requirement`, `load_requirement`, `snapshot`, and `_require_demo_requirement` stay in `app/server.py`. `test_ui_smoke.py` asserts the requirement text.
3. `studio_page` — **extracted** in MIG-03 to `app/studio_page.py`. `_review_path_chrome` moved with it. GET and POST `/studio`, `_studio_model`, `_studio_message`, and `save_studio_config` stay in `app/server.py`. Gate: `test_sys03_door.py` `test_studio_page_creates_and_edits_curbpack_studio_json`.
4. `check_page` — **extracted** in MIG-04 to `app/check_page.py`. `_curbpack_editor` moved with it. `repo_config_panel` stayed in `app/pages.py`. GET and POST `/check`, `_check_editor_model`, `_check_report`, and `_check_message` stay in `app/server.py`. Gate: `test_check_editor.py` and `test_sys03_door.py` check tests.
5. `claims_page` — **extracted** in MIG-05 to `app/claims_page.py`. `_claim_context`, `_claim_seal_html`, and `_passages_html` moved with it. `repo_config_panel` stayed in `app/pages.py`. GET `/claims`, the saved/cleared/signed/retired message, and `_claims_model` stay in `app/server.py`. POST `/claims`, `/claims/{id}`, `/claims/{id}/sign`, and `/claims/{id}/retire` stay there. Gate: `test_claims_binding_ui.py`.
6. `review_page` — **extracted** in MIG-06 to `app/review_page.py`, with the private helpers that were only used by it. `page`, `_flash`, `_reading`, and `repo_config_panel` stayed in `app/pages.py`. GET `/review`, `_review_view`, and `_door_chrome` stay in `app/server.py`. `tests/test_review_compile.py` now imports `review_page` from `app.review_page`. Gate: `test_rev03_review.py` and `test_review_compile.py` `test_page_shows_an_older_run_and_requirements_that_were_not_checked`.
7. `scaffold_page` — **extracted** in MIG-07 to `app/scaffold_page.py`. No private helper moved with it. GET `/scaffold` calls `scaffold_page()` with no arguments. POST still calls `write_stub` and redirects to `/scaffold?wrote=1`; that query is not read. `scaffold/stub.py` is unmoved. The owner is now its own Studio component, created as late as possible. See Decided ownership. Gate: `test_ui_smoke.py` `test_open_project_scaffold_page_shows_the_stub_form` asserts the heading, form action, and "The stub is not approved evidence." The POST still does not assert the stub file.

`project_page` is already outside `app/pages.py`. Do not mix it into this extraction. A later single change can thin `handle_project_post` without moving the other doors.

After those seven, the next single slices are handler/view-model extractions, still not a batch.

8. Pack sources GET — **extracted** in MIG-08 to `app/documents_model.py` `_documents_model`. `_edit_adapter_choices` moved with it because nothing else called it. The URL stays in `Handler._get`. `?document=` still calls `_catalog_model` in `app/server.py`. POST routes stay there. `_sync_open_repo`, `_registered_repo_path`, `_adapter_for_url`, `_catalog_job`, and `_catalog_message` stay in `app/server.py` because other handlers use them. The model imports those five when it runs. `documents_page` stays in `requirements/ui/pages.py`. Not moved into `studio/`.
9. Requirement editor GET/POST — **extracted** in MIG-09 to `app/requirement_editor.py`. `_editor_model`, `_editor_message`, `_save_requirement_form`, and `_edits_from_form` moved. The URL, the `saved=1` redirect, sign, and try-discovery stay in `app/server.py`. `_open_requirement` stays for try-discovery and sign. `_pack_query` stays for those redirects, `_repo_pack_copy_model`, and `_requirement_editor_for_error`. `_lines` stays for the demo `edits_for_requirement`. The editor imports those three when it runs. `editor_page` stays in `requirements/ui/pages.py`. Not moved into `studio/`.
10. Export GET/POST — **extracted** in MIG-10 to `app/pack_export.py`. `_export_model`, `_export_document`, and `_export_selected` moved. The URL stays in `app/server.py`. `_formex_sources` stays there because the discover sources and the catalog model use it. The export imports it when it runs. `export_page` stays in `requirements/ui/pages.py`. Not moved into `studio/`.

The next single slice is extract-review GET/POST. It is not started. Compare and consolidate apply are owned by `studio/pack/`. Their business logic stays in the shared Requirements backend. The router and the UI stay thin. No test posts `/requirements/compare/apply` or `/requirements/consolidate/apply`; `test_requirements_compare.py` and `test_requirements_consolidate.py` assert the domain functions. That gap is recorded and does not block the migration.

## Decided ownership

Decided 2026-11-08. These four decisions are also named from [EP-02](EPIC.md). They do not authorize a new story, a package directory, or a behavior change in the current extract. None of them blocks the one-handler migration.

1. **Scaffold.** Its own Studio component, with its own page, created as late as possible. EP-02 preserves the current stub: `app/scaffold_page.py`, `scaffold/stub.py`, and the `/scaffold` routes. EP-02 does not build a later agent or repair architecture. That later work may justify a separate repository. The component directory is created in that late slice, not before.
2. **Try-discovery.** Owned by `studio/claim/` Discovery. The requirement editor only makes an API call. The current button, file view, and job stay where they are until their own slice. Do not fold the search into `studio/pack/`.
3. **Authentication.** `studio/authentication/` and `studio/authorization/`, as in the target architecture. This tree still has no login beyond the open-project redirect. Adding those packages is not part of a behavior-preserving extract of an existing page.
4. **Compare and consolidate apply.** Owned by `studio/pack/`. One shared Requirements backend. The business logic does not live in the router or the UI. The missing HTTP posts are a recorded test gap, not an ownership gap.

## Open questions

1. **Project selection vs `studio/app.py`.** The target shell must not contain feature logic, and project selection is not a Pack, Claim, Check, Compile, or Review rule. Proposal: a small shell-adjacent module registered by `studio/app.py`, not an eighth product engine. Not decided.
2. **Unused `review/view_html.py`.** Proposal: do not migrate it. Confirm it is dead before any later deletion. Deletion is not part of MIG-00.
3. **Demo routes** `/requirement`, `/publish`, `/seal-pack`, `/prepare`. They are reachable and partly untested over HTTP. Proposal: preserve them as historical behavior under `studio/pack/` when their pages are extracted, and do not treat them as the Pack editor. Not a decision to remove them.
4. **`tests/cs/` not collected by `make test`.** Whether they should be added to the suite is a test-policy decision, not a migration step.

## Area rollup

The epic asked for one row per area. Those rows are indexes. Work proceeds by the handler table, one row at a time. Status means the baseline is recorded. It does not mean the area has been migrated or that every handler in it has an HTTP assertion.

| Functional area | Existing implementation | Target owner | Assertion-backed tests (inspected) | Handlers still without an HTTP assertion | Status |
| --- | --- | --- | --- | --- | --- |
| Shell / project / Studio settings | `app/server.py`, `app/project_selector.py`, `app/cover.py` `cover`, `app/studio_page.py` `studio_page` | Shell | `test_project_page.py`, `test_cover_navigation.py`, `test_pilot_pack_selection.py`, `test_sys03_door.py` studio and curbpack save | POST `/prepare`; SVG icon | Cover and Studio renderers extracted. Project selection and the handler are not started. |
| Pack catalogue and sources | `requirements/catalog.py`, `requirements/ui/pages.py`, `app/documents_model.py`, remaining server view-models | `studio/pack/` | `test_requirements_catalog.py`, `test_requirements_ui.py` | GET `/requirements/inspect`, POST `/requirements/source`, POST `/requirements/start-empty` | Pack sources view-model extracted. Export is extracted in MIG-10. The other Pack source handlers are not started. |
| Extract and jobs | `requirements/extract/`, `requirements/jobs.py` | `studio/pack/` | `test_requirements_extract.py`, `test_requirements_jobs.py`, `test_requirements_ui.py`, `test_revise_loop.py`, `test_e2e_annex_vii.py` | POST job abort URL | Baseline recorded; migration not started |
| Formex | `requirements/extract/formex/` | `studio/pack/impl/` | `test_formex_inventory.py`, `test_formex_provisions_cra.py`, `test_formex_package.py`, `test_formex_no_number_leak.py`, `test_xml_adapters.py`, `test_cra_vii_compare.py` | no separate HTTP surface | Baseline recorded; migration not started |
| Requirement edit and sign | `requirements/editing.py`, `app/requirement_editor.py`, editor page, `app/requirement_page.py` `requirement_page` | `studio/pack/` | `test_m1_requirement.py`, `test_requirement_field_errors.py`, `test_requirements_ui.py`, `test_requirements_publish.py` | demo POST `/requirement`, `/publish`, `/seal-pack` | Demo `/requirement` renderer extracted. Requirement editor GET model and save POST extracted. Sign and the demo POST handlers are not started. |
| Working copies, legacy Publish, export | `requirements/workspace.py`, `app/pack_export.py` | `studio/pack/` | `test_requirements_publish.py`, `test_requirements_export.py`, `test_pilot_pack_selection.py` | none beyond the demo publish URLs above | Export GET model and POST extracted. Publish and the copy handler are not started. |
| Compare and consolidate | `requirements/compare.py`, `requirements/consolidate.py` | `studio/pack/`. Shared Requirements backend. See Decided ownership. | domain tests named above; extract-review HTTP asserted | compare page smoke only; both `*/apply` URLs. The gap does not block. | Baseline recorded; migration not started |
| Claims | `claims/bind.py`, `app/claims_page.py` `claims_page` | `studio/claim/` | `test_m3_claims.py`, `test_claim_workflow.py`, `test_claims_binding_ui.py`, `test_create_configured_claims.py`, `test_review_replace_flow.py` | none for the claims editor routes | Claims editor renderer extracted. POST routes and the handler are not started. |
| Discovery | `discovery/`, `claims/ui/` | `studio/claim/` | `test_discover_claims_ui.py`, `test_discover_browse.py`, `test_discover_repos.py`, `test_discover_feedback.py`, `test_m2_discovery.py`, `test_discovery_assess.py` | POST `/discover/claims/create`; POST discover job abort URL | Baseline recorded; migration not started |
| Try-discovery | `requirements/ui/try_discovery.py`, `discovery/try_run.py` | `studio/claim/` Discovery. The editor only calls it. See Decided ownership. | `test_try_discovery_ui.py` | none for the asserted routes | Baseline recorded; migration not started |
| Curbcheck | `checks/` | `curbcheck/` | `test_check_dispatch.py`, `test_chk07_curbcheck.py`, `test_m4_checks.py`, `test_git_checks.py`, `test_curbcheck_catalogue.py`, `test_curbcheck_package.py` | packaged binary not run in this baseline | Baseline recorded; migration not started |
| Studio Check | `app/check_page.py` `check_page`, POST `/check` | `studio/check/` → `curbcheck/api.py` | `test_check_editor.py`, `test_chk08_studio.py`, `test_sys03_door.py`, `test_ui_smoke.py` | none for the main POST | Check renderer extracted. POST `/check` and the handler are not started. |
| Review | `app/review_page.py` `review_page`, `review/present.py`, decision/sign in `review/compile.py` | `studio/review/` | `test_rev03_review.py`, `test_review_compile.py`, `test_review_replace_flow.py`, `test_review_report_kept.py`, `test_review_discover_again.py`, `test_review_coverage_ui.py` | unused `view_html.py` | Review renderer extracted. Presentation, decision, signing, and the handler are not started. |
| Compile | `review/compile.py` assembly, `compile/pdf.py` | `studio/compile/` | `test_review_compile.py`, `test_compile_pdf.py`, `test_chk08_studio.py` | no HTTP PDF route, by inspection | Baseline recorded; migration not started |
| Shared IO and signing | `common/` | shared, plus future `models/pydantic/` when a contract story says so | `test_jsonio.py`, signature cases inside publish and review tests | `tests/cs/` not in `make test` | Baseline recorded; migration not started |
| Install and CLI wiring | `Makefile`, `scripts/`, `app/__main__.py`, `checks/__main__.py` | entrypoints updated in place later | `test_delivery.py`, `test_installers.py`, `test_stop_app.py` | native package smoke not run | Baseline recorded; migration not started |

## MIG-01 — extract `cover`

**Status:** extract gate passed. Move, separate, Pydantic, FastAPI, and TypeScript are not this step.

| Field | Record |
| --- | --- |
| Identifier | Home / cover. GET `/`. Shows the four navigation links, or the project list when no project is open. |
| Baseline | Parent revision `99afc44569b94caa069ce6dd019825bf06dc77fa`. Renderer was `app/pages.py` `cover`. The function ignores its model argument. `Handler._get` still calls `_home_model` (selection side effects) and `_home_message`, then renders. No open project: `_requires_open_project` redirects to `/project`. |
| Extract | `app/cover.py` `cover`. Same function text. `app/server.py` delegates with `cover(_home_model(ws), message=_home_message(query))`. URL, handler, `_home_model`, and `_home_message` stayed in `app/server.py`. `page` and `_flash` stayed in `app/pages.py`. |
| Move | Not started. File is not under `studio/`. |
| Separate | Not started. No domain logic was moved. |
| Boundary | Not applicable. No Packs v2 or Pydantic change. |
| HTTP | Not started. Old `ThreadingHTTPServer` still serves GET `/`. |
| UI | Not started. Still Python HTML. |
| Gate | Focused, before and after the move: `.venv/bin/python -m unittest tests.test_cover_navigation tests.test_ui_smoke tests.test_pilot_pack_selection`. Before: 10 tests, OK, 3.775s. After: 10 tests, OK, 3.673s. Exit code 0 both times. Then `make test`: **416 PASS, 0 FAIL**, exit code 0, about 87 seconds. No skip summary was printed. This run did not execute `make cicd`, `make package`, `make package-studio`, `make package-curbcheck`, or `tests/cs/`. |
| Checkpoint | Local commit on `daniel/post-pilot-fixes-1` that adds this section. The hash is not written here; a commit cannot record itself. |
| Review | Independent read of `git diff HEAD`. No Critical or Important findings. Three wording notes were applied in this file before the commit: GET `/` stays **Asserted**; `VERIFIED` is not redefined as an extract; `app/cover.py` is listed as an importer of `page` and `_flash`. |

`app.pages.cover` is gone. The only call site was `app/server.py`.

## MIG-02 — extract `requirement_page`

**Status:** extract gate passed. Move, separate, Pydantic, FastAPI, and TypeScript are not this step.

| Field | Record |
| --- | --- |
| Identifier | Demo requirement. GET `/requirement`. Shows the saved demo requirement text, or the project list when no project is open. |
| Baseline | Parent revision `88521e14fcac019ffd9485cf18af14de820a58b2`. Renderer was `app/pages.py` `requirement_page`. `Handler._get` still calls `load_requirement` (`packs/cra-baseline/CRA-ANNEX-VII-RISK.json`) and `snapshot`, then renders. No open project: `_requires_open_project` redirects to `/project`. |
| Extract | `app/requirement_page.py` `requirement_page`. Same function text. The only caller omits `message` and `error`; the original signature stays and still passes them to `_flash`. `_lines` moved with it; `app/pages.py` used that helper only for this function. `app/server.py` delegates with `requirement_page(requirement, reading)`. URL, handler, `load_requirement`, `snapshot`, and `_require_demo_requirement` stayed in `app/server.py`. `app/server.py` `_lines` was not changed. `page`, `_flash`, and `_reading` stayed in `app/pages.py`. |
| Move | Not started. File is not under `studio/`. |
| Separate | Not started. No domain logic was moved. |
| Boundary | Not applicable. No Packs v2 or Pydantic change. |
| HTTP | Not started. Old `ThreadingHTTPServer` still serves GET `/requirement`. |
| UI | Not started. Still Python HTML. |
| Gate | Focused: `.venv/bin/python -m unittest tests.test_ui_smoke tests.test_cover_navigation`. 5 tests, OK, 2.803s. Exit code 0. Those two modules are the only tests that GET the demo `/requirement` URL; no test POSTs it. Then `make test`: **Summary: 416 PASS, 0 FAIL**, exit code 0, about 85 seconds (`real 84.92`). No skip summary was printed. This run did not execute `make cicd`, `make package`, `make package-studio`, `make package-curbcheck`, or `tests/cs/`. |
| Checkpoint | The later local commit on `daniel/post-pilot-fixes-1` that adds this section. The hash is not written here; a commit cannot record itself. |
| Review | Independent read of `git diff HEAD`. No Critical or Important findings. Three wording notes were applied before the commit: the caller omits `message` and `error` but the signature stays; `app/pages.py` no longer calls itself the demo HTML; `test_ui_smoke.py` stays off the edit-and-sign test list. |

`app.pages.requirement_page` is gone. The only call site was `app/server.py`.

## MIG-03 — extract `studio_page`

**Status:** extract gate passed. Move, separate, Pydantic, FastAPI, and TypeScript are not this step.

| Field | Record |
| --- | --- |
| Identifier | Studio settings. GET `/studio`. Shows the studio config form, or the project list when no project is open. |
| Baseline | Parent revision `3f044c1f2b15a1bb0d5b29747bb87efb51c10cc2`. Renderer was `app/pages.py` `studio_page`. `Handler._get` still calls `_studio_model` and `_studio_message`, then renders. POST `/studio` still calls `save_studio_config`. No open project: `_requires_open_project` redirects to `/project`. |
| Extract | `app/studio_page.py` `studio_page`. Same function text. `app/server.py` delegates with `studio_page(_studio_model(ws, query), message=_studio_message(query))`. URL, handler, `_studio_model`, and `_studio_message` stayed in `app/server.py`. POST still calls `save_studio_config` there. `_review_path_chrome` moved with `studio_page`; a search found no other caller. `_current_project_label` stayed in `app/pages.py` because `repo_config_panel` calls it. Claims, Check, and Review in `app/pages.py` use that panel, and so do `requirements/ui/pages.py` and `claims/ui/pages.py`. `studio_page` imports `page`, `_flash`, and `_current_project_label`. |
| Move | Not started. File is not under `studio/`. |
| Separate | Not started. No domain logic was moved. |
| Boundary | Not applicable. No Packs v2 or Pydantic change. |
| HTTP | Not started. Old `ThreadingHTTPServer` still serves GET and POST `/studio`. |
| UI | Not started. Still Python HTML. |
| Gate | Focused: `.venv/bin/python -m unittest tests.test_sys03_door.StudioConfigTest.test_studio_page_creates_and_edits_curbpack_studio_json tests.test_cover_navigation`. 5 tests, OK, 2.250s (`real 2.40`). Exit code 0. Then `make test`: **Summary: 416 PASS, 0 FAIL**, exit code 0, about 85 seconds (`real 85.08`). No skip summary was printed. This run did not execute `make cicd`, `make package`, `make package-studio`, `make package-curbcheck`, or `tests/cs/`. |
| Checkpoint | The later local commit on `daniel/post-pilot-fixes-1` that adds this section. The hash is not written here; a commit cannot record itself. |
| Review | Independent read of `git diff HEAD`. No Critical or Important findings. Two wording notes were applied before the commit: `_current_project_label` is on the keep-importable list, and the deviation list no longer says all product HTML is still in `app/pages.py`. |

`app.pages.studio_page` is gone. The only call site was `app/server.py`.

## MIG-04 — extract `check_page`

**Status:** extract gate passed. Move, separate, Pydantic, FastAPI, and TypeScript are not this step.

| Field | Record |
| --- | --- |
| Identifier | Check. GET `/check`. Shows the open repository's packs and the selected run, or the project list when no project is open. |
| Baseline | Parent revision `28aabea6d69446e64ccf2c2bafab0da0e2bf45b4`. Renderer was `app/pages.py` `check_page`. `Handler._get` still calls `_check_editor_model` and `_check_report`, then renders. POST `/check` still validates `curbpack.json` and calls `run_and_write`. No open project: `_requires_open_project` redirects to `/project`. |
| Extract | `app/check_page.py` `check_page`. Same function text. The only caller omits `error`; the original signature stays and still passes it to `_flash`. `_curbpack_editor` moved with it; a search found no other caller. `app/server.py` delegates with `check_page(result, exit_code, message=_check_message(query), editor=editor)`. URL, handler, `_check_editor_model`, `_check_report`, and `_check_message` stayed in `app/server.py`. POST stays there. `repo_config_panel` stayed in `app/pages.py` because Claims, Review, `requirements/ui/pages.py`, and `claims/ui/pages.py` call it. `check_caption` stays imported in `app/pages.py` because `_review_checks` uses it; `check_page` imports it from `checks.labels`. `check_page` imports `page`, `_flash`, and `repo_config_panel`. |
| Move | Not started. File is not under `studio/`. |
| Separate | Not started. No domain logic was moved. |
| Boundary | Not applicable. No Packs v2 or Pydantic change. |
| HTTP | Not started. Old `ThreadingHTTPServer` still serves GET and POST `/check`. |
| UI | Not started. Still Python HTML. |
| Gate | Focused: `.venv/bin/python -m unittest tests.test_check_editor tests.test_sys03_door.DoorUiTest.test_product_views_are_empty_until_a_repository_is_open tests.test_sys03_door.CheckIoTest.test_check_runs_the_open_repository_and_keeps_dated_results tests.test_sys03_door.ReviewIoTest.test_review_compiles_the_open_repository_run_into_dated_reports tests.test_cover_navigation tests.test_ui_smoke`. 9 tests, OK, 7.230s (`real 7.36`). Exit code 0. Then `make test`: **Summary: 416 PASS, 0 FAIL**, exit code 0, about 85 seconds (`real 85.01`). No skip summary was printed. This run did not execute `make cicd`, `make package`, `make package-studio`, `make package-curbcheck`, or `tests/cs/`. |
| Checkpoint | The later local commit on `daniel/post-pilot-fixes-1` that adds this section. The hash is not written here; a commit cannot record itself. |
| Review | Independent read of `git diff HEAD`. No Critical, Important, or Minor findings. |

`app.pages.check_page` is gone. The only call site was `app/server.py`.

## MIG-05 — extract `claims_page`

**Status:** extract gate passed. Move, separate, Pydantic, FastAPI, and TypeScript are not this step.

| Field | Record |
| --- | --- |
| Identifier | Claims editor. GET `/claims`. Shows existing claims, or a heading when no project is open. |
| Baseline | Parent revision `012d1b8512c44949686d7e1d637b2812ffc6a464`. Renderer was `app/pages.py` `claims_page`. `Handler._get` still chooses the saved, cleared, signed, or retired message, calls `_claims_model`, then renders. POST `/claims`, `/claims/{id}`, `/claims/{id}/sign`, and `/claims/{id}/retire` stay in `app/server.py`. `/claims` is not behind the open-project redirect. |
| Extract | `app/claims_page.py` `claims_page`. Same function text. The only caller omits `error`; the original signature stays and still passes it to `_flash`. `_claim_context`, `_claim_seal_html`, and `_passages_html` moved with it; a search found no other caller. `app/server.py` delegates with `claims_page(_claims_model(ws, query), message=message)`. URL, handler, and `_claims_model` stayed in `app/server.py`. `repo_config_panel` stayed in `app/pages.py` because Review, `requirements/ui/pages.py`, and `claims/ui/pages.py` call it. `claims_page` imports `page`, `_flash`, and `repo_config_panel`. |
| Move | Not started. File is not under `studio/`. |
| Separate | Not started. No domain logic was moved. |
| Boundary | Not applicable. No Packs v2 or Pydantic change. |
| HTTP | Not started. Old `ThreadingHTTPServer` still serves GET and POST `/claims`. |
| UI | Not started. Still Python HTML. |
| Gate | Focused: `.venv/bin/python -m unittest tests.test_claims_binding_ui tests.test_cover_navigation tests.test_ui_smoke tests.test_review_replace_flow`. 12 tests, OK, 5.752s. Exit code 0. Then `make test`: **Summary: 416 PASS, 0 FAIL**, exit code 0, about 85 seconds. No skip summary was printed. This run did not execute `make cicd`, `make package`, `make package-studio`, `make package-curbcheck`, or `tests/cs/`. |
| Checkpoint | The later local commit on `daniel/post-pilot-fixes-1` that adds this section. The hash is not written here; a commit cannot record itself. |
| Review | Independent read of `git diff HEAD`. No Critical or Important findings. Before the commit: the page import was placed in alphabetical order, and POST `/claims/{id}/retire` is recorded as asserted by `test_review_replace_flow.py`. |

`app.pages.claims_page` is gone. The only call site was `app/server.py`. This is not `claims/ui/researcher.py` `requirement_page`.

## MIG-06 — extract `review_page`

**Status:** extract gate passed. Move, separate, Pydantic, FastAPI, and TypeScript are not this step.

| Field | Record |
| --- | --- |
| Identifier | Review. GET `/review`. Shows the review board, or the project list when no project is open. A missing `curbpack.json` still renders the page with the error. |
| Baseline | Parent revision `b38f830e88fd93d51bc23c4126d4c5b4a42bf092`. Renderer was `app/pages.py` `review_page`. `Handler._get` still calls `_review_view` and `_door_chrome`, then renders. POST `/review` stays in `app/server.py`. |
| Extract | `app/review_page.py` `review_page`. Same function text, and the same text for the nineteen helpers that were only used there (`_review_groups` through `_dialog_id`). Both call sites in `app/server.py` delegate with the same arguments. `tests/test_review_compile.py` imports `review_page` from `app.review_page` because it called the function directly. `page`, `_flash`, `_reading`, and `repo_config_panel` stayed in `app/pages.py`. `check_caption`, `quote`, `re`, the constants `NO_CRA_FIELD` and `NOT_A_LEGAL_CONCLUSION`, and the function `worktree_sentence` moved with this module because nothing left in `app/pages.py` used them. |
| Move | Not started. File is not under `studio/`. |
| Separate | Not started. No domain logic was moved. |
| Boundary | Not applicable. No Packs v2 or Pydantic change. |
| HTTP | Not started. Old `ThreadingHTTPServer` still serves GET and POST `/review`. |
| UI | Not started. Still Python HTML. |
| Gate | Focused: `.venv/bin/python -m unittest tests.test_rev03_review tests.test_review_compile tests.test_cover_navigation tests.test_ui_smoke tests.test_review_replace_flow tests.test_review_coverage_ui tests.test_review_discover_again`. 55 tests, OK, 27.992s. Exit code 0. Then `make test`: **Summary: 416 PASS, 0 FAIL**, exit code 0, about 82 seconds. No skip summary was printed. This run did not execute `make cicd`, `make package`, `make package-studio`, `make package-curbcheck`, or `tests/cs/`. |
| Checkpoint | The later local commit on `daniel/post-pilot-fixes-1` that adds this section. The hash is not written here; a commit cannot record itself. |
| Review | Independent read of `git diff HEAD`. No Critical or Important findings. Before the commit, `worktree_sentence` is named as a function, and `NO_CRA_FIELD` and `NOT_A_LEGAL_CONCLUSION` as the two constants. |

`app.pages.review_page` is gone. The call sites were `app/server.py` and `tests/test_review_compile.py`.

## MIG-07 — extract `scaffold_page`

**Status:** extract gate passed. Move, separate, Pydantic, FastAPI, and TypeScript are not this step. The owner stays **Open**.

| Field | Record |
| --- | --- |
| Identifier | Scaffold. GET `/scaffold`. With no open project the open-project gate redirects to the project list. POST writes a stub and redirects to `/scaffold?wrote=1`. |
| Baseline | Parent revision `5f509e04392deba4a0875124a19635be6966eb37`. Renderer was `app/pages.py` `scaffold_page`. `Handler._get` calls it with no arguments, so `message` and `error` stay at their defaults and `?wrote=1` is not read. POST `/scaffold` calls `write_stub` in `scaffold/stub.py`. |
| Extract | `app/scaffold_page.py` `scaffold_page`. Same function text. No private helper moved. `app/server.py` delegates with `scaffold_page()`. The URL and the handler stayed in `app/server.py`. POST calls `write_stub` in `scaffold/stub.py`. `page` and `_flash` stayed in `app/pages.py`. `scaffold/stub.py` is unmoved. No `studio/scaffold/` directory. |
| Move | Not started. Owner is still **Open**. |
| Separate | Not started. |
| Boundary | Not applicable. No Packs v2 or Pydantic change. |
| HTTP | Not started. Old `ThreadingHTTPServer` still serves GET and POST `/scaffold`. |
| UI | Not started. Still Python HTML. |
| Gate | Focused: `.venv/bin/python -m unittest tests.test_cover_navigation tests.test_ui_smoke tests.test_e2e_annex_vii`. 7 tests, OK, 4.158s. Exit code 0. `test_open_project_scaffold_page_shows_the_stub_form` asserts `<h1>Scaffold</h1>`, `action="/scaffold"`, and "The stub is not approved evidence." The other tests still redirect GET `/scaffold` when no project is open, POST `/scaffold` without asserting the stub file, and call `write_stub` directly. Then `make test`: **Summary: 417 PASS, 0 FAIL**, exit code 0, about 86 seconds. No skip summary was printed. This run did not execute `make cicd`, `make package`, `make package-studio`, `make package-curbcheck`, or `tests/cs/`. |
| Checkpoint | The later local commit on `daniel/post-pilot-fixes-1` that adds this section. The hash is not written here; a commit cannot record itself. |
| Review | Two independent reads of `git diff HEAD`. The first found no Critical findings and one Important finding: the moved HTML was not asserted while the record called the gate passed. Before the commit, `tests/test_ui_smoke.py` gained `test_open_project_scaffold_page_shows_the_stub_form`, and the record cites that assertion. The first review's Minor note is applied: the POST handler calls `write_stub`; the function stays in `scaffold/stub.py`. The second read found no Critical or Important findings. Its smoke-list note is applied: compare and consolidate stay in the smoke-only list, and the scaffold body stays on the Asserted rows. The test does not lock "refuses to overwrite", `name="path"`, or the default path. The record does not claim those strings. |

`app.pages.scaffold_page` is gone. The only call site was `app/server.py`.

## MIG-08 — extract the Pack sources view-model

**Status:** extract gate passed. Move, separate, Pydantic, FastAPI, and TypeScript are not this step.

| Field | Record |
| --- | --- |
| Identifier | Pack sources. GET `/requirements` without `document`. With no open project the open-project gate redirects to the project list. `?document=` is the Pack sections page and is not this step. |
| Baseline | Parent revision `3bd3b0f28a72945b91d7488c6e4e7487f1429a17`. View-model was `app/server.py` `_documents_model`. `Handler._get` calls `documents_page` with that model. POST routes under `/requirements` stay in `app/server.py`. |
| Extract | `app/documents_model.py` `_documents_model`. Same return value and the same calls. `_edit_adapter_choices` moved with it. The model imports `_sync_open_repo`, `_registered_repo_path`, `_adapter_for_url`, `_catalog_job`, and `_catalog_message` from `app.server` when it runs, because those functions still serve other handlers. When the query names a repo id that is already registered, `_sync_open_repo` still writes `open-repo.json`. An unknown id raises `ModelError` and does not write. This function does not write pack files, claim files, or `curbpack.json`. `app/server.py` delegates with `_documents_model(ws, query)`. The URL, the `?document=` branch, and the POST handlers stayed in `app/server.py`. `documents_page` stayed in `requirements/ui/pages.py`. No `studio/` directory. |
| Move | Not started. File is not under `studio/`. |
| Separate | Not started. No domain logic was rewritten. |
| Boundary | Not applicable. No Packs v2 or Pydantic change. |
| HTTP | Not started. Old `ThreadingHTTPServer` still serves GET `/requirements`. |
| UI | Not started. `documents_page` is still the Python page. |
| Gate | Focused: `.venv/bin/python -m unittest tests.test_cover_navigation tests.test_sys03_door tests.test_requirements_export tests.test_requirements_ui`. 50 tests, OK, 16.784s. Exit code 0. Then `make test`: **Summary: 417 PASS, 0 FAIL**, exit code 0, about 85 seconds. No skip summary was printed. This run did not execute `make cicd`, `make package`, `make package-studio`, `make package-curbcheck`, or `tests/cs/`. |
| Checkpoint | The later local commit on `daniel/post-pilot-fixes-1` that adds this section. The hash is not written here; a commit cannot record itself. |
| Review | Two independent reads of `git diff HEAD`. The first found no Critical findings and one Important finding: the record said the view-model writes no files, while a query that names a repo still writes `open-repo.json` through `_sync_open_repo`. That disclosure is now in the behavior row and the Extract cell. The same review's Minor notes are applied: the definition moved and `app/server.py` imports it, and the Pack catalogue rollup says this view-model is extracted. The second read found no Critical or Important findings. Its note is applied: the write happens when the named id is already registered. An unknown id raises `ModelError` and does not write. |

The definition of `_documents_model` moved to `app/documents_model.py`. `app/server.py` imports it, and `Handler._get` calls it.

## MIG-09 — extract the requirement editor GET model and save

**Status:** extract gate passed. Move, separate, Pydantic, FastAPI, and TypeScript are not this step.

| Field | Record |
| --- | --- |
| Identifier | Requirement editor. GET `/requirements/requirement/{id}` and POST that saves the form. Sign is `/requirements/requirement/{id}/sign` and is not this step. Try-discovery is not this step. |
| Baseline | Parent revision `955ed68477c7d93b3af0dba603f0e8a8b377c406`. GET model was `app/server.py` `_editor_model`. POST called `_save_requirement_form` and redirected with `saved=1`. |
| Extract | `app/requirement_editor.py` `_editor_model`, `_editor_message`, `_save_requirement_form`, and `_edits_from_form`. Same return values and the same calls, apart from importing `_open_requirement`, `_pack_query`, and `_lines` from `app.server` when those functions run. `_open_requirement` stays for try-discovery and sign. `_pack_query` stays for the sign, try-discovery, and save redirects, `_repo_pack_copy_model`, and `_requirement_editor_for_error`. `_lines` stays for the demo `edits_for_requirement`. GET does not write files. POST writes the working requirement through `save_working_requirement` and does not sign. `app/server.py` still owns the URL, the `saved=1` redirect, sign, and try-discovery. `editor_page` stayed in `requirements/ui/pages.py`. `assign_reference_numbers` is no longer imported by `app/server.py`. The unused `import copy` left with `_edits_from_form`. No `studio/` directory. |
| Move | Not started. File is not under `studio/`. |
| Separate | Not started. No domain logic was rewritten. |
| Boundary | Not applicable. No Packs v2 or Pydantic change. |
| HTTP | Not started. Old `ThreadingHTTPServer` still serves the editor GET and POST. |
| UI | Not started. `editor_page` is still the Python page. |
| Gate | Focused: `.venv/bin/python -m unittest tests.test_requirements_ui tests.test_requirement_field_errors tests.test_try_discovery_ui tests.test_m1_requirement`. 16 tests, OK, 5.089s. Exit code 0. Then `make test`: **Summary: 417 PASS, 0 FAIL**, exit code 0, about 86 seconds. No skip summary was printed. This run did not execute `make cicd`, `make package`, `make package-studio`, `make package-curbcheck`, or `tests/cs/`. |
| Checkpoint | The later local commit on `daniel/post-pilot-fixes-1` that adds this section. The hash is not written here; a commit cannot record itself. |
| Review | Independent read of `git diff HEAD`. No Critical or Important findings. Before the commit, the unused `import copy` was removed, and the Extract cell names the remaining caller of each helper that stayed in `app/server.py`. |

The definitions moved to `app/requirement_editor.py`. `app/server.py` imports `_editor_model` and `_save_requirement_form`. `Handler._get` and `Handler._post` call them.

## MIG-10 — extract the Pack export GET model and write

**Status:** extract gate passed. Move, separate, Pydantic, FastAPI, and TypeScript are not this step.

| Field | Record |
| --- | --- |
| Identifier | Pack export. GET `/requirements/export` and POST that writes a directory. This does not publish a release. |
| Baseline | Parent revision `056705af581762f9e4155b3b34a8fcf45b2959bd`. GET model was `app/server.py` `_export_model`. POST called `_export_selected`. |
| Extract | `app/pack_export.py` `_export_model`, `_export_document`, and `_export_selected`. Same return values and the same calls, apart from importing `_formex_sources` from `app.server` when `_export_document` runs. `_formex_sources` stays because discover sources and the catalog model use it. Both GET and POST call `_export_document`, so both seed `registered_sources.json` through `ensure_catalog` when that file is missing. POST also writes `destination/<pack-id>/` through `export_pack`. A destination conflict redirects and leaves the existing directory. `app/server.py` still owns the URL. `export_page` stayed in `requirements/ui/pages.py`. `export_pack` is no longer imported by `app/server.py`. No `studio/` directory. |
| Move | Not started. File is not under `studio/`. |
| Separate | Not started. No domain logic was rewritten. |
| Boundary | Not applicable. No Packs v2 or Pydantic change. |
| HTTP | Not started. Old `ThreadingHTTPServer` still serves GET and POST `/requirements/export`. |
| UI | Not started. `export_page` is still the Python page. |
| Gate | Focused: `.venv/bin/python -m unittest tests.test_requirements_export tests.test_cover_navigation tests.test_requirements_ui`. 33 tests, OK, 9.911s. Exit code 0. Then `make test`: **Summary: 417 PASS, 0 FAIL**, exit code 0, about 87 seconds. No skip summary was printed. This run did not execute `make cicd`, `make package`, `make package-studio`, `make package-curbcheck`, or `tests/cs/`. |
| Checkpoint | The later local commit on `daniel/post-pilot-fixes-1` that adds this section. The hash is not written here; a commit cannot record itself. |
| Review | Independent read of `git diff HEAD`. No Critical or Important findings. Before the commit, the catalogue rollup no longer says export is not started, and the catalog seed is recorded on both GET and POST. |

The definitions moved to `app/pack_export.py`. `app/server.py` imports `_export_model` and `_export_selected`. `Handler._get` and `Handler._post` call them.

## Stop

MIG-10 stops here. The next single slice is extract-review GET/POST. It is not started.
