# EP-02 — Migration coverage and verification

**Source inspected:** `curbpack-review(1).zip` (pilot snapshot); route inventory below is extracted from `app/server.py`. This is a migration checklist, **not proof of test success**. No PoC source was supplied for this review.

## Required migration coverage

**Rule:** Each row must have a destination, migrated behavior, passing tests of the new call path, and no active callers into the old one. Existing test names are *candidates for reuse*, not evidence they currently pass or exercise the new FastAPI/TypeScript stack. Record migration status in this table rather than writing another planning document.

| Functional area | Existing implementation | New owner | Existing test candidates | Must verify after migration | Status |
| --- | --- | --- | --- | --- | --- |
| Application shell / workspace / project selection | `app/server.py; app/project_selector.py; app/pages.py` | `studio/app.py; subsystem routes and shell` | `test_project_page.py; test_pilot_pack_selection.py; test_sys03_door.py; test_cover_navigation.py` | Open/select project, navigate, reject invalid/no open project, keep workspace state | NOT VERIFIED |
| Pack catalogue / source selection | `requirements/catalog.py; requirements/ui/pages.py; app/server.py` | `studio/pack/` | `test_requirements_catalog.py; test_requirements_ui.py` | Catalogue, source selection, pack sections, metadata editing; verify response and persistence | NOT VERIFIED |
| Requirement extraction and jobs | `requirements/extract/; requirements/jobs.py; app/server.py` | `studio/pack/impl/ and router.py; pages/extract/` | `test_requirements_extract.py; test_requirements_jobs.py; test_revise_loop.py; test_e2e_annex_vii.py` | Start/status/abort; parse inputs; inspect, revise, accept; preserve traceability and errors | NOT VERIFIED |
| Formex / CRA adapters | `requirements/extract/formex/` | `studio/pack/impl/` | `test_formex_inventory.py; test_formex_provisions_cra.py; test_xml_adapters.py; test_cra_vii_compare.py` | Coverage of provisions, correct citations and no dropped source sections | NOT VERIFIED |
| Requirement editing and signing | `requirements/editing.py; requirements/workspace.py; app/server.py` | `studio/pack/` | `test_m1_requirement.py; test_requirement_field_errors.py; test_requirements_ui.py; test_requirements_publish.py` | Edit, invalid input, save/reload, signing and invalidation | NOT VERIFIED |
| Pack lifecycle / working copies / publish | `requirements/workspace.py; common/signing.py; app/server.py` | `studio/pack/` | `test_requirements_publish.py; test_release_publish.py; test_requirements_export.py; test_pilot_pack_selection.py` | Import, copy, edit, publish versions; preserve origin/signing/Packs v2 on disk | NOT VERIFIED |
| Comparison / consolidation / export | `requirements/compare.py; requirements/consolidate.py; app/server.py` | `studio/pack/` | `test_requirements_compare.py; test_requirements_consolidate.py; test_requirements_export.py` | Diff/preview, explicit apply, export contents with same source references | NOT VERIFIED |
| Claims and binding | `claims/bind.py; claims/ui/; app/server.py` | `studio/claim/` | `test_claim_workflow.py; test_claims_binding_ui.py; test_m3_claims.py` | Create/edit/retire/sign/bind with correct requirement and pack; invalid selection fails | NOT VERIFIED |
| Discovery and user choice | `discovery/; claims/ui/researcher.py; claims/ui/pages.py; app/server.py` | `studio/claim/impl/ and pages/discovery/` | `test_discover_browse.py; test_discover_repos.py; test_discover_feedback.py; test_discover_claims_ui.py; test_m2_discovery.py` | Candidates, browse, jobs, feedback; explicit user decision before claim changes | NOT VERIFIED |
| Try-discovery / hints | `requirements/ui/try_discovery.py; app/server.py` | `studio/pack/ and studio/claim/ (decide owner by actual operation)` | `test_try_discovery_ui.py; test_discovery_assess.py; test_requirements_ui.py` | Preserve per-requirement refinement, preview/apply or discard; do not alter legal interpretation | NOT VERIFIED |
| Check registry and tool CLI | `checks/available_checks.json; checks/commands.py; checks/dispatch.py; checks/__main__.py; checks/bin/` | `curbcheck/api.py; curbcheck/cli.py; curbcheck/impl/; curbcheck/checks/` | `test_check_dispatch.py; test_chk07_curbcheck.py; test_curbcheck_catalogue.py; test_git_checks.py; test_curbcheck_package.py` | Invoke registered checks, parameter schema, deterministic results, status/exit codes, CLI and package | NOT VERIFIED |
| Check configuration and run from Studio | `app/server.py; checks/run.py; checks/defaults.py` | `studio/check/router.py and pages/ -> curbcheck/api.py` | `test_check_editor.py; test_chk08_studio.py; test_curbcheck_action.py; test_m4_checks.py` | Set options, run against selected repo, preserve run-result JSON; no duplicated engine | NOT VERIFIED |
| Review rendering / decisions / evidence | `review/present.py; review/view_html.py; claims/ui/coverage.py; app/server.py` | `studio/review/` | `test_rev03_review.py; test_rev03_review_render.py; test_review_replace_flow.py; test_review_report_kept.py; test_review_discover_again.py` | View results and evidence; fail/skip reasons, add/delete explicit, report never silently overwritten | NOT VERIFIED |
| Compile reports, PDF and sealing | `review/compile.py; review/gitseal.py; compile/pdf.py; compile/cli.py; app/server.py` | `studio/compile/ for report assembly; studio/review/ for review decisions` | `test_review_compile.py; test_compile_pdf.py; test_chk08_studio.py; test_rev03_review.py` | JSON/PDF artifacts, dated filenames, signed review status and preservation; decide signing responsibility explicitly | NOT VERIFIED |
| Shared data, paths, security | `common/; data/; app/project_selector.py` | `models/ + subsystem impl/; studio/authentication/ and authorization/ where applicable` | `test_jsonio.py; test_delivery.py; test_requirements_publish.py` | Preserve path confinement, signatures, files on disk, response validation; add direct API auth tests for new boundary | NOT VERIFIED |
| Installation/build/CLI/CI | `Makefile; scripts/; testing/; .github/workflows/; app/__main__.py; checks/__main__.py` | `Update entrypoints and imports in place; no new build system` | `test_delivery.py; test_installers.py; test_curbcheck_package.py; test_stop_app.py` | make start/test/package, native build smoke, cli exits and entrypoints after moves | NOT VERIFIED |
| System journeys and missing PoC parity | `docs/test/; tests/system/; tests/Review_ACCEPTANCE_SCENARIOS.md` | `cross-cutting` | `test_ui_smoke.py; test_e2e_annex_vii.py; test_review_replace_flow.py; test_sys03_door.py` | Run actual UI->REST journey; compare PoC if provided; unknown parity remains explicitly unverified | NOT VERIFIED |

## Existing HTTP surfaces in the pilot

These are literal path predicates extracted from the pilot handlers; a prefix ending `*` denotes dynamic routes. They are an **inventory of legacy behavior**, not a specification of final REST URL naming. Some predicates are handled outside the generic dispatcher. Verify real HTTP methods, request types, responses and consumers before replacing each route.

| Handler | Existing paths and prefixes |
| --- | --- |
| GET | `/`, `/abort*`, `/check`, `/claims`, `/discover`, `/discover/browse`, `/discover/jobs/*`, `/discover/repo`, `/project`, `/requirement`, `/requirements`, `/requirements/compare`, `/requirements/consolidate`, `/requirements/copy`, `/requirements/export`, `/requirements/extract/review`, `/requirements/inspect`, `/requirements/jobs/*`, `/requirements/publish`, `/requirements/requirement/*`, `/requirements/try-discovery/jobs/*`, `/review`, `/scaffold`, `/studio`, `/try-discovery/file*` |
| POST | `/abort*`, `/check`, `/claims`, `/claims/*`, `/discover/jobs/*`, `/discover/repos`, `/discover/run`, `/prepare`, `/project`, `/publish`, `/requirement`, `/requirements/catalog`, `/requirements/compare/apply`, `/requirements/consolidate/apply`, `/requirements/curbpack`, `/requirements/documents`, `/requirements/export`, `/requirements/extract`, `/requirements/extract/review`, `/requirements/jobs/*`, `/requirements/publish`, `/requirements/requirement/*`, `/requirements/seal`, `/requirements/select`, `/requirements/source`, `/requirements/start-empty`, `/retire*`, `/review`, `/review/compile`, `/review/sign`, `/scaffold`, `/seal-pack`, `/select-pack`, `/sign*`, `/studio`, `/try-discovery*` |

## Evidence for accepting each migrated feature

1. Baseline: record the current pilot test(s), a representative request/input, the observed output and any known failure **before** moving the behavior.
2. Implementation: confirm real TypeScript page → owning Studio REST router → explicit typed Python arguments → domain implementation. For Checks: Studio router → curbcheck Python API → engine. CLI uses the same engine.
3. API: test success and invalid request (Pydantic 422), plus relevant permission/authorization enforcement on **direct** HTTP requests (not just UI). Ensure error responses and status codes are intentional.
4. Domain: test implementation directly without importing FastAPI. Test persistent file formats, relative paths, signatures and non-happy paths with real fixtures where applicable.
5. UI: exercise an actual user interaction via browser/test client so a rendered page **cannot pass** if REST wiring is missing; verify both returned state and persistent result.
6. Regression: run pre-existing relevant tests after adaptation and an end-to-end flow spanning Pack → Claim/Discovery → Check → Compile → Review. Capture failures, do not mark complete on mocks alone.
7. Completion: ensure no live route or navigation still depends on old `app/server.py`, `app/pages.py`, `requirements/ui/` or `claims/ui/`; compatibility shims must be explicitly listed and temporary, not hidden.
8. Preserve current CLI, native packaging, `Makefile` target behavior, external input/output formats and signature semantics. No new functionality is implied by this migration.

## Not verified by this inventory

- Current test pass/fail and runtime behavior have not been executed in this audit.
- Functional parity against the **original PoC** cannot be established without the PoC snapshot or recorded observations; do not use the pilot as proof that lost features are present.
- There is no demonstrated TypeScript browser test suite or full new REST API coverage yet; these must be built as the corresponding feature is migrated, reusing existing fixture assertions.
- The authentication and authorization target is an architecture decision; current pilot endpoints are not proof that OIDC, roles, certificates or a SQLite authorization store already exist.
