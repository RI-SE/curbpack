# Review pilot integration plan

> **For agentic workers:** Execute one small task at a time under `poc2/AGENTS.md`. This plan is not `REQUIREMENTS_IMPLEMENTATION_PLAN.md`. Do not start Requirements Task 21 from here. Do not edit any `ARCHITECTURE.md`.

**Goal:** Finish the agreed Claims → Checks → Compile → Review pilot: Review opens existing Discovery, the person adds Claims, explicitly retires the old Claim, reruns Checks, and signs the Claim and the report as separate actions; a signed report survives a later Check run and is not replaced without confirmation.

**Architecture:** Packs v2 stays the only persistent domain model. Discovery, Checks, and Claim sealing stay the functions that already exist. Compile and final review stay in `poc2/review/compile.py`. The HTTP entry only routes. The durable report path is the conventional product-repo file named by `poc2/review/ARCHITECTURE.md`. Git history, after the user commits, is the earlier-report record. PoC2 does not commit, tag, push, or create a branch.

**Tech Stack:** Python 3, existing `poc2/common` validation and Ed25519 signing, `unittest` from `poc2/`, `poc2/app/server.py`.

## Global Constraints

- Do not edit Packs v2 or any `ARCHITECTURE.md`.
- Do not add a discovery engine, checker, history store, report index, or second Claim/Requirement model.
- Do not commit, tag, push, or manage branches from an application operation.
- UI renders and collects input. Compile, confirmation, and signature rules stay in ordinary functions.
- Do not import or modify `poc/`.
- Local commits of coherent verified steps only. Do not include unrelated dirty files (`poc/data/`, zip archives, `daniel/`, `docs/superpowers/`).

## Configuration conflict (stopped)

`docs/arch/ARCHITECTURE.md` says deployment configuration, outside Packs v2, tells the process where Pack directories are and which product-repo path receives the durable report, and that a later named setting must extend that existing configuration explicitly.

`validate_curbpack_config` allows only `packs`, `exclude_requirements`, `requirements`, and `hunt`. There is no existing named setting for a report path or a Pack directory. Adding one would invent a configuration field the contracts do not define.

This plan does not add that setting.

What the contracts already allow, and this plan does:

- The report path is an argument. The conventional durable file is `<product-repo>/docs/reports/review-report.json` (`poc2/review/ARCHITECTURE.md`).
- The Check run result stays `<product-repo>/.curbpack/run-result.json`.
- `run_repository(repo, packs_root)` already keeps the product repository and the Pack directory apart. `Workspace.packs` and `Workspace.repo` stay separate directories.
- `curbpack.json` continues to name Pack ids. Pack `version` stays on `pack.json` and on `run_result.packs`. This plan does not add a version field to `curbpack.json`.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan state | IN PROGRESS. Implementation of Tasks 1–3 is in the tree. This plan is not Done. Do not move it to `impl/pilot/`. |
| Current phase/task | Stop for independent review. |
| Last completed task | Task 2 and the Review regression. Opening Review does not write. `POST /review/compile` writes `docs/reports/review-report.json`. Replacing that file requires `confirm=yes` and does not copy `decision`. A later Check leaves the file. The page and the cover show `same_run`. |
| Last verified local commit | Task 1 is `c105ab52c8a1ac512d9914292b9bce9a2cb78ed6`. Task 2 is `56892d0d0b0798424f8ab60845f08ca06af3f4f6`. |
| Uncommitted files | None for this plan after that commit. Unrelated and not part of this plan: `poc/data/**`, `daniel/`, `docs/superpowers/specs/2026-10-02-curbpack-scan-design.md`, `poc2.zip`, `poc2 2.zip`, `poc/data/step2_discover/feedback/cra-vii__European-Parliament-MCP-Server.json`. |
| Last tests and result | `cd poc2 && .venv/bin/python -m unittest tests.test_review_report_kept tests.test_review_discover_again tests.test_review_replace_flow tests.test_review_coverage tests.test_review_coverage_ui tests.test_ui_smoke tests.test_review_compile tests.test_pilot_pack_selection tests.test_e2e_annex_vii tests.test_claim_workflow` — PASS, 25 tests, outside the sandbox. The two `ModelError` tracebacks in that run are the refused decision-before-compile and unconfirmed replace. `cd poc2 && .venv/bin/python -m unittest discover -s tests` — 165 tests, FAILED (failures=1, errors=1 on the first run; the error was a different discover-job test on the second run). Stable failure: `test_requirements_ui.RequirementsUiTest.test_catalog_edit_sign_publish_and_extract` looks for `title="MUST, SHOULD, or MAY…"` and the editor uses `aria-label`. That file is not in this diff. The discover-job `invalid JSON` error did not repeat on the same test and the discover-to-claim test passed alone. Browser: `http://127.0.0.1:8771/review` showed `not saved` before any file existed; after `POST /review/compile` the page showed the unsigned reading, `same run: yes`, and the replace checkbox, and the file was `docs/reports/review-report.json`. A later Check after the evidence changed left the decision in place and the page said `same run: no. This saved report is an older run.` `POST /review/compile` without `confirm` returned HTTP 400 and kept the decision. `POST /review/compile` with `confirm=yes` dropped `decision`. The cover then said `Report: review report verifiable no. same run: yes.` Button clicks in the browser were blocked; the pages were loaded and the form routes were posted. |
| Active blocker/decision | No named configuration field for a report path. Use `docs/reports/review-report.json`. Do not invent a setting. The full suite is not green because of the Requirements editor assertion above. That is outside this plan. |
| **Exact next action** | Independent review of this plan under `policies/review.md`. Do not move this file to `impl/pilot/`. Do not start Requirements Task 21. Do not push. |

## Tasks

### Task 1: Report object matches the Review contract

**Files:** `poc2/review/compile.py`, `poc2/tests/test_review_compile.py`, callers of `compile_report` that pass `packs=`.

- [x] `compile_report(run_result, requirements, claims)` embeds Claims in run-row order and the Requirements those Claims name, in first-seen order. It copies `run_result`. It omits top-level `decision`, `signed`, `git_note`, `limits`, and `packs`.
- [x] A missing Claim for a row, or a Claim digest that differs from the row, raises `ModelError` and does not write.
- [x] `validate_report` rejects unknown keys, including `compliant` and `meets_cra`.
- [x] `write_report` / `load_report` validate. `same_run` compares the embedded run result with a loaded run result. `worktree_sentence` is page copy, not a stored field.
- [x] `replace_saved_report` refuses to replace an existing file unless `confirm` is true, and the new report has no copied `decision`.
- [x] `save_report_decision` and `save_report_signature` require an existing file and leave it unchanged when signing or validation fails.
- [x] Update `test_e2e_annex_vii` and `test_claim_workflow` to the new report shape. Do not weaken their seal checks.

**Test:** `cd poc2 && .venv/bin/python -m unittest tests.test_review_compile tests.test_e2e_annex_vii tests.test_claim_workflow tests.test_review_report_kept`

### Task 2: Confirmed Compile, previous run, conventional path

**Files:** `poc2/app/server.py`, `poc2/app/pages.py`, `poc2/workflow.py`, review HTTP tests.

- [x] `Workspace.report_path` and `workflow.snapshot` use `docs/reports/review-report.json`. The run result path stays `.curbpack/run-result.json`. No second report file is written.
- [x] Opening Review with no file shows a preview and does not write. The reading says `not saved`.
- [x] `POST /review/compile` is the write. Replacing an existing file requires `confirm=yes`. The new file is unsigned and has no `decision`.
- [x] `POST /review` and `POST /review/sign` require the saved file. They do not call `run_and_write`.
- [x] The page shows `same_run`, the worktree sentence, the two standing sentences, and selected Requirements that have no row as not checked.
- [x] A Check run still does not delete or rewrite the report. Compile and sign do not create a Git commit.
- [x] The cover shows whether a report is absent, or the report reading and whether `same_run` is true.

**Test:** `cd poc2 && .venv/bin/python -m unittest tests.test_review_report_kept tests.test_review_discover_again tests.test_review_replace_flow tests.test_review_coverage tests.test_review_coverage_ui tests.test_ui_smoke tests.test_review_compile`

### Task 3: Regression and stop for review

- [x] `cd poc2 && .venv/bin/python -m unittest discover -s tests` — 165 tests. Not green. See the checkpoint. The stable failure is the Requirements editor `title` assertion, outside this diff.
- [x] Exercise Review in the browser: preview does not write; compile writes `docs/reports/review-report.json`; a later Check leaves that file; compile without confirmation leaves it; compile with confirmation replaces it without the old decision. Pages were loaded. The form posts were the HTTP routes. Button clicks were blocked.
- [x] Update this checkpoint with commands, results, and the commit hash.
- [ ] Stop for independent review. Do not move this file to `impl/pilot/`. Do not start Requirements Task 21.
