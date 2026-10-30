# REV-03 — Review run results by Requirement

## Summary

- **Story:** `docs/agile/epics/01-pack-editor/stories/REV-03-Review-enhancements.md`
- **Goal:** A reviewer opens one curbcheck run result or one compiled review report for the repository chosen on the shared door, reviews Claims grouped by Requirement, records a `decision`, and seals that report. Run results stay in `results_dir`. Review reports stay in `reports_dir`. `signed` is not approval. `skipped` is not pass.
- **Scope / exclusions:** Scenarios 1–42 and 10a, 11a, 35a, 37a in the story. No new Packs v2 field, no second report schema, no change to `compile_report` / `record_decision` / `sign_report` / `read_signature` / `read_digest` / `git_commit_signature` shapes. Do not move the page to `review/ui/` (EP-02). Do not add scored-excerpt highlighting, a coverage tool, registry path metadata, inline Check editing, automatic curbcheck rerun, or automatic Claim replace/delete. Keep the signature appendix and the existing "selected Requirements were not checked" line; do not expand them into a completeness comparison. Leave `review/ARCHITECTURE.md`'s single-file `docs/reports/review-report.json` paragraph stale; do not restore replace-after-confirm (Decision D1).
- **Baseline:** Branch `daniel/pilot-work` at `84682d68a6762ff59efb92b77cf66450e0e05c08`. The story file is already staged (`A docs/agile/epics/01-pack-editor/stories/REV-03-Review-enhancements.md`). Do not reset it, and do not put it in a REV-03 commit unless the maintainer asks. Outside the sandbox, `python3 -m unittest tests.test_review_compile tests.test_review_report_kept tests.test_review_discover_again tests.test_review_replace_flow tests.test_review_coverage_ui tests.test_ui_smoke` — Ran 16 tests, OK. The same command inside the sandbox errors in `prepare_demo` → `git init -b main` (4 errors). That sandbox failure is pre-existing. Review today: `repo_config_panel(..., show=("config", "results", "reports"))` hides Packs and Claims paths; GET `/review` with no `report` calls `compile_report` on the latest run result and fails when a Claim file is missing or the digest differs; POST `/review/compile` also takes that latest file; Claims render as a flat list; the follow-up control says "Discover again"; Check does not link to Review with `result=`.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | DONE |
| Approved by | Maintainer, 2026-10-29. Plan approved as written, including D1 dated reports and no compile preview. |
| Current task | DONE |
| Last completed task | Task 7 |
| Last verified tests | 2026-10-30 outside sandbox: `python3 -m unittest tests.test_rev03_review tests.test_review_compile tests.test_review_report_kept tests.test_sys03_door` — Ran 66 tests, OK. |
| Last checkpoint commit | `07d418d` |
| Requirements | Story scenarios in `REV-03-Review-enhancements.md`. Plan rows REV-R01–REV-R10 are traceability aliases for those scenarios. No new `docs/req/` file. |
| Packs v2 | `docs/reference/packs2.md` and `docs/reference/workspace.md` at `84682d68a6762ff59efb92b77cf66450e0e05c08`. This plan edits neither. Report keys stay `run_result`, `requirements`, `claims`, `appendix`, optional `decision`, optional `signed`. `decision` stays the reviewer's own words. |
| Blockers | None |
| **Exact next action** | No further implementation. Story complete at `impl/REV-03.md`. |

## Requirements and acceptance mapping

The story already states the behavior as Given/When/Then. These ids are only so this plan can name a row. They are not new derived requirements.

| Requirement ID | Story | Test / observed evidence | Status |
| --- | --- | --- | --- |
| REV-R01 | REV-03 scenarios 1, 2, 38 | `tests/test_rev03_review.py` | Task 1 verified |
| REV-R02 | REV-03 scenarios 3, 4, 5, 37a, 39, 40, 41, 42 | `tests/test_rev03_review.py` | Task 1 verified |
| REV-R03 | REV-03 scenarios 7, 8, 9, 11, 11a, 23 | `tests/test_rev03_review.py` | Task 2 verified; Task 3 when the run result is embedded |
| REV-R04 | REV-03 scenarios 12, 13, 14, 15, 16 | `tests/test_rev03_review.py` | Task 2 verified; scenarios 12–14 also Task 3; scenario 16 in Tasks 5 and 6 |
| REV-R05 | REV-03 scenarios 10a, 21, 22 | `tests/test_rev03_review.py` | Task 2 verified; Task 3 for the embedded run |
| REV-R06 | REV-03 scenarios 6, 10, 37 | `tests/test_rev03_review.py` | Task 3 verified |
| REV-R07 | REV-03 scenarios 17, 18, 19, 20, 36 | `tests/test_rev03_review.py` | Task 4 verified |
| REV-R08 | REV-03 scenarios 24, 25, 26, 27, 28 | `tests/test_rev03_review.py` | Task 5 verified |
| REV-R09 | REV-03 scenarios 29, 30, 31, 32 | `tests/test_rev03_review.py` | Task 6 verified |
| REV-R10 | REV-03 scenarios 33, 34, 35, 35a | `tests/test_rev03_review.py` | Task 7 verified |

## Decisions

**D1 — many dated reports, no overwrite, no compile preview on open.** `review/ARCHITECTURE.md` still says one file, `docs/reports/review-report.json`, replaced after confirmation, and that opening Review with no saved report shows an in-memory `compile_report` preview. `docs/reference/workspace.md` and REV-03 scenario 33 say `<reports_dir>/review-report_<UTC>.json` and "not overwrite an earlier review report". Scenario 5 says opening a run result starts a review and does not create a report until Compile. SYS-03 Task 6 already writes the dated file and currently previews through `compile_report`. Proposed resolution: keep the dated files. Compile of a selected run result creates a new file. It does not replace an older report and does not ask to replace one. GET of a run result does not call `compile_report`. Keep `worktree_sentence` and the two standing sentences `NOT_A_LEGAL_CONCLUSION` and `NO_CRA_FIELD` on the page. Do not edit the architecture document in this story. Status: approved with this plan, 2026-10-29. Not a second schema.

**D2 — seal summary labels.** The story names `Unsigned`, `Verification unavailable`, `Untrusted signer`, and `Invalid seal`. `read_digest` and `git_commit_signature` do not emit those four strings. They emit the sentences and Git status codes below. This story forbids changing the seal contract. Display mapping, labels only, existing `reason` still shown with the five facts:

| Existing reading | Label | Forces the Requirement open |
| --- | --- | --- |
| `read_signature` / no Git seal: reason starts "No signed block and no signed Git commit" | Unsigned | no |
| reason starts "The certificate for name is not available" | Verification unavailable | no |
| Git `%G?` is `E` | Verification unavailable | no |
| reason is "The certificate does not verify the signature, or name is not the identity on that certificate." | Invalid seal. Maintainer, 2026-10-29. This sentence is not Untrusted signer. | yes |
| Git `%G?` is `U` | Untrusted signer | no |
| reason starts "The current bytes are not the digest that was signed" | Invalid seal | yes |
| Git `%G?` is `B` | Invalid seal | yes |
| Git `%G?` is `X`, `Y`, or `R` | no new label; show the existing reason | no |

`Verification unavailable` and `Untrusted signer` do not by themselves open the Requirement. A valid seal does not open it either. The explicit-seal sentence and Git `%G?` `U` were decided by the maintainer on 2026-10-29. The other rows are this plan's mapping and are included in plan approval. Do not add a new reason string in `read_digest`. Task 4 implements this table.

**D6 — same presentation for an embedded run result.** Maintainer, 2026-10-29. When an embedded `run_result` is opened from a compiled review report, the same presentation as a raw run result applies: the run header is shown; the Claim digest is classified as unchanged or changed; `pass`, `fail`, and `skipped` control initial expansion by the same rules. The report's embedded objects and historical grouping stay authoritative for the history.

**D7 — Re-Discover after accepted evidence.** Maintainer, 2026-10-29. Accepted evidence goes through the ordinary Claim workflow, leaves the existing run result unchanged, and leaves the existing review report unchanged. The return to Review says that the current Claim has changed, and that a new curbcheck run is required for a new run result and thereafter a new review report.

**D3 — fixture file.** The story's acceptance fixture (13 Claims, 19 Checks) is not in the tree. Tests build the smallest run result, Claim, Requirement, and report that satisfy each scenario, including one failing Claim, one `skipped` Check with `detail`, one `exist` or `contents` Check with more than one path, and one `dep_ban` Check. If the maintainer later adds the 13-Claim file, one extra test can load it. Do not invent 13 Claims only to hit that count.

**D4 — expansion across navigation.** First paint follows the story's open/closed rules and puts no `expanded` query on the URL. A header click is a GET that sets `expanded` to the requirement ids that are open after the click, plus the selected `repo`, `result` or `report`. The file dialog and the Claims Editor return link carry that same query. No new Packs v2 field and no browser storage. "Inspect" has no separate Review route; do not add one. Scenario 16 is the file dialog and the Claims Editor round trip.

**D5 — directory text.** Show the five path fields with the shared panel, using the strings written in `curbpack.json` (`curbpack_file`, `packs_dir_value`, `claims_dir_value`, `results_dir_value`, `reports_dir_value`). That matches the current Check panel. Do not render host `Path` strings.

## Tasks

### Task 0 — approve this plan

**Inputs / contracts:** REV-03 story; `docs/reference/packs2.md` §2.6 and §3.1; `docs/reference/workspace.md` §2; `review/ARCHITECTURE.md` (storage paragraph is not followed, see D1); `review/compile.py`; `app/server.py` `_review_view` and POST `/review/compile`; `app/pages.py` `review_page`.
**Change files:** `plan/REV-03.md` only.
**Acceptance / stop:** maintainer approval recorded, including D2. No product code in this task.

- [x] Independent plan review completed.
- [x] Maintainer approved the plan, including D1 and D2.

### Task 1 — paths, two lists, and an explicit document

**Requirements:** REV-R01, REV-R02. Scenario 4's Check link is in this task.
**Files:** `app/pages.py` (`review_page` panel `show` becomes `("config", "packs", "claims", "results", "reports")`; Check page gains a link to Review for the run result just shown), `app/server.py` (`_review_view`, list helpers, POST `/review/compile` reads the posted result path), `tests/test_rev03_review.py` (new), `tests/test_sys03_door.py` (the widget Review section that expects a silent preview and a compile with no result path).
**Test first:** One repository with `curbpack.json`, two `run-result_*.json` files under `results_dir`, and two `review-report_*.json` files under `reports_dir`. GET `/review?repo=<id>` shows the five written path fields, lists the two run results as run results, lists the two reports as review reports, and does not call either a report a run result or the reverse. It does not open one of them by itself and it does not write a file. GET with `result=<one run result>` shows that file's Claim ids and writes nothing. GET with `report=<one report>` opens that report. Changing `repo` drops `result` and `report`. A `result` or `report` outside the matching directory, or a missing file, names the requested path and the expected type and does not show the other file's Claim id. Missing or invalid `curbpack.json` names `curbpack.json` and does not invent directories. An unusable Results directory is named and Reports is not listed in its place. An unusable Reports directory is named and Results is not written as a fallback. An empty Results directory says there is no run result and does not say the review passed. A listed file that is not JSON names that file and type and does not render the other document. Check's page, after a run, links to `/review` with that repo and that result path. POST compile without a selected result writes nothing.
**Validation:** `python3 -m unittest tests.test_rev03_review tests.test_sys03_door tests.test_review_compile tests.test_review_report_kept tests.test_review_discover_again tests.test_ui_smoke`
**Stop if:** listing or selecting would need a new `curbpack.json` key, or compile would overwrite an existing `review-report_*.json`.
**Already present, do not rebuild:** dated compile output and "no repository is chosen" when no repo is open. Update the SYS-03 widget assertions that currently require the latest run to appear on GET `/review?repo=widget` with no `result`, and that compile with only `repo_id`.

- [x] RED observed for the intended behavior (or existing PASS demonstrated).
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

### Task 2 — group a raw run result by the current Requirement

**Requirements:** REV-R03, REV-R04 except scenario 16, REV-R05.
**Files:** `review/present.py` (new, no HTML), `app/pages.py` (render the groups), `app/server.py` (pass current Claims and Requirements into the presenter instead of `compile_report` on GET), `tests/test_rev03_review.py`.
**Test first:** A raw run result with two Claims that share one current `requirement_id` renders one Requirement group. The Requirement id comes from the current Claim, not from parsing the Claim id. A Claim id with no current file is under an expanded heading `Unresolved Claims`, with its recorded Checks, and the page does not invent a Requirement or say the repository passes that Claim. A current Claim whose `requirement_id` does not resolve is in that same group, and the page shows that `requirement_id`. All-pass, no attention condition: the Requirement body is closed, and the header outside that body shows the Requirement id, a seal summary from the existing reading (`what`, `who`, `when`, `version`, `verifiable`, and `reason` when present), and a result summary. D2's four short labels are not required in this task. Any contained `fail`: the Requirement is open, each failed Claim or Check status uses the existing red class `pill-bad`, and `detail` is present. No `fail`, one `skipped`: open, the skipped status does not use `pill-bad` or `pill-ok`, the word pass is not used for it, and `detail` is shown. A header click GETs `expanded` set to the ids that should be open after the click. A follow-up GET with that same `expanded` value, omitting a Requirement that contains `fail`, renders that Requirement closed. The click does not change the run result file, any Claim file, or a report. Matching digest text says the Claim is unchanged since the Check run. A different digest says `Claim changed since Check`, opens the Requirement on first paint when `expanded` is absent, keeps the recorded statuses, and says a new curbcheck run is required. It also says the previous Requirement relationship cannot be established from the raw run result. The open Claim shows every recorded Check's `check`, `index`, `args`, `status`, and `detail` when present, including two paths on one Check. The run header shows `tool`, `tool_version`, `commit`, `worktree`, and each pack `id` and `version`. `worktree` `dirty` is visible, uses `worktree_sentence`, and is not a Check status. The page still contains `NOT_A_LEGAL_CONCLUSION` and `NO_CRA_FIELD`. `pass`, `fail`, and `skipped` stay distinct.
**Validation:** `python3 -m unittest tests.test_rev03_review tests.test_review_discover_again tests.test_ui_smoke`
**Stop if:** grouping needs a Requirement id derived from the Claim id string, or GET starts writing a report.
**Note:** The header seal summary in this task is the existing reading, visible while the body is closed. D2's short labels and the invalid-seal expansion rule are Task 4. Until then an all-pass Requirement stays closed when its only seal condition is an unsigned reading (scenario 20: `Unsigned` does not by itself force expansion). Missing-path expansion is Task 5. A changed Requirement on a compiled report is Task 3.

- [x] RED observed for the intended behavior (or existing PASS demonstrated).
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

### Task 3 — open a compiled report without regrouping it

**Requirements:** REV-R06, and D6: REV-R03, REV-R04 scenarios 12–14, and REV-R05 for the embedded `run_result`.
**Files:** `review/present.py`, `app/pages.py`, `app/server.py`, `tests/test_rev03_review.py`.
**Test first:** A report file embeds Requirement R-old, a Claim under R-old, a `decision`, and a `run_result`. The current Claim file with the same id has `requirement_id` R-new. With no `expanded` query, GET `report=<that file>` groups the Claim under R-old, the R-old group is open, the visible text says the current relationship changed, and it says a new curbcheck run is required. The historical result is not under R-new. The embedded `decision` is shown. Embedded Claim `args` are not replaced by the current file. The same GET shows the embedded run header: `tool`, `tool_version`, `commit`, `worktree`, and each pack `id` and `version`. `worktree` `dirty` uses `worktree_sentence` and is not a Check status. The page contains `NOT_A_LEGAL_CONCLUSION` and `NO_CRA_FIELD`. Every recorded Check's `check`, `index`, `args`, `status`, and `detail` when present are shown from the embedded `run_result`, including two paths on one Check. A current digest equal to that embedded digest says the Claim is unchanged since the Check run. A current digest that differs says `Claim changed since Check`, keeps the recorded statuses, and opens the historical Requirement on first paint. An embedded all-pass run with a matching digest and no attention condition renders that Requirement closed, with its id, seal summary, and result summary outside the body. An embedded `fail` opens that Requirement and uses `pill-bad`. No `fail` and one `skipped` opens it, and `skipped` does not use `pill-bad` or `pill-ok` and is not described as pass. A present `expanded` query is the full set of open Requirement ids and overrides those initial rules, including a `fail` group named by the query as closed. A second report with `signed` shows the seal reading and does not describe `signed` as approval. The current Claim file bytes and the report bytes are unchanged by the GET.
**Validation:** `python3 -m unittest tests.test_rev03_review tests.test_review_compile tests.test_review_report_kept`
**Stop if:** the page would write the current Claim back into the report, or would add a report field for the changed relationship.

- [x] RED observed for the intended behavior (or existing PASS demonstrated).
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

### Task 4 — seal summaries

**Requirements:** REV-R07.
**Files:** `review/present.py` (map an existing reading to the confirmed D2 label; call `read_signature`, `read_claim_signature`, `read_report_signature`, and `git_commit_signature` — do not edit those functions), `app/pages.py`, `tests/test_rev03_review.py`.
**Test first:** The Requirement header summary, still outside the collapsible body, uses the D2 label. A Claim summary is separate from that, from Check status, and from `decision`. The five facts stay on the page. Cases, using fixtures the existing signing helpers already accept: valid explicit `signed`; Claim with no `signed` and a Git commit `git_commit_signature` reports as good, and the page does not say Unsigned only because `signed` is absent; the displayed who is that reading's who, and a commit author string that differs from it is not labeled as the signer; certificate material absent; Git status `U` is labeled `Untrusted signer` and does not by itself open an all-pass Requirement; a reading whose reason is exactly `The certificate does not verify the signature, or name is not the identity on that certificate.` is labeled `Invalid seal`, is not labeled `Untrusted signer`, and opens the affected Requirement; explicit seal whose current bytes no longer match, so verification is not verifiable and the recorded `decision` text is still on the page; Check `fail` remains `fail` after the report is sealed. An invalid seal on a Requirement opens that Requirement. An invalid seal on a contained Claim opens that Requirement. An invalid seal on the review report opens every Requirement group, and the report summary stays outside those groups. Unsigned, Verification unavailable, and Untrusted signer do not by themselves open a group. A label that belongs on a closed all-pass header is still visible without opening the body.
**Validation:** `python3 -m unittest tests.test_rev03_review tests.test_review_compile`
**Stop if:** the test needs a new reason string inside `common/signing.py` or `review/gitseal.py`.

- [x] RED observed for the intended behavior (or existing PASS demonstrated).
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

### Task 5 — path adapter and file dialog

**Requirements:** REV-R08, REV-R04 scenario 16 for the file dialog.
**Files:** `review/present.py` (path list for `exist`, `contents`, and `dep_ban` only), `app/pages.py`, `app/server.py` (confined file read on the review GET; `file` query), `tests/test_rev03_review.py`.
**Test first:** `exist` with `args.paths` of two repo-relative paths renders both. `contents` with `args.path` renders that path. `contents` with `args.paths` of two paths renders both, and each path that exists is selectable. A path that exists is a control that GETs the same review with `file=<that path>` and shows the file text and the repo-relative path. Closing it (GET without `file`) still has the same `repo`, `result` or `report`, and `expanded`. A recognised path that is not in the repository now is marked missing, the Check `status` in the HTML is the recorded status, and on first paint with no `expanded` query the Requirement is open even when every recorded status is `pass`. `dep_ban` shows `package` and `banned_versions` and has no file link. An unknown `check` shows `args`, `status`, and `detail` and has no file link. A path that resolves outside the repository is called invalid and the response body does not contain a marker planted in that outside file. `expanded` is unchanged.
**Validation:** `python3 -m unittest tests.test_rev03_review`
**Stop if:** the adapter would treat `npm_dep_ban` / `manifest_dep_ban` as `dep_ban`, or would scrape arbitrary strings for paths. Those aliases stay unknown Checks for this story.

- [x] RED observed for the intended behavior (or existing PASS demonstrated).
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

### Task 6 — Edit the matched Check, and Re-Discover

**Requirements:** REV-R09, REV-R04 scenario 16 for the Claims Editor return.
**Files:** `app/pages.py`, `app/server.py` only if the Claims redirect must carry the review query back, `tests/test_rev03_review.py`, `tests/test_review_discover_again.py` (the visible control text becomes `Re-Discover`; keep the one-Requirement dialog and the assertion that the failed Claim stays on the page).
**Test first:** When the current Claim digest equals the run-result digest and `checks[index].check` equals the recorded `check`, the page offers Edit to the existing Claims Editor for that Claim, and the editor shows that current `check` and `args`. Review's HTML has no second inputs named for editing `check` or `args`. When the digest differs, or the index is past the current Checks, or the current `check` string differs, the recorded result remains, the page says the current Check cannot be matched safely, and there is no Edit control for that Check. Saving a change from the Claims Editor updates the current Claim file only. If that Claim had a seal, the old seal no longer verifies. The selected run result bytes and any review report bytes stay equal to what they were before the save. The return URL still has the same `repo`, document, and `expanded`, and the page says a new curbcheck run is required. Re-Discover opens the existing Discovery popup for that Claim's Requirement. Opening and closing it does not change the Claim file, the run result, or the report. The button text is `Re-Discover`. Accepting evidence uses the ordinary Claim write that Discovery already posts. After that write, the selected run-result file and the selected review-report file are byte-for-byte unchanged. The return to the same Review document says `The current Claim has changed.` and `A new curbcheck run is required for a new run result, and then a new review report.`
**Validation:** `python3 -m unittest tests.test_rev03_review tests.test_review_discover_again tests.test_review_replace_flow tests.test_claims_binding_ui`
**Stop if:** Edit would require a new Claims Editor route or a new Check editor inside Review.

- [x] RED observed for the intended behavior (or existing PASS demonstrated).
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

### Task 7 — Compile the selected run, then decision and seal

**Requirements:** REV-R10.
**Files:** `app/server.py` POST `/review/compile`, `/review`, `/review/sign`; `app/pages.py` only for the wording that distinguishes the decision from the seal; `tests/test_rev03_review.py`. `review/compile.py` stays the writer. Do not call `replace_saved_report`.
**Test first:** POST compile with the selected result path, when every run-result Claim digest matches a current Claim, writes a new `review-report_<UTC>.json` under `reports_dir`. The file embeds that `run_result` and has no `decision`. The run result file is unchanged. A second compile leaves the first report bytes unchanged. POST compile when one Claim file is missing, or the current digest differs, writes no report file and the error names that Claim id. The error does not embed the changed Claim. POST decision on the compiled report stores `decision` and does not change any Check `status`. The words may be an approval or a request for changes; the stored value is that text, not a new enum. POST review-sign then sets `signed` over the report including `decision`. The page says the report is sealed and does not say the decision became pass. A contained `fail` or `skipped` is still that status. `read_report_signature` is verifiable for that signer before a later byte change, and not verifiable after the covered bytes change. The decision text is still readable after that failed verification.
**Validation:** `python3 -m unittest tests.test_rev03_review tests.test_review_compile tests.test_review_report_kept tests.test_sys03_door`
**Stop if:** compile would accept a mismatched digest, overwrite a report, or encode the decision by editing a Check status.

- [x] RED observed for the intended behavior (or existing PASS demonstrated).
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

## Work log

- **2026-10-29 / Task 0:** Inspected the story, `review/ARCHITECTURE.md`, `review/compile.py`, `review/gitseal.py`, `common/signing.py` `read_digest`, `app/server.py` `_review_view` and the review POSTs, `app/pages.py` `review_page` / `_review_claim_row`, and `tests/test_sys03_door.py` widget Review section. No `docs/req/` row for REV-03. The 13-Claim fixture named in the story is not in the tree (D3). Baseline outside the sandbox: 16 review tests OK. Sandbox `git init` errors recorded and not treated as product failures. Wrote this plan. No product code.
- **2026-10-29 / Task 0 plan review:** Independent review Issues Found (`0e4e2030`). Fixed in this plan: collapsed Requirement keeps its seal summary outside the body (Task 2); a changed Requirement on a compiled report starts open and says a new run is required (Task 3); a missing recognised path opens the Requirement, and `contents.args.paths[]` is listed (Task 5); an unsafe Check match says it cannot be matched safely (Task 6). Folded the advisory notes into those tasks and into D1: `expanded` overrides the initial fail-open rule; report-level invalid seal opens every group; Git author is not the signer; a Claims Editor save clears the old seal and says a new run is required; GET does not preview through `compile_report`; `fail` uses existing `pill-bad`. No product code.
- **2026-10-29 / Task 0 re-review:** New reviewer Issues Found (`8b09718d`). Three blockers remain, so this plan is BLOCKED and there is no third review. (1) Scenarios 7, 12–14, 21, 22, and 23 also apply when the run result is opened through a compiled report; Task 3 does not lock them. (2) D2 must not label the existing explicit-seal failure sentence as Untrusted signer or leave that Requirement closed. (3) Scenario 32's accept-evidence path must leave the run result and report unchanged and say a new curbcheck run is required; Task 6 only locks open and close. Advisory, not applied: `expanded` is the full open set for every initial-open condition; the other run results stay selectable while one is open; a parseable but invalid document is scenario 42; the signature appendix and the unchecked-Requirements line come from an opened compiled report, not from a raw-run GET. No product code.
- **2026-10-29 / Task 0 maintainer:** The three blockers are decided and written into this revision. D6: an embedded `run_result` uses the same header, digest classification, and pass/fail/skipped expansion as a raw run; embedded objects and historical grouping stay authoritative. D2: the explicit-seal sentence is `Invalid seal` and opens the Requirement; Git `%G?` `U` stays `Untrusted signer` and does not. D7: accepted evidence uses the ordinary Claim write, leaves the run result and review report unchanged, and the return says `The current Claim has changed.` and `A new curbcheck run is required for a new run result, and then a new review report.` Plan status returned to DRAFT for a new review round. No product code.
- **2026-10-29 / Task 0 review:** New reviewer Approved (`d8931048`). No issues. Advisory, not applied: scenario 4 keeps other run results selectable while one is open; scenario 42 names a parseable but invalid document and is not rendered as complete; a present `expanded` query overrides every initial-open rule; Task 4 reads the seal of the object on screen, not today's Claim in place of an embedded seal; keep the signature appendix and the unchecked-Requirements line on an opened compiled report; Task 0 approval should name D1; a compiled report whose current Claim file is missing stays in its historical group and does not move to `Unresolved Claims`. Verified separately: POST `/review/compile` with only `repo_id` is in `tests/test_sys03_door.py`, `tests/test_chk08_studio.py`, `tests/test_ui_smoke.py`, `tests/test_review_replace_flow.py`, and `tests/test_review_report_kept.py`. `tests/test_review_compile.py` does not post that route. No product code.
- **2026-10-29 / Task 1 IMPL-START:** REV-R01 (scenarios 1, 2, 38) and REV-R02 (scenarios 3, 4, 5, 37a, 39, 40, 41, 42). Planned test `tests/test_rev03_review.py`. Expected files `app/pages.py`, `app/server.py`, `tests/test_sys03_door.py`. No product code yet.
- **2026-10-29 / Task 1 RED:** `python3 -m unittest tests.test_rev03_review` (outside sandbox) — Ran 10 tests, FAILED (failures=6, errors=3). The page hid Packs and Claims, opened the latest report, ignored a missing or foreign path, lacked `There is no run result.`, and had no Check link. Unusable directories and invalid `curbpack.json` returned HTTP 400. After the compile case was pointed at a real run, `test_compile_without_a_selected_run_result_writes_nothing` failed because POST `/review/compile` with only `repo_id` wrote `review-report_*.json`.
- **2026-10-29 / Task 1 GREEN:** `python3 -m unittest tests.test_rev03_review` — Ran 10 tests, OK. Validation `python3 -m unittest tests.test_rev03_review tests.test_sys03_door tests.test_review_compile tests.test_review_report_kept tests.test_review_discover_again tests.test_ui_smoke tests.test_chk08_studio tests.test_review_replace_flow` — Ran 46 tests, OK. The last two modules are the other compile callers that posted only `repo_id`.
- **2026-10-29 / Task 1 REVIEW-START:** Independent review of the uncommitted diff. No commit yet.
- **2026-10-29 / Task 1 review:** Independent review Issues Found (`69127475`). No Critical. Important, fixed in this step: a raw run result no longer renders the signature-appendix sentence or empty Requirement and source lines; `docs/reference/outputs.md` Compile and Open Review rows now say compile reads the posted path and Review opens only the requested document. `docs/reference/stable-contracts.md` at `0ae6ad6` is already an index and has no "latest report" row, so this step does not edit it. `review/ARCHITECTURE.md` stays unchanged by this step. Minor, not applied: an unselected Review card still says "No run result to compile."; the unusable-directory tests match the configured path string.
- **2026-10-29 / Task 1 re-review:** Approved (`168ada6d`). No Critical or Important findings. Minor, not applied: the same two notes, plus `docs/user-guides/developers.md` still describes compiling the latest run and opening the latest report. That guide is outside this step. `python3 -m unittest tests.test_rev03_review tests.test_sys03_door tests.test_review_compile tests.test_review_report_kept tests.test_review_discover_again tests.test_ui_smoke tests.test_chk08_studio tests.test_review_replace_flow` — Ran 46 tests, OK.
- **2026-10-29 / Task 2 RED:** `python3 -m unittest tests.test_rev03_review.ReviewGroupingTest` — Ran 6 tests, FAILED (failures=2, errors=4). The page had no Requirement groups and no `expanded` link.
- **2026-10-29 / Task 2 GREEN:** `python3 -m unittest tests.test_rev03_review tests.test_review_discover_again tests.test_ui_smoke` — Ran 18 tests, OK.
- **2026-10-29 / Task 2 REVIEW-START:** Independent review of the uncommitted diff. No commit yet.
- **2026-10-29 / Task 2 review:** Independent review Issues Found (`32cc09be`). No Critical. Important, fixed before the re-review: a failed Check uses `pill-bad` even when the Claim status is pass; the Requirement id, seal, and result summary are one `expanded` link.
- **2026-10-29 / Task 2 re-review:** Issues Found (`3e36edbc`). No Critical. One Important remains: `<summary>` can still toggle locally outside the anchor. No third review. After that report, the summary marker is hidden and only the anchor receives the click. `python3 -m unittest tests.test_rev03_review tests.test_review_discover_again tests.test_ui_smoke` — Ran 18 tests, OK. The fix is uncommitted and not re-reviewed. Task 2 is BLOCKED. Task 3 has not started.
- **2026-10-29 / Task 2 REVIEW-START:** Maintainer authorized a new review round for the header hit-target fix. No commit yet.
- **2026-10-29 / Task 2 review:** New independent review Approved (`e5b959cc`). No Critical or Important findings. Minor, not applied: keyboard activation of `<summary>` can still toggle `open` locally; the hit-target CSS is not asserted by a test. Outside sandbox validation — Ran 18 tests, OK.
- **2026-10-29 / Task 3 RED:** `python3 -m unittest tests.test_rev03_review.ReviewCompiledReportTest` — failed for flat Check results without historical R-old grouping.
- **2026-10-29 / Task 3 GREEN:** `python3 -m unittest tests.test_rev03_review tests.test_review_compile tests.test_review_report_kept` — Ran 32 tests, OK.
- **2026-10-29 / Task 3 REVIEW-START:** Independent review of the uncommitted diff. No commit yet.
- **2026-10-29 / Task 3 review:** Issues Found (`1f7e4ea3`). Important fixed: appendix restored on compiled report; Requirement move includes `Claim changed since Check` when digest differs.
- **2026-10-29 / Task 3 re-review:** Approved (`43d4a70f`). No Critical or Important. Minor, not applied: current Claim path isolation; appendix reason assertion.
- **2026-10-29 / Task 4 RED/GREEN:** D2 labels on existing readings; Git-before-Unsigned for Requirements and reports; claim seal facts stay in the closed header. Validation — Ran 35 tests, OK.
- **2026-10-29 / Task 4 review:** Issues Found (`73d0e6f5`). Important: scenario 19 stubbed `git_commit_signature`. Fixed with a real SSH-signed commit fixture (`_ssh_signed_commit`); author `Author Name`, `%GS` `CLAIM-KEY`, run header commit stays `abc123`.
- **2026-10-29 / Task 4 re-review:** Approved (`cab6bd75`). No Critical or Important. Minor, not applied: parse Git status from reason substrings; page tests for Claim `Invalid seal` and Git `U` closed all-pass. `python3 -m unittest tests.test_rev03_review tests.test_review_compile` — Ran 35 tests, OK.
- **2026-10-29 / Task 5 RED/GREEN:** Pilot path adapter for `exist`/`contents`/`dep_ban`, confined `file=` dialog, missing path opens all-pass. Validation — Ran 29 tests, OK.
- **2026-10-29 / Task 5 review:** Issues Found (`a9479f03`). Important fixed: closed fixtures create evidence files; contents probes stay beside path links.
- **2026-10-29 / Task 5 re-review:** Approved (`156180dd`). No Critical or Important. Minor, not applied: Close href / report file dialog assertion; alias and symlink assertions; resolve-then-reject for `..`. `python3 -m unittest tests.test_rev03_review` — Ran 29 tests, OK.
- **2026-10-29 / Task 6 RED/GREEN:** Edit when digest+check match; unsafe sentence otherwise; Re-Discover label; Claims `return_to` with digest-gated `claim_changed`; Discovery breakout helper. Validation — Ran 41 tests, OK.
- **2026-10-29 / Task 6 review:** Issues Found (`c2827b78`). Important: Discovery accept evidence did not return to Review; `claim_changed` on unchanged digest. Fixed in tree before re-review.
- **2026-10-29 / Task 6 re-review:** Issues Found (`77519acf`). Important remain: return_to dropped after Discovery navigation / Take / error pages; breakout script injection risk; scenario 32 not a full Discovery post acceptance test. No third review. Task 6 BLOCKED. Local follow-up edits after that re-review are unreviewed.
- **2026-10-30 / Task 6 REVIEW-START:** Maintainer authorized one additional review round for the three Important findings from `77519acf`. Follow-up fixes: return_to survives overview/file/vote/Take/check-error/create-error; breakout uses `_safe_review_return` plus JSON encoding; scenario 32 posts Discovery add+exist check, follows breakout, asserts D7 sentences and unchanged run/report/old Claim bytes. Validation — Ran 42 tests, OK. Independent review of the uncommitted Task 6 diff next.
- **2026-10-30 / Task 6 review:** Approved (`53a5710b`). No Critical or Important. The three `77519acf` findings are resolved. Minor, not applied: missing-file Discovery error page has no Back link with return_to; reject `#` in `_safe_review_return` so claim_changed cannot land in a fragment. `python3 -m unittest tests.test_rev03_review tests.test_review_discover_again tests.test_review_replace_flow tests.test_claims_binding_ui` — Ran 42 tests, OK.
- **2026-10-30 / Task 6 VERIFIED:** Checkpoint and local commit `bbdbb63` for Edit / Re-Discover / Discovery return_to / D7. Next: Task 7.
- **2026-10-30 / Task 7 IMPL-START:** REV-R10 (scenarios 33, 34, 35, 35a). Planned test class in `tests/test_rev03_review.py`. Expected files `app/server.py`, `app/pages.py` only if seal wording must change. `review/compile.py` stays the writer.
- **2026-10-30 / Task 7 RED:** `python3 -m unittest tests.test_rev03_review.ReviewCompileDecisionSealTest` — Ran 3 tests, FAILED (failures=1). Scenarios 33 and 34 already green through existing compile routes. Scenario 35a failed because the flash still said `Report signed.` instead of `Report sealed.`
- **2026-10-30 / Task 7 GREEN:** Flash after review-sign is `Report sealed.` Compile/decision/seal HTTP acceptance tests lock scenarios 33–35a. Validation — Ran 66 tests, OK. Independent review next.
- **2026-10-30 / Task 7 review:** Approved (`6d0a6ffe`). No Critical or Important. Minor, not applied: assert embedded Claim/Requirement ids on the compiled file; assert the original decision sentence on the sealed page before the tamper write; post-tamper readability need not reopen Review (covered by Task 4). `python3 -m unittest tests.test_rev03_review tests.test_review_compile tests.test_review_report_kept tests.test_sys03_door` — Ran 66 tests, OK.
- **2026-10-30 / Task 7 VERIFIED:** Checkpoint and local commit `07d418d` for compile / decision / seal. Story complete; move plan to `impl/`.
- **2026-10-30 / DONE:** All REV-R01–REV-R10 evidenced. No new Packs v2 fields. `review/ARCHITECTURE.md` left stale per D1. Unrelated dirty tree preserved.
