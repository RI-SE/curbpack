# FMT-01 — Format version on the saved JSON contracts

## Summary

A fresh context implements from this file alone. Do not implement from `docs/agile/epics/15-file-format-versions/stories/FMT-01-version-and-upgrade-chain.md`. That story still says decimal steps `1.0` / `1.1` / `1.2` and is updated in Task 6, after the code. Start at Task 1. One task at a time. Test first. Commit that task before the next. If the context runs out after Task 5, stop. Task 6 is documentation and can wait.

- **Story:** `docs/agile/epics/15-file-format-versions/stories/FMT-01-version-and-upgrade-chain.md` (draft, stale). Implementation follows this plan. The story is updated afterwards as documentation of what was built. It does not gate the code.
- **Goal:** Each saved JSON contract carries `format_version`. A missing number is version 0. Load returns version 1 in memory and reports which version was on disk. The file stays unchanged until an explicit save. A person who is already on a screen that saves that file can upgrade or cancel. Reading a sealed file does not ask and does not write.
- **Scope / exclusions:** The saved JSON contracts: `curbpack.json`, `pack.json`, a Requirement, a Claim, a run result and its files sidecar, `review_items.json` (including the working remedy fields and the sealed items file), the review report, and the remedy report JSON (`remedy-report_<stamp>.json`, plus the older `remedy-report.json` and `review-report_*.remedy.json` names of that same document). Remedy Markdown and PDF are renderings of the seal and are out. So are job files, try-run, feedback, catalog, repos, `source_adapter.json`, `llm.json`, `provisions.json`, `coverage.json`, and keys. No change to Pack release `version`, namespace, status, origin, or Claim binding meaning. No reference-product migration. No hand-edited version field. No new epic. EP-02 is out of scope.
- **Baseline:** Not run for this plan. HEAD when the plan was written: `3a2859c`. First implementation step records `python3 -m unittest` for the new tests and the seal, digest, and claim-load tests named in Task 1 and Task 2.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | APPROVED |
| Approved by | Maintainer, 2026-11-26. Implement Tasks 1-5 from this plan. Task 6 documents the story afterwards and is not a gate. |
| Current task | Task 4 — one upgrade-or-cancel dialog on screens that already save (IMPL-START) |
| Last completed task | Task 3 — one function per step, with the second step only in a test |
| Last verified tests | `python3 -m unittest tests.test_fmt01_chain tests.test_fmt01_load` → Ran 20 tests, OK. Full suite before the last runner tightening: `python3 -m unittest discover -s tests -p 'test_*.py'` → Ran 711 tests, FAILED (failures=1, errors=4). The failure is `test_review_flow` (`No module named 'reportlab'`). The four errors are `test_compile_pdf` and `test_remedy_report` (`pypdf`) and `test_review_deviations` and `test_review_retire` (`reportlab`). Second review: no Critical or Important findings. |
| Last checkpoint commit | This commit. Resolve with `git log -1 --format=%H -- plan/FMT-01.md`. |
| Requirements | Plan-local FMT-R01–FMT-R06 below. They become the FMT-01 story criteria. Do not add a `docs/req/` file. |
| Packs v2 | `docs/reference/packs2.md`. Task 1 added `format_version` and excluded it from the version digest and the pack directory digest. Task 2 loads version 1 in memory and writes the key only on save. `curbpack.json` is also `docs/reference/workspace.md` §2. Run result, review report, and remedy report are `docs/reference/outputs.md`. Review items are `docs/reference/studio-internal.md`. |
| Blockers | None |
| **Exact next action** | Task 4 IMPL-START. FMT-R03 and FMT-R06 dialog half. Write the upgrade-or-cancel page test and record RED before adding the prompt. |

## Requirements and acceptance mapping

| Requirement ID | Story | Test / observed evidence | Status |
| --- | --- | --- | --- |
| FMT-R01 | FMT-01 | A file of each saved JSON kind with no `format_version`, whose other fields match the current contract, loads as `format_version` 1. The file bytes are unchanged. `read_version` is 0 and `current_version` is 1. The kinds are `curbpack.json`, Pack, Requirement, Claim, run result, review items, review report, and remedy report. | DRAFT |
| FMT-R02 | FMT-01 | The production chain is the single step 0 → 1, and that step only adds `format_version` 1. The runner never skips. A test-only chain 3 → 4 then 4 → 5, given a document at 3, runs both functions and returns version 5 in memory. A document at 1 is rejected when that chain starts at 3. The file is unchanged. Those extra steps are not registered in production. Obsolete means a version is no longer written. Removing the ability to read it is a separate floor: below the floor the load is rejected. A missing step is a gap and is rejected, not jumped. | DRAFT |
| FMT-R03 | FMT-01 | Load does not write. Save writes the in-memory object, including `format_version` 1. Cancel leaves the file at the version that was read. | DRAFT |
| FMT-R04 | FMT-01 | `format_version` greater than 1, or not an integer, is rejected. The file bytes are unchanged. | DRAFT |
| FMT-R05 | FMT-01 | Loading a Claim in the retired `{check, args}` shape returns the current Claim shape in memory. `upgrade_stored_claim` does not write the file. | DRAFT |
| FMT-R06 | FMT-01 | `version_digest` ignores `format_version`. A pack directory digest of a file written by `save_pack` / `save_requirement` is unchanged when the only difference is that key. An existing signature over that digest still verifies. The upgrade-or-cancel dialog appears only where that file is already saved by a person, and only when `read_version` is lower than `current_version`. Check and compile do not open it and do not write. | DRAFT |

`format_version` is an integer on the file. It is not `pack.json` `version`, not `origin.version`, and not the directory `<packs_dir>/<pack-id>/<pack-version>/`.

Version 0 is not written. It means the key is absent. Version 1 is the contract at `3a2859c` plus the key. A later contract change is a new story that adds the step 1 → 2. It does not grow this plan.

## Tasks

### Task 1 — accept `format_version` and keep digests stable

**Requirements:** FMT-R04, FMT-R06 (digest half)
**Files:** `docs/reference/packs2.md` §2.6 and the Pack, Requirement, and Claim sections; `docs/reference/workspace.md` §2 for `curbpack.json`; `docs/reference/outputs.md` for the run result, review report, and remedy report; `docs/reference/studio-internal.md` for review items; `common/canonical.py`; `common/validate.py`. Tests live next to the existing digest and seal tests (`tests/test_vr00_signature.py`, `tests/test_vr00_pack_seal.py`).
**Test first:** One requirement object hashed with `version_digest` has the same digest after `format_version: 1` is added. One pack saved with `save_pack` and `save_requirement`, then sealed, still verifies after those files are saved again with only `format_version: 1` added. A document with `format_version: 2` is rejected and the fixture file is byte-identical. Expected RED: the field is unknown to validation, and the digests still include every key except `signed`.
**Validation:** The new tests plus `python3 -m unittest tests.test_vr00_signature tests.test_vr00_pack_seal`.
**Stop if:** Keeping the pack-directory digest stable would require hashing every current file through a new serializer. Files with no `format_version` keep today's raw-byte hash. Only a file that has the key is hashed as `dump_text` of the same object with that key removed, which matches `common/jsonio.dump_text` output from before the key was added.

- [x] RED observed for the digest and the rejected version.
- [x] `version_digest` drops `format_version` the way it already drops `signed`. Pack-directory digest follows the rule in the stop condition.
- [x] Validation accepts `1` and rejects any other present value. Absence stays legal at this task; the loader's stamp is Task 2.
- [x] Checkpoint saved and one local commit created.

### Task 2 — load the current shape in memory; save writes it

**Requirements:** FMT-R01, FMT-R03, FMT-R05
**Files:** `common/store.py` for Pack, Requirement, Claim, and run result. A new `load` / `save` pair for `curbpack.json` beside `validate_curbpack_config` in `common/validate.py`, because that file is read today with `read_json` plus `validate_curbpack_config`. Review items: `load_items` / `write_items` in `studio/review/impl/items.py`. The sealed copy `review-report_<stamp>.items.json` is the same structure. Review report: `load_report` / `write_report` in `studio/compile/impl/report.py`. Remedy report: `sign_remedy_document` in `studio/review/impl/items.py`, written by `write_json` in `app/review_model.py`. Current name `remedy-report_<stamp>.json`. Older names of that same document are `remedy-report.json` and `review-report_*.remedy.json`. Working remedy fields (`remedy`, `remedy_notes`, `remedy_locked`, `remedy_revoked`, `outside`, `projected_runs`, `pending_outside`, `studio_snapshot`) stay on `review_items.json`. `upgrade_stored_claim` loses its write. The write today is in `load_claim`. The run-result files sidecar `run-result_<stamp>.files.json` uses the same read/save rule.
**Test first:** For each kind in the scope, a current-contract fixture with no `format_version` loads as version 1 and the file bytes are unchanged. The reading reports `read_version == 0` and `current_version == 1`. Calling save writes `format_version` 1 and leaves every other field as it was. A retired `{check, args}` Claim loads as the current Claim shape and the file is unchanged. An existing remedy report and an existing review report load as version 1 and are not rewritten. Expected RED: `load_claim` still writes when `upgrade_stored_claim` returns a document, and nothing reports the two versions.
**Validation:** The new tests plus the existing claim-upgrade tests and `python3 -m unittest tests.test_vr00_pack_seal`.
**Stop if:** A caller needs the retired Claim file to be rewritten on load. The in-memory object is the current shape. Disk changes only on save.

Shape of the reading, so existing callers do not each learn a new return type:

- `read_pack`, `read_requirement`, `read_claim`, `read_curbpack`, `read_run_result`, `read_review_items`, `read_review_report`, and `read_remedy_report` return the document at the current version, the integer that was on disk (`0` when the key was absent), and `current_version`.
- `load_pack`, `load_requirement`, `load_claim`, `load_claims`, `load_run_result`, `load_items`, and `load_report` keep returning the document alone. They call `read_*` and do not write. Add `load_remedy_report` the same way.
- `save_*` writes the document it was given after validation, with `format_version` 1. Save does not run an upgrade dialog. Sign Off writes a new remedy report at version 1. Compile writes a new review report at version 1. Check writes a new run result at version 1. None of those writers rewrite an older sealed file.

The production chain is one function, 0 → 1. That function sets `format_version` to 1 and changes no other field.

- [x] RED observed: load of an unversioned file either fails validation or writes, and no reading reports 0 and 1.
- [x] Load is side-effect free for every kind in the scope, including the retired Claim shape and an already sealed remedy report.
- [x] Save of a loaded object is the only write, and the written file is version 1.
- [x] Checkpoint saved and one local commit created.

### Task 3 — one function per step, with the second step only in a test

**Requirements:** FMT-R02
**Files:** the chain helper introduced in Task 2, and its unit test. Production registers only 0 → 1.
**Test first:** A chain registered as 3 → 4 then 4 → 5, given a document at 3, runs those two functions in that order and returns version 5. A document at 1 against that same chain is rejected and the file bytes are unchanged. Expected RED: no such runner exists, or the only code path is the single 0 → 1 assignment.
**Validation:** `python3 -m unittest` on that test module.
**Stop if:** The test needs a real 1 → 2 change to Packs v2. The extra steps exist only inside the test.

- [x] RED observed for the ordered two-step run.
- [x] Production still exposes only 0 → 1.
- [x] Checkpoint saved and one local commit created.

### Task 4 — one upgrade-or-cancel dialog on screens that already save

**Requirements:** FMT-R03, FMT-R06 (dialog half)
**Files:** the screens that already save a Pack, a Requirement, a Claim, `curbpack.json`, or `review_items.json`. One shared prompt. The review screen that saves `review_items.json` is one of them. Check, compile, Sign Off, discovery reads, and opening a sealed file do not gain a prompt.
**Test first:** Opening a page that saves a Requirement whose file has no `format_version` shows one upgrade-or-cancel choice and does not change the file. Cancel leaves the bytes. Upgrade writes version 1 and no other field change. The same choice, with the same two outcomes, is what the Pack screen, the Claim screen, the `curbpack.json` screen, and the review-items screen use. A Check run against an unversioned Pack reads version 1 in memory, writes no Pack or Claim file, and shows no upgrade prompt. Opening an existing run result, review report, remedy report, or sealed items file does not write and does not prompt. Expected RED: those screens load and show the editor with no choice, or a save happens on open.
**Validation:** The new page tests plus the existing requirement-save and check-run tests those screens already have.
**Stop if:** The prompt would have to appear in `curbcheck`, on compile, on Sign Off, or on open of a run result, a review report, a remedy report, or a sealed items file. Those readers use `load_*` / `read_*` and do not write. Remedy Markdown and PDF get no version field.

- [ ] RED observed for "open does not write, and the choice is shown".
- [ ] Upgrade saves version 1. Cancel does not save. The other three screens use that same prompt.
- [ ] Check reads an unversioned Pack without writing and without the prompt.
- [ ] Checkpoint saved and one local commit created.

### Task 5 — route existing load and save call sites through those functions

**Requirements:** FMT-R01, FMT-R05
**Files:** product code that still calls `read_json` plus `validate_curbpack_config` for `curbpack.json`, or that writes a Pack, Requirement, or Claim with `write_json` instead of `save_pack`, `save_requirement`, or `save_claim`. Tests that assert the whole saved document gain `format_version` 1 where they go through save. Tests of `version_digest` stay on the digest, which ignores the key.
**Test first:** No new behavior. Grep-led list of the bypasses, then a regression run. Expected result is the Task 1–4 tests still passing after each bypass is removed. A bypass that writes on load is a failure of FMT-R05, not a new feature.
**Validation:** `python3 -m unittest` for the modules touched, then the suite those modules already belong to. Record the exact commands and counts. Do not describe a skipped module as passing.
**Stop if:** A bypass is remedy Markdown or PDF, a job file, try-run, feedback, catalog, repos, or a test fixture writer. Leave those on `write_json`. Run results, review items, the review report, and the remedy report JSON are in scope and move onto `read_*` / `save_*`.

- [ ] Product reads of every kind in the scope go through `read_*` / `load_*`. Product writes go through `save_*`.
- [ ] Remedy Markdown, PDF, job files, and fixture writers are unchanged.
- [ ] Regressions for the touched modules are recorded with counts.
- [ ] Checkpoint saved and one local commit created.

### Task 6 — update the story so it matches what was built

**Inputs / contracts:** this file after Tasks 1–5; `docs/agile/epics/15-file-format-versions/stories/FMT-01-version-and-upgrade-chain.md`.
**Change files:** the FMT-01 story only.
**Acceptance / stop:** The story describes integer versions, the chain with no skips and a floor, digest exclusion, the GUI-only dialog, and the saved JSON kinds this plan lists. This task does not gate Tasks 1–5. If the context runs out after the code is in, this task waits.

- [ ] Story text matches the implemented behavior.
- [ ] No product code in this task.

## Work log

- **2026-11-26 / Task 0:** Plan written from the agreed sequence. Missing `format_version` is version 0 and is not stored. Version 1 is the contract at `3a2859c` plus that key. Load returns the version-1 document in memory and reports both numbers. Save is the only write. The dialog is upgrade or cancel, and only on screens that already save. `format_version` is outside `version_digest` and outside the pack-directory digest of a `dump_text` file. Story file not edited in this step. No product code. No tests run.
- **2026-11-26 / Task 6:** Maintainer chose to implement from this plan first. The story file is documentation after Tasks 1–5, and it does not gate the code.
- **2026-11-26 / Task 0:** Scope widened after a file inventory. Run results, `review_items.json`, the review report, and the remedy report JSON are in. Working remedy state is fields on `review_items.json`, not a separate file. Sign Off writes `remedy-report_<stamp>.json` (older names `remedy-report.json` and `review-report_*.remedy.json` are the same document). Remedy Markdown and PDF stay out. A sealed file is not rewritten on read.
- **2026-11-26 / Task 1 IMPL-START:** FMT-R04, FMT-R06 (digest half). `python3 scripts/check_story_plan.py FMT-01 --phase ready` passed. Tests to write first: `version_digest` ignores `format_version`; a sealed pack still verifies after `save_pack` / `save_requirement` add only `format_version` 1; `format_version` 2 is rejected and the fixture bytes stay. No production code yet.
- **2026-11-26 / Task 1 RED:** `python3 -m unittest tests.test_vr00_signature.ObjectSignatureTest.test_version_digest_ignores_format_version tests.test_vr00_pack_seal.PackSealTest.test_adding_format_version_keeps_the_pack_seal tests.test_vr00_pack_seal.PackSealTest.test_format_version_2_is_rejected_and_the_file_is_unchanged` → 3 tests, FAILED (failures=2, errors=1). Digest mismatch because `format_version` was hashed. `save_pack` raised `ModelError` for unknown `format_version`. Version 2 was rejected as an unknown field (`expected one of [...]`), not as `1, or absent`.
- **2026-11-26 / Task 1 GREEN:** Same three tests, then `python3 -m unittest tests.test_vr00_signature tests.test_vr00_pack_seal` → Ran 16 tests, OK. `python3 -m unittest tests.test_review_compile tests.test_review_report_kept` passed inside a combined run of 22 results. `tests.test_remedy_report` did not run: `ModuleNotFoundError: No module named 'pypdf'`. That module was not changed. REVIEW-START.
- **2026-11-26 / Task 1 review 1:** Blocking: CRLF requirement changed the pack directory digest; several signing sentences still said the digest removes only `signed`. Minor, recorded and fixed in this step: the seal test did not assert the key survived the save; `sign_object` docstring named only `signed`. Recommendations left for Task 2: `write_items` key list, remedy-report validation, one shared format-version helper, Git blob comparison stays raw bytes, embedded copies are not stamped. CRLF test failed first (`90ad1b50…` != `5a4c52a8…`), then `python3 -m unittest tests.test_vr00_signature tests.test_vr00_pack_seal` → Ran 17 tests, OK. Second review of the updated diff.
- **2026-11-26 / Task 1 VERIFIED:** Second review found no Critical or Important issues. Minor, left as recorded: `docs/reference/packs2.md` §3 still says the Claim digest is the canonical Claim without `signed` only; the rejection test covers integer `2` and not a non-integer such as `true`. `python3 -m unittest tests.test_vr00_signature tests.test_vr00_pack_seal` → Ran 17 tests, OK. Next action is Task 2. Commit `9dfa246fbbfe7dad9de29d22837ccd182c555c73`.
- **2026-11-26 / Task 2 IMPL-START:** FMT-R01, FMT-R03, FMT-R05. Tests in `tests/test_fmt01_load.py`. Each unversioned kind loads as version 1 with `read_version` 0 and `current_version` 1, and the file bytes stay. Save is the write. A retired Claim and an existing remedy report and review report are not rewritten on load.
- **2026-11-26 / Task 2 RED:** Before the readers existed, `load_claim` on a retired `{check, args}` Claim changed the file bytes and removed `check`. Nothing reported `read_version` 0 and `current_version` 1.
- **2026-11-26 / Task 2 GREEN:** `python3 -m unittest tests.test_fmt01_load tests.test_m1_requirement tests.test_m3_claims tests.test_m4_checks tests.test_e2e_annex_vii tests.test_sys03_door.CurbpackPathFieldsTest tests.test_vr00_pack_seal tests.test_vr00_signature tests.test_rev03_review.ReviewCompileDecisionSealTest.test_compile_writes_a_new_report_without_decision_or_overwrite tests.test_review_flow.ReviewRemediationFlowTest.test_the_page_carries_a_review_through_remediation_and_into_the_next_review` → 60 tests, 1 failure. The failure is `test_review_flow`: `publish_remedy_reading` imports `reportlab`, which is not installed (`No module named 'reportlab'`). That failure is after `save_remedy_report` and is the same missing dependency as the import errors below. Full suite outside the sandbox: `python3 -m unittest discover -s tests -p 'test_*.py'` → Ran 700 tests, FAILED (failures=1, errors=4). The failure is the same review-flow `reportlab` error. The four errors are import failures: `test_compile_pdf` and `test_remedy_report` (`pypdf`), `test_review_deviations` and `test_review_retire` (`reportlab`). A sandboxed full run also reported git and HTTP errors; those did not recur outside the sandbox. REVIEW-START.
- **2026-11-26 / Task 2 review 1:** Blocking. An older review report no longer matched `load_run_result` because the loaded run gained `format_version`. Compile put that key on the embedded run, claims, and requirements, and `version_digest` only drops the top-level key. A retired Claim with `format_version` 2 loaded. The seal test resealed files that already had the key. Minor, left as recorded: `stamp_saved_document` mutates the caller's dict so a saved object matches a reload. The version-1 `read_version` case is now tested. After the fix, `python3 -m unittest discover -s tests -p 'test_*.py'` → Ran 706 tests, FAILED (failures=3, errors=4). Two failures were snapshot assertions updated to expect the embedded run without `format_version` (`test_chk08_studio`, `test_e2e_annex_vii`). The third failure and the four errors are the same missing `reportlab` / `pypdf` modules. Those two tests then passed. Second review of the updated diff.
- **2026-11-26 / Task 2 VERIFIED:** Second review found no Critical or Important issues. Minor, left as recorded: `stamp_saved_document` mutates the caller's dict; `write_items` does not reject a stored version other than absent or 1 before rewriting; a non-integer `format_version` is still untested on the new readers. `decision.py` still writes the sealed items file with `write_json`, and some `curbpack.json` writers still use `write_json`. Those stay for Task 5. Task 3's test chain has to apply its steps before `validate_format_version`, which accepts only absent or 1. Next action is Task 3. Commit `1997fb81ec6563b13643915681f0f48b0ead22c9`.
- **2026-11-26 / Task 3 IMPL-START:** FMT-R02. Tests for an ordered chain 3 → 4 then 4 → 5, a document below the chain start, and a missing step. Production still registers only 0 → 1. No runner yet.
- **2026-11-26 / Task 3 RED:** `python3 -m unittest tests.test_fmt01_chain` → 1 test, ERROR. `ImportError: cannot import name 'PRODUCTION_FORMAT_STEPS' from 'common.store'`. `apply_format_chain` is also absent. The failure is the missing runner, not a fixture or environment error.
- **2026-11-26 / Task 3 GREEN:** `python3 -m unittest tests.test_fmt01_chain tests.test_fmt01_load tests.test_vr00_pack_seal tests.test_m3_claims` → Ran 34 tests, OK. `python3 -m unittest discover -s tests -p 'test_*.py'` → Ran 711 tests, FAILED (failures=1, errors=4). The failure is `test_review_flow` (`No module named 'reportlab'`). The four errors are `test_compile_pdf` and `test_remedy_report` (`pypdf`) and `test_review_deviations` and `test_review_retire` (`reportlab`). REVIEW-START.
- **2026-11-26 / Task 3 review 1:** No Critical findings. Important: `Makefile`, `requirements-quality.txt`, and `scripts/ci/checks/quality.py` are unrelated quality tooling and are not part of this step. They stay unstaged. Minor, fixed in this step: a version above the chain was returned unchanged, and a missing later step ran earlier functions before raising. Both now reject before any step function runs. `python3 -m unittest tests.test_fmt01_chain tests.test_fmt01_load` → Ran 20 tests, OK. Second review of the updated diff.
- **2026-11-26 / Task 3 VERIFIED:** Second review found no Critical or Important issues. Minor, left as recorded: an empty step list returns the document unchanged; a document already part-way up a chain, and a step whose destination skips an integer, are implemented and not separately tested. Next action is Task 4. Commit is this step. Resolve with `git log -1 --format=%H -- plan/FMT-01.md`.
