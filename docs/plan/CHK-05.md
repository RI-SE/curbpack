# CHK-05 — Git provenance Checks

## Summary

- **Story:** `docs/agile/epics/01-pack-editor/stories/CHK-05-remaning-checks.md`
- **Goal:** A user can check Git history for evidence named by a Claim: when it last changed, whether that commit's signature verifies, and who authored it or signed it, as separate Check results.
- **Scope / exclusions:** One Git checker command may back several registered Check ids. Results stay in the existing `checks[]` and run-result shape. No `owned` implementation, no `dep_ban`, no new Claim schema, no GUI redesign, no EP-02 move. Discovery-form configuration and naming the last-change commit on a passing row stay deferred.
- **Baseline:** 2026-10-23, outside the sandbox (a sandboxed `git init` fails and is not a product failure). `python3 -m unittest tests.test_m3_claims` — Ran 5 tests, OK. `python3 -m unittest tests.test_m4_checks` — Ran 6 tests, OK. `python3 -m unittest tests.test_discover_claims_ui` — Ran 1 test, OK. `fresh` is registered and evaluates as `fail` with `not implemented` (`tests/test_m3_claims.py`).

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | BLOCKED |
| Approved by | Maintainer, 2026-10-23 |
| Current task | Task 3 — git_fresh uses the last commit that changed the path |
| Last completed task | Task 2 — four Git Check schemas registered |
| Last verified tests | 2026-10-23: `python3 -m unittest tests.test_git_checks tests.test_m4_checks tests.test_m3_claims` OK 31. That run does not cover a symlink loop or a path whose parent is a file. |
| Last checkpoint commit | This commit. Resolve with `git log -1 --format=%H -- docs/plan/CHK-05.md`. |
| Requirements | `docs/req/checks.md` — CHK-R01–CHK-R13 DRAFT. Maintainer accepted OPEN-1 through OPEN-8 on 2026-10-23. |
| Packs v2 | `docs/reference/packs2.md`, imported from Curbpack `b07b8deb9fed331b493241251087ce7ce648f5e4`. §4 and §4.1 name `git_fresh`, `git_signed`, `git_author`, and `git_signer`. |
| Blockers | Task 3 re-review: a symlink loop raises `RuntimeError`, and a path through a file such as `notdir/child.md` raises `NotADirectoryError`. Either aborts the run. No further review round. |
| **Exact next action** | Stop. Do not edit Task 3 further and do not start Task 4 until the maintainer reopens the step. The uncommitted `git_fresh` code is not a completed step. |

## Requirements and acceptance mapping

| Requirement ID | Story | Test / observed evidence | Status |
| --- | --- | --- | --- |
| CHK-R01 | CHK-05 | `tests/test_git_checks.py` `test_four_ids_share_one_command_and_old_ids_remain`. | DRAFT |
| CHK-R02 | CHK-05 | Packs v2 §2.5 `checks[]`. Runner loop in `checks/run.py` `run_claim`. No mixed Git Check test. | DRAFT |
| CHK-R03 | CHK-05 | Same runner loop and Packs v2 §3.1 aggregate. Not tested with one failing and one passing Git Check. | DRAFT |
| CHK-R04 | CHK-05 | `common/validate.py` rejects `detail` on `pass` and unknown Check-result keys. | DRAFT |
| CHK-R05 | CHK-05 | `tests/test_m3_claims.py`, `tests/test_m4_checks.py` (baseline above). | DRAFT |
| CHK-R06 | CHK-05 | `tests/test_git_checks.py` GitCheckSchemaTest. Packs v2 `b07b8deb`. `fresh` and `owned` stay registered. | DRAFT |
| CHK-R07 | CHK-05 | No test. OPEN-2 accepted 2026-10-23. Last commit that changed the path. Monday plus `max_age_days` 2 is fail when `as_of` is later than two days. | DRAFT |
| CHK-R08 | CHK-05 | No test. OPEN-3 accepted 2026-10-23. | DRAFT |
| CHK-R09 | CHK-05 | No test. OPEN-4 accepted 2026-10-23. | DRAFT |
| CHK-R10 | CHK-05 | No test. OPEN-5 accepted 2026-10-23. | DRAFT |
| CHK-R11 | CHK-05 | No test. OPEN-6 accepted 2026-10-23. Green row shows path and HEAD. Last-change commit id is in `detail` only on fail. Passing-row half of acceptance 4 is deferred. | DRAFT |
| CHK-R12 | CHK-05 | No test. OPEN-7 accepted 2026-10-23. Problems are `fail` with a reason. `skipped` stays the deliberate Claim skip. | DRAFT |
| CHK-R13 | CHK-05 | No test. OPEN-8 accepted 2026-10-23. Discovery form stays unchanged. `tests/test_discover_claims_ui.py` still expects the current form. | DRAFT |

Packs v2 §4 and §4.1 are committed. Story acceptance still to test: 1 (Git ids), 3 (independent Git results), 5 (fail closed), 6 (author is not signer), and 8 (the Git cases). Acceptance 2 for the discovery form is deferred with CHK-R13. The passing-row half of acceptance 4 is deferred with CHK-R11. Acceptance 7 is the existing copy-through rule in CHK-R04.

## Tasks

### Task 0 — derive and approve requirements and plan

**Inputs / contracts:** CHK-05 story; `checks/ARCHITECTURE.md`; `checks/available_checks.json`; `checks/run.py`; `common/validate.py`; `claims/ui/researcher.py`; `claims/ui/http.py`; `policies/architecture.md`; `policies/testing.md`; Packs v2 §2.5, §3.1, §4 at `a9ea1ef`.
**Change files:** `docs/req/checks.md`, `docs/req/README.md`, `docs/plan/CHK-05.md`
**Acceptance / stop:** Human approval recorded on this checkpoint. Any OPEN item still open blocks Build.

- [x] Requirements derived and conflicts recorded with file references. Proposals are not normative.
- [x] Independent plan review completed; no blocking findings. Advisory notes are in the work log and folded into CHK-R04, OPEN-6, and Task 1.
- [x] Baseline observed; this checkpoint records the commands above.
- [x] Plan approved by the maintainer on 2026-10-23. `python3 scripts/check_story_plan.py CHK-05 --phase ready` is the Build gate.

### Task 1 — close the open contract decisions

**Requirements:** CHK-R06–CHK-R13
**Files:** `docs/req/checks.md`, and Packs v2 only if the maintainer edits the Curbpack repository. No studio Check code.
**Test first:** None. This task does not add a test.
**Validation:** Re-read Packs v2 §4 against the approved sentences. If they still disagree, stop.
**Stop if:** The maintainer has not chosen, for each OPEN item, either the proposal, a replacement sentence, or an explicit deferral of that acceptance criterion.

- [x] OPEN-1 through OPEN-8 are each approved or deferred in `docs/req/checks.md`.
- [x] Packs v2 commit `b07b8deb9fed331b493241251087ce7ce648f5e4` names the four Check ids. No new result field.
- [x] Implementation tasks are listed below. The checkpoint current task is Task 2.

The extension point is an in-process branch in `checks/run.py` `_execute_check`, as `exist` and `contents` already use. The registry `command` string is not a subprocess dispatch, and this story does not add a checker framework. `fresh` and `owned` stay registered and non-passing so the current discovery form can still save them.

### Task 2 — register the four Git Check schemas

**Requirements:** CHK-R01, CHK-R06, CHK-R13
**Files:** `checks/available_checks.json`, `checks/schema.py` only for keywords the registry must enforce (`minimum`, RFC 3339, `allowed_signers` stays inside the repo), `tests/test_git_checks.py`
**Test first:** `python3 -m unittest tests.test_git_checks.GitCheckSchemaTest` fails because the four ids are unknown.
**Validation:** That test passes. `python3 -m unittest tests.test_m3_claims tests.test_m4_checks tests.test_discover_claims_ui` stays green. `fresh` still evaluates as not implemented.
**Stop if:** A schema would add a result field or change `exist` / `contents`.

- [x] RED observed for missing Git Check ids.
- [x] Schemas registered and the schema test is green.
- [x] Regression tests and review complete.
- [x] Checkpoint saved and verified local commit created.

### Task 3 — git_fresh uses the last commit that changed the path

**Requirements:** CHK-R07, CHK-R08, CHK-R11, CHK-R12
**Files:** `checks/run.py`, `tests/test_git_checks.py`
**Test first:** A new test in `tests/test_git_checks.py` fails because `git_fresh` is not implemented. It covers a fresh file (`pass`, no `detail`), Monday versus Friday with `max_age_days` 2 (`fail`, detail names the commit), a missing path (`fail`), a dirty path (`fail`), and an untracked path (`fail`).
**Validation:** The new test and `tests.test_m4_checks`.
**Stop if:** The check would read the wall clock, follow a rename, or put `detail` on `pass`.

- [ ] RED observed for the age and missing-path behavior.
- [ ] Minimal `git_fresh` implementation and GREEN verified.
- [ ] Regression tests and review complete.
- [ ] Checkpoint saved and verified local commit created.

### Task 4 — git_author is not a signature

**Requirements:** CHK-R10, CHK-R12
**Files:** `checks/run.py`, `tests/test_git_checks.py`
**Test first:** Author name and email match is `pass`. A different author is `fail`. The same author on an unsigned commit is still `pass` for `git_author`.
**Validation:** The new test. A missing path is its own `fail`.
**Stop if:** The author Check starts verifying a signature.

- [ ] RED observed.
- [ ] Minimal implementation and GREEN verified.
- [ ] Regression tests and review complete.
- [ ] Checkpoint saved and verified local commit created.

### Task 5 — git_signed and git_signer

**Requirements:** CHK-R09, CHK-R10, CHK-R12
**Files:** `checks/run.py`, `tests/test_git_checks.py`
**Test first:** A commit Git accepts under the named trust input is `pass` for `git_signed`. A missing signature and a rejected signature are separate `fail` details. `git_signer` passes only when `signer` equals the identity Git reports. The same author with another signer is `pass` for `git_author` and `fail` for `git_signer`.
**Validation:** Those tests. No key fetch and no reading of Claim `signed`.
**Stop if:** The test needs a network, a new trust store, or a machine-wide key.

- [ ] RED observed.
- [ ] Minimal implementation and GREEN verified.
- [ ] Regression tests and review complete.
- [ ] Checkpoint saved and verified local commit created.

### Task 6 — independent results, copy-through, and the old Checks

**Requirements:** CHK-R02, CHK-R03, CHK-R04, CHK-R05, CHK-R12
**Files:** `tests/test_git_checks.py`, and `checks/run.py` only if a mixed Claim does not already keep both rows.
**Test first:** One Claim with a failing `git_fresh` and a passing `git_author` keeps both statuses. Four Git Checks on one missing path are four `fail` rows. A passing Git Check has no `detail`. Compile copies the run result unchanged. `exist` and `contents` tests stay green.
**Validation:** `python3 -m unittest tests.test_git_checks tests.test_m3_claims tests.test_m4_checks tests.test_discover_claims_ui` plus the existing compile test that copies a run result, if one exists.
**Stop if:** The result gains a field or the discovery form changes.

- [ ] RED observed for the mixed Claim, or the behavior is already present and recorded.
- [ ] GREEN verified.
- [ ] Regression tests and review complete.
- [ ] Checkpoint saved and verified local commit created.

## Work log

- **2026-10-23 / Task 0:** Inspected CHK-05, `checks/ARCHITECTURE.md`, `checks/run.py`, `checks/available_checks.json`, `common/validate.py`, the discovery Check form, and Packs v2 §2.5, §3.1, and §4 at `a9ea1ef49a6589ce355940cac4c031fcc84c0410` (`packs2.md` clean relative to that commit). Baseline outside the sandbox: `python3 -m unittest tests.test_m3_claims` OK 5; `python3 -m unittest tests.test_m4_checks` OK 6; `python3 -m unittest tests.test_discover_claims_ui` OK 1. A sandboxed run of `test_empty_claim_list_is_not_success_and_dirty_is_labeled` failed in `git init` and passed when re-run unsandboxed. Wrote `docs/req/checks.md` with CHK-R01–CHK-R05 DRAFT and OPEN-1–OPEN-8. Did not change Check code or tests. Unrelated dirty files `AGENTS.md` and `.cursor/skills/story-workflow/SKILL.md` were left untouched. Independent plan review found no blocking issues. Advisory notes: future tasks must cover shared commit and fail-closed rules, pass traceability, compile/review copy-through, and the `exist` / `contents` regression; CHK-R04 must not be cited as acceptance 4; OPEN-6 must say whether acceptance 4 is deferred; implementation stays an in-process branch in `_execute_check`. Those notes are now in this plan and in `docs/req/checks.md`. `python3 scripts/check_story_plan.py CHK-05 --phase draft` passed after that wording fix.
- **2026-10-23 / Task 0:** Maintainer accepted OPEN-1, OPEN-3, OPEN-4, OPEN-5, and OPEN-8. Those are now CHK-R06, CHK-R08, CHK-R09, CHK-R10, and CHK-R13. OPEN-2, OPEN-6, and OPEN-7 remain. No Check code.
- **2026-10-23 / Task 0:** Maintainer confirmed OPEN-2. The relevant commit is the last commit that changed the path. `risk.md` changed Monday with max age 2 days is fail when `as_of` is more than two days later. CHK-R07 is DRAFT. OPEN-6 and OPEN-7 remain. No Check code.
- **2026-10-23 / Task 0:** Maintainer accepted OPEN-6 and OPEN-7. CHK-R11 and CHK-R12 are DRAFT. All eight decisions are closed. Studio implementation remains blocked until Packs v2 §4 is edited. No Check code.
- **2026-10-23 / Task 0:** Drafted an uncommitted edit of `../curbpack/docs/reference/packs2.md` §4 and §4.1 for maintainer review. Not committed. No Studio Check code.
- **2026-10-23 / Task 1:** Maintainer approved the packs2 diff. Local commit `b07b8deb9fed331b493241251087ce7ce648f5e4` on `curbpack` `main`, message `docs: replace fresh and owned with four Git checks`. Not pushed. Only `docs/reference/packs2.md` is in that commit. No Studio Check code.
- **2026-10-23 / Task 1:** Maintainer said to continue. Plan status set to APPROVED. Tasks 2–6 added. Build starts at Task 2. `python3 scripts/check_story_plan.py CHK-05 --phase ready` passed.
- **2026-10-23 / Task 2 IMPL-START:** CHK-R01, CHK-R06, CHK-R13. Files: `checks/available_checks.json`, `checks/schema.py`, `tests/test_git_checks.py`. Test: `python3 -m unittest tests.test_git_checks.GitCheckSchemaTest`.
- **2026-10-23 / Task 2:** RED: that command, 5 tests, 4 errors and 1 failure, `unknown check type`. GREEN after the schemas: `python3 -m unittest tests.test_git_checks tests.test_m3_claims tests.test_m4_checks tests.test_discover_claims_ui` OK 17. First review: RFC 3339 check was too loose (Important). Fixed `_rfc3339` to require seconds and an offset of `Z` or `±HH:MM`, and added those cases. Second review: no Critical or Important findings. Minor, left as recorded: lowercase `t`/`z` rejected; a wrong `openpgp` value is reported as a missing `allowed_signers`; `git_signer` test does not repeat the both-trust-inputs case. Unrelated dirty files were not included.
- **2026-10-23 / Task 3 IMPL-START:** CHK-R07, CHK-R08, CHK-R11, CHK-R12. Files: `checks/run.py`, `tests/test_git_checks.py`. Test: `python3 -m unittest tests.test_git_checks.GitFreshTest`.
- **2026-10-23 / Task 3 REVIEW-START:** First review, blocking. A pathspec such as `notes[1].md` matched `notes1.md` and passed. `git diff --quiet` treated `--skip-worktree` and `--assume-unchanged` as clean while the worktree bytes differed from HEAD. Fixed in the uncommitted diff: `GIT_LITERAL_PATHSPECS=1`, and dirty detection compares `git hash-object` with `git ls-tree HEAD`. Added `test_a_bracket_path_is_not_a_glob` and `test_skip_worktree_and_assume_unchanged_do_not_hide_a_dirty_file`. `python3 -m unittest tests.test_git_checks tests.test_m4_checks` then OK 19.
- **2026-10-23 / Task 3 BLOCKED:** Second review, still blocking. No third round. Important: `Path.is_file()` and `git hash-object` follow symlinks, so replacing a fresh file with a symlink to the same bytes returns `pass` while Git reports a typechange; a clean tracked symlink can fail `differs from HEAD`. Important: `_git_run` copies the process environment, so an inherited `GIT_DIR` makes `git -C` read another repository and can pass a stale file. Minor, not fixed: a repo with no commit is reported as `git is unavailable`; tests set author date and committer date to the same instant; `parse_rfc3339` labels a bad committer stamp as a bad `as_of`. Uncommitted files stay uncommitted. Task 4 has not started.
- **2026-10-23 / Task 3:** Maintainer reopened the step. Accepted fix: drop inherited repository pointers in the Git child environment for `_git_run` and `git_snapshot`; hash a real symlink as its link text and require mode `120000`. A regular file stays on `git hash-object -- path`. Planned tests: symlink typechange fails, a clean symlink passes, inherited `GIT_DIR` stays on the repo argument, a CRLF worktree with `eol=lf` matches the LF blob.
- **2026-10-23 / Task 3 RED:** The four new tests. Symlink typechange returned `pass`. A clean symlink returned `fail`. Inherited `GIT_DIR` returned `pass`. The CRLF worktree already returned `pass` on Git 2.54 because `git hash-object -- path` applies the `eol=lf` clean filter, so that case stays a regression test with no extra hashing code.
- **2026-10-23 / Task 3 REVIEW-START:** `python3 -m unittest tests.test_git_checks tests.test_m4_checks tests.test_m3_claims` OK 28.
- **2026-10-23 / Task 3:** First review of the reopened diff, still blocking. A clean absolute or `../` symlink raised `ModelError` and aborted the Claim. A clean dangling symlink and a symlink to a directory failed as `absent`. `chmod +x` passed while `core.filemode=true`. RED for those cases, then fixed: presence uses `lstat` on the unresolved entry, a path that leaves the repo is `fail` without aborting later Checks, and the executable bit is compared only when `core.filemode` is not `false`. `python3 -m unittest tests.test_git_checks tests.test_m4_checks tests.test_m3_claims` OK 31.
- **2026-10-23 / Task 3 BLOCKED:** Re-review of the reopened diff, still blocking. No further round. Important: `_entry_path` only turns `ModelError` into `fail`. A symlink loop raises `RuntimeError`, and `notdir/child.md` raises `NotADirectoryError` from `lstat`. Either leaves `run_claim`, so later Checks are not recorded. Minor, not fixed: `core.filemode=0` is still treated as tracked; a repo with no commit is still `git is unavailable`; tests still set author date and committer date to the same instant. Uncommitted files stay uncommitted. Task 4 has not started.
