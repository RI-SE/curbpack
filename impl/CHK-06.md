# CHK-06 — Ship curbcheck as its own program

## Summary

- **Story:** `docs/agile/epics/01-pack-editor/stories/CHK-06-curbcheck-program.md`
- **Goal:** `make package` writes a curbcheck file for this host, beside the Studio application. That file runs `--repo`, `--packs`, `--out`, and `--skip`, and it contains `curbcheck-exist`, `curbcheck-contents`, `curbcheck-git`, and `checks/available_checks.json`.
- **Scope / exclusions:** Do not put `checks/bin` into the Studio file. Do not implement `dep_ban`, `fresh`, `owned`, `git_signed`, or `git_signer`. Do not rename `checks/`, `python3 -m checks`, `/check`, or the JSON field `check`. Do not edit `docs/reference/packs2.md`, `daniel/ny_sdd/`, the reference product, or EP-10. Do not switch `make test` onto the built file. Git stays the system `git`.
- **Baseline:** `python3 scripts/ci/checks/tests.py` on 2026-10-25 before this story's code printed `Summary: 185 PASS, 28 FAIL`. One PASS name was printed twice, so `plan/CHK-06-baseline-pass.txt` has the 184 unique names, one per line, with no trailing space. The 28 failures are named in the work log. A later run must still pass every name in that file. The 28 are left as they are unless this story's diff is what breaks them. `test_git_checks.test_an_executable_bit_fails_only_when_git_tracks_filemode` and `test_git_checks.test_skip_worktree_and_assume_unchanged_do_not_hide_a_dirty_file` did not appear in that run.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | DONE |
| Approved by | Maintainer, 2026-10-25, ordered this story written and carried to completion. Plan review 2 approved. |
| Current task | None. CHK-06 is complete. |
| Last completed task | Task 2 — package curbcheck, smoke it, and name it in the docs |
| Last verified tests | `python3 -m unittest tests.test_curbcheck_package tests.test_delivery -q` → 12 tests, OK. `make package` → `[PASS] smoke curbpack-studio-macos-arm64`, `[PASS] smoke curbcheck-macos-arm64`, `[PASS] wrote SHA256SUMS`. `python3 scripts/ci/checks/tests.py` → `Summary: 223 PASS, 0 FAIL`. All 184 names in `plan/CHK-06-baseline-pass.txt` are in that pass list. |
| Last checkpoint commit | 892e86c67b1272fb27a2307322f9a1d2690ac9f6 |
| Requirements | `docs/req/checks.md` CHK-R14–CHK-R17 APPROVED for CHK-06; CHK-R01–CHK-R13 stay as they were for CHK-05 |
| Packs v2 | `docs/reference/packs2.md` — not applicable to change. This story does not add a field. The runner already writes the run result that contract describes. |
| Blockers | None |
| **Exact next action** | No further implementation step. CHK-06 is complete. |

## Requirements and acceptance mapping

| Requirement ID | Story | Test / observed evidence | Status |
| --- | --- | --- | --- |
| CHK-R14 | CHK-06 | `tests/test_curbcheck_package.py` asserts the Studio PyInstaller argv still starts at `app/__main__.py` and does not add `checks/bin`. It asserts the curbcheck argv starts at `checks/__main__.py`, adds `checks/available_checks.json`, and omits the UI datas. The same test asserts the host names `curbcheck-macos-arm64`, `curbpack-studio-macos-arm64`, `curbcheck-windows-x64.exe`, and `curbpack-studio-windows-x64.exe`. `make package` on this Mac writes the two macOS files and a `dist/SHA256SUMS` line for each. | APPROVED |
| CHK-R15 | CHK-06 | `tests/test_curbcheck_package.py` starts the tool entry the packaged file will use. `exist` and `contents` pass. `git_fresh` and `git_author` pass on a temp Git repo. `git_signed` and `git_signer` return not implemented. `dep_ban` fails because the command is absent. `--skip claim-id=reason` stores the reason. `make package` then runs `dist/curbcheck-macos-arm64` through the same cases. | APPROVED |
| CHK-R16 | CHK-06 | Existing `tests/test_check_dispatch.py` still starts an external program for a source-tree call. `python3 -m checks --repo --packs --out` on a temp repo with one `exist` Claim exits 0. | APPROVED |
| CHK-R17 | CHK-06 | `.github/workflows/ci.yml` uploads `dist/curbcheck-*` with `dist/curbpack-studio-*` and `dist/SHA256SUMS`. `docs/user-guides/install.md` and `docs/user-guides/ci-cd.md` name the program `curbcheck`. `docs/concepts/README.md` says `exist`, `contents`, `git_fresh`, and `git_author` run through `curbcheck-exist`, `curbcheck-contents`, and `curbcheck-git`. It says `git_signed` and `git_signer` are not implemented, and that `dep_ban`, `fresh`, and `owned` fail because their commands are absent. Importing `checks.__main__` does not import `app`, `requirements.ui`, `claims.ui`, review, or scaffold. | APPROVED |

## Tasks

### Task 0 — derive and approve requirements and plan

**Inputs / contracts:** CHK-06 story. `checks/dispatch.py` starts `[command, check, --repo, --args]` with `PATH` prefixed by `checks/bin/`. `checks/schema.py` loads `available_checks.json` beside the module. `scripts/build/package.py` builds only `app/__main__.py` and writes one SHA256 line. `scripts/release/publish.py` downloads the two Studio artifact names and verifies every file in each directory against `SHA256SUMS`.
**Change files:** `docs/req/checks.md`, `plan/CHK-06.md`, `docs/agile/epics/01-pack-editor/EPIC.md`, `docs/agile/epics/01-pack-editor/stories/CHK-06-curbcheck-program.md`
**Acceptance / stop:** plan review has no blocking issue; `python3 scripts/check_story_plan.py CHK-06 --phase draft` passes; maintainer approval recorded; `--phase ready` passes before Build.

- [x] Requirements derived, traceable, reviewed and approved.
- [x] Baseline observed; risk/contract conflicts recorded.
- [x] Plan approved in Cursor Plan Mode (record approver).

### Task 1 — re-enter the three tools from one process

**Requirements:** CHK-R15, CHK-R16
**Files:** `checks/dispatch.py`, `checks/__main__.py`, `tests/test_curbcheck_package.py`
**Test first:** `python3 -m unittest tests.test_curbcheck_package` fails because the packaged re-entry is not implemented: a call that sets argv0 to `curbcheck-exist` is not dispatched, and `contents`, `git_fresh`, `git_author`, `git_signed`, `git_signer`, `dep_ban`, and `--skip` are not covered.
**Validation:** that test, then `python3 -m unittest tests.test_check_dispatch tests.test_m3_claims`. A source call with `sys.frozen` false still uses `checks/bin` and the argv in `checks/ARCHITECTURE.md`.
**Stop if:** the only way to keep `git_signed` unimplemented is to hide a pass, or a source-tree test starts requiring the built file, or the packaged argv would differ from `<command> <check-id> --repo <path> --args <json>`.

- [x] RED observed for the intended behavior (or existing PASS demonstrated).
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

IMPL-START CHK-R15, CHK-R16. Files: `checks/dispatch.py`, `checks/__main__.py`, `checks/commands.py`, `checks/bin/curbcheck-exist`, `checks/bin/curbcheck-contents`, `checks/bin/curbcheck-git`, `checks/toolmain.py`, `tests/test_curbcheck_package.py`. Test: `python3 -m unittest tests.test_curbcheck_package`.

**Decision, recorded here so Task 1 does not edit `checks/ARCHITECTURE.md`.** That file says the runner executes the registered command as `<command> <check-id> --repo <path> --args <json>`. A source checkout keeps that argv and finds the command on `PATH` under `checks/bin/`. The packaged file is one program, so it cannot also be three files in `checks/bin/`. When `sys.frozen` is true, `run_check_tool` starts the same argv and sets `executable` to `sys.executable`. The child sees `argv[0]` as the command name (`curbcheck-exist`, `curbcheck-contents`, or `curbcheck-git`) and the rest unchanged. There is no `--tool` flag. `curbcheck-exist` calls `run_exist`, `curbcheck-contents` calls `run_contents`, and `curbcheck-git` calls the git handler that already returns not implemented for `git_signed` and `git_signer`. Any other command name prints one JSON object `{"status":"fail","detail":"check tool '<command>' is unavailable"}` and exits 0 so the parent records that fail. This is the missing-command result the architecture already requires. It is not a second argv and not an architecture edit.

### Task 2 — package curbcheck, smoke it, and name it in the docs

**Requirements:** CHK-R14, CHK-R17
**Files:** `scripts/build/package.py`, `scripts/release/smoke.py`, `.github/workflows/ci.yml`, `docs/user-guides/install.md`, `docs/user-guides/ci-cd.md`, `docs/concepts/README.md`, `tests/test_curbcheck_package.py`
**Test first:** the package test fails because `_pyinstaller_args` has no curbcheck entry and `write_sums` records one file.

IMPL-START CHK-R14, CHK-R17. Files: `scripts/build/package.py`, `scripts/release/smoke.py`, `.github/workflows/ci.yml`, `tests/test_curbcheck_package.py`, `docs/concepts/README.md`, `docs/concepts/packs.md`, `docs/concepts/evidence.md`, `docs/user-guides/install.md`, `docs/user-guides/ci-cd.md`. Test: `python3 -m unittest tests.test_curbcheck_package.PackageArgsTest`.
**Validation:** `python3 -m unittest tests.test_curbcheck_package`. Then `make package` on this Mac. The curbcheck smoke runs the built file on a temp repo: `exist` and `contents` pass, `git_fresh` and `git_author` pass, `git_signed` and `git_signer` are not implemented, `dep_ban` is unavailable, and `--skip` stores the reason. The Studio smoke stays the cover-page smoke. Then `python3 scripts/ci/checks/tests.py` and compare PASS names with `plan/CHK-06-baseline-pass.txt`. Every name in that file must still pass.
**Stop if:** the Studio datas gain `checks/bin`, or `SHA256SUMS` omits a file that the package job uploads. `scripts/release/publish.py` keeps artifact names `curbpack-studio-macos-arm64` and `curbpack-studio-windows-x64`; curbcheck is a second file inside that artifact, so every uploaded file must be a line in `SHA256SUMS`.

- [x] RED observed for the intended behavior (or existing PASS demonstrated).
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

## Work log

- **2026-10-25 / Task 0:** Baseline `python3 scripts/ci/checks/tests.py` exited 1 with `Summary: 185 PASS, 28 FAIL`. The 185 PASS names are `plan/CHK-06-baseline-pass.txt`. FAIL names: `test_e2e_annex_vii.test_requirement_to_review_uses_the_same_objects`; `test_git_checks.test_a_different_author_fails_and_names_the_commit`; `test_git_checks.test_a_missing_path_fails`; `test_git_checks.test_a_non_utf8_author_fails_and_the_next_check_still_runs`; `test_git_checks.test_a_unit_separator_in_the_name_is_not_the_email`; `test_git_checks.test_a_utf8_author_passes_when_the_repo_prints_latin1`; `test_git_checks.test_an_unsigned_commit_still_passes`; `test_git_checks.test_matching_name_and_email_pass_without_detail`; `test_git_checks.test_a_bracket_path_is_not_a_glob`; `test_git_checks.test_a_clean_symlink_passes`; `test_git_checks.test_a_clean_symlink_passes_for_every_target_kind`; `test_git_checks.test_a_crlf_worktree_matches_the_lf_blob`; `test_git_checks.test_a_future_commit_fails`; `test_git_checks.test_a_path_that_leaves_the_repo_fails_without_aborting_the_claim`; `test_git_checks.test_a_path_through_a_file_fails_and_the_next_check_still_runs`; `test_git_checks.test_a_recent_file_passes_without_detail`; `test_git_checks.test_a_rename_does_not_keep_the_old_path_history`; `test_git_checks.test_a_symlink_loop_fails_and_the_next_check_still_runs`; `test_git_checks.test_a_symlink_with_the_same_bytes_differs_from_head`; `test_git_checks.test_age_equal_to_the_maximum_passes`; `test_git_checks.test_an_inherited_git_dir_stays_on_the_requested_repo`; `test_git_checks.test_missing_dirty_and_untracked_paths_fail`; `test_git_checks.test_monday_change_fails_when_friday_head_touched_another_file`; `test_m4_checks.test_empty_claim_list_is_not_success_and_dirty_is_labeled`; `test_review_discover_again.test_failed_claim_stays_visible_and_popup_is_one_requirement`; `test_review_report_kept.test_post_check_does_not_delete_a_signed_report`; `test_review_report_kept.test_a_later_run_stays_distinct_until_compile_is_confirmed`; `test_ui_smoke.test_pages_show_the_saved_requirement_and_a_real_failure`. No Packs v2 field is proposed. Story, epic row, and CHK-R14–CHK-R17 written. Plan review 1 ([review](7b1cdcc6-dd50-4007-8c90-b3d477ee1539)) found three issues: a `--tool` argv would conflict with `checks/ARCHITECTURE.md`; the tests omitted `contents`, `git_fresh`, `git_author`, `git_signed`, and `git_signer`; the 185 names were only in `/tmp`. The plan now keeps the architecture argv and uses `executable=sys.executable` when frozen, names those Check results in Task 1 and the package smoke, and stores the pass names in `plan/CHK-06-baseline-pass.txt`. Advisory notes on Windows names, the draft-status sentences, `--skip`, the import boundary, and the unavailable-versus-not-implemented wording are in the same revision. Plan review 2 ([review](2cf4aa1c-e69e-431f-b033-2613f2e98fca)) approved with no issues. The baseline file was then deduped: the runner printed `test_requirements_produce.test_discovery_guidance_asks_for_actionable_hints` twice, so the file holds 184 unique names. Maintainer approval is the 2026-10-25 request to write this story and finish it.
- **2026-10-25 / Task 1:** RED: `python3 -m unittest tests.test_curbcheck_package -v` — frozen parent raised `KeyError: 'executable'`; exist, contents, and dep_ban exited 2 from the CLI parser (`--packs` and `--out` required). The git case first died in the sandbox on `git init`; outside the sandbox it reaches the same missing tool entry. `--skip` already returned skipped with detail `not this build` (existing PASS). GREEN: same module plus `tests.test_check_dispatch` and `tests.test_m3_claims`, 14 tests, OK. Code review [review](72f99749-6bed-4512-81d2-0bae2fd70066): no Critical or Important. Minors: the frozen test mocks `subprocess.run` (Task 2 smoke is the real process); dep_ban args were not schema-valid. Those args are now `package` and `banned_versions`. The frozen test name now says it checks the parent argv.
- **2026-10-25 / Task 2:** RED: `python3 -m unittest tests.test_curbcheck_package.PackageArgsTest -v` — `ImportError` for `curbcheck_args`, and `write_sums` raised `AttributeError` on a list. The import-boundary test already passed. GREEN: `python3 -m unittest tests.test_curbcheck_package tests.test_delivery -q` → 12 tests, OK. `make package` wrote both macOS files and printed `[PASS] smoke curbpack-studio-macos-arm64`, `[PASS] smoke curbcheck-macos-arm64`, and `[PASS] wrote SHA256SUMS`. A second smoke of `dist/curbcheck-macos-arm64` after the smoke-script cleanup also printed `[PASS] smoke curbcheck-macos-arm64`. `python3 scripts/ci/checks/tests.py` → `Summary: 223 PASS, 0 FAIL`. Every name in `plan/CHK-06-baseline-pass.txt` is in that pass list. Code review [review](9ecd2919-a346-4099-89e2-4351246fdec7): no Critical or Important. Minors fixed in this step: temp dirs are removed if the fixture raises, the install guide no longer says Linux `make package` builds a binary, the CI guide names `curbcheck-windows-x64.exe`, and the sums test checks the digest and the two-space separator. `docs/concepts/packs.md` and `docs/concepts/evidence.md` are included because the concepts page links to them. `getting-started.md` and `troubleshooting.md` stay untracked.
- **2026-10-25 / Task 2 close:** Task 2 commit `892e86c67b1272fb27a2307322f9a1d2690ac9f6`. Plan status set to DONE and the file moved to `impl/CHK-06.md`. No implementation step remains.
