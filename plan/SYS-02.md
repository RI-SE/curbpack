# SYS-02 — Keep the pilot on one test suite

## Summary

- **Story:** `docs/agile/epics/01-pack-editor/stories/SYS-02-one-test-suite.md`
- **Goal:** The pipeline runs one functional suite. `scripts/ci` only summarizes it. `tests/cs/` is removed after its unique cases sit in that suite.
- **Scope / exclusions:** No subsystem-folder move, no `tests/ci/`, no scanner scripts, no new Make target, no Packs v2 change, no EP-02, no release work. Not a pilot release blocker. Do not start Task 1 ahead of a runnable pilot.
- **Baseline:** 2026-10-23, outside the sandbox. `make test` — `Summary: 194 PASS, 0 FAIL`, exit 0. `make ci-tests` — `tests ................... [PASS]` then `Summary: 1 PASS, 0 FAIL`, exit 0. `./tests/cs/run_all.sh` — 16 passes, `[PASS] security boundary suite`, exit 0. `requirements/workspace.py` `_pack_id_name` is already in the working tree and is preserved, not rewritten.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | DRAFT |
| Approved by | Pending human approval of requirements and plan |
| Current task | Task 0 — derive requirements and get plan approval |
| Last completed task | None |
| Last verified tests | 2026-10-23 baseline above. Not a story acceptance run. |
| Last checkpoint commit | None. Resolve with `git log -1 --format=%H -- plan/SYS-02.md`. |
| Requirements | `docs/req/pack-editor.md` — SYS-R01, SYS-R02, SYS-R03 DRAFT |
| Packs v2 | Not applicable. This story does not change Pack, Requirement, Claim, signature, or result fields. Contract file remains `docs/reference/packs2.md`. |
| Blockers | None |
| **Exact next action** | Maintainer approves or corrects this draft. Do not start Task 1. Pilot release work is not this story. |

## Requirements and acceptance mapping

| Requirement ID | Story | Test / observed evidence | Status |
| --- | --- | --- | --- |
| SYS-R01 | SYS-02 | `make test` and `make ci-tests` both invoke `scripts/ci/checks/tests.py`. After Task 2, `tests/cs/` is absent and the moved cases are `tests/test_*.py`. | DRAFT |
| SYS-R02 | SYS-02 | `make ci-tests` one-line summary; `ONLY=tests make ci-tests` case lines; `ONLY=nope make ci-tests` nonzero and lists `tests`. No new Make target. | DRAFT |
| SYS-R03 | SYS-02 | New cases in `tests/test_requirements_extract.py` and `tests/test_requirements_publish.py`. Behavior is the existing `_pack_id_name` check. | DRAFT |

## Tasks

### Task 0 — derive and approve requirements and plan

**Inputs / contracts:** SYS-02 story; `docs/req/pack-editor.md` SYS-R01–SYS-R03; `Makefile`; `scripts/ci/run.py`; `scripts/ci/checks/tests.py`; `docs/agile/future_cicd.md` presentation section; `policies/testing.md`; EP-03 SEC-03 line in `docs/agile/epics/03-ssdf-security/EPIC.md`.
**Change files:** the story, `docs/req/pack-editor.md`, `docs/req/README.md`, `plan/SYS-02.md`, the EP-01 story row, the EP-03 SEC-03 pointer.
**Acceptance / stop:** Human approval recorded on this checkpoint. No product code in this task.

- [ ] Requirements derived, traceable, reviewed and approved.
- [ ] Baseline observed; the EP-03 wording conflict is recorded with its proposed resolution.
- [ ] Plan approved. `python3 scripts/check_story_plan.py SYS-02 --phase ready` is the Build gate.

### Task 1 — assert pack id confinement inside the suite

**Requirements:** SYS-R03
**Files:** `tests/test_requirements_extract.py` gets the working-copy cases: a normal id selects, and `../outside` raises `ModelError`. `tests/test_requirements_publish.py` gets the published cases: a normal id selects a directory `root/published/<pack_id>/<version>/`, and `../external` raises `ModelError`. Delete `tests/cs/workspace_selector.py` only after those cases pass. If `_pack_id_name` is missing, stop. Do not reimplement it in this story.
**Test first:** Add the cases, then run them. Expected result is PASS, because `_pack_id_name` already rejects a non-segment id. Do not force a fake RED. If they fail, stop; the working-tree fix has been lost. Port them as ordinary `unittest` methods. Do not import `tests/cs/_support.py`.
**Validation:** `python3 -m unittest tests.test_requirements_extract tests.test_requirements_publish` passes. `select_working_copy` accepts a normal id and raises `ModelError` for `../outside`. `select_published_pack` accepts a normal id and raises `ModelError` for `../external`.
**Stop if:** The fix would need a new Packs v2 field, a symlink policy, or an HTTP exploit claim. This task does not close SEC-02.

- [ ] Existing PASS demonstrated for the two rejection cases and the normal id.
- [ ] `tests/cs/workspace_selector.py` removed.
- [ ] Relevant regressions and review complete.
- [ ] Checkpoint saved and one local commit created for this step only.

### Task 2 — move the gaps and delete the side suite

**Requirements:** SYS-R01, SYS-R02
**Files:** Move each remaining assertion into the module that already owns that behavior, as ordinary `unittest` methods. Do not import `tests/cs/_support.py`.

- `tests/test_m4_checks.py`: `run_exist` and `run_contents` reject `../`, an absolute path, `docs/../../`, and a symlink to a file outside the repo. A whitespace-only skip reason raises `ModelError`. When one claim is `pass` and another is `fail`, assert both statuses and a nonzero `process_exit_code`.
- `tests/test_m2_discovery.py`: `read_source_text` rejects `docs\..\..\private.md`. A symlink is rejected by `read_source_text`, and `iter_markdown` does not return the external target.
- `tests/test_review_compile.py`: the four signature-mutation cases from `tests/cs/review_signature.py`, and the changed-check-args case from `tests/cs/check_result_integrity.py`.

Do not copy the cases the story lists as already covered. After these moves, delete `tests/cs/` including `run_all.sh`, `_support.py`, and `README.md`.
**Test first:** The new cases should PASS against current code. Record that. Do not weaken an assertion to make a duplicate disappear.
**Validation:** `make test` exit 0. `make ci-tests` prints one `tests` line and a summary with no FAIL. `ONLY=tests make ci-tests` prints case lines and a single summary. `ONLY=nope make ci-tests` exits nonzero and mentions `tests`. `tests/cs` is not a directory.
**Stop if:** A moved case fails for a reason other than a missing import. Do not change product code to green it in this story.

- [ ] Moved cases pass, or an unexpected failure is recorded and the step stops.
- [ ] `tests/cs/` deleted. `make test` and both `make ci-tests` forms verified.
- [ ] Relevant regressions and review complete.
- [ ] Checkpoint saved and one local commit created for this step only.

## Work log

- **2026-10-23 / Task 0:** Draft story placed in EP-01 as SYS-02. Requirements SYS-R01–SYS-R03 added to `docs/req/pack-editor.md`. Baseline commands and results are those in the Summary. EP-03 SEC-03 one-liner contradicted this story; the epic row now points at SYS-02 and leaves scanner scripts to SEC-04. That pointer is part of the draft, not an approved contract. No product code written for this story. `_pack_id_name` was already present in the working tree.
- **2026-10-23 / Task 0 review:** First independent review returned Issues Found. Task 2 deleted four assertions that were not duplicates and had no destination: backslash traversal and discovery symlink escape, a blank skip reason, and a mixed pass/fail exit code. Those now have destinations in Task 2. Task 1 now states the published happy path and that SEC-02 stays open.
- **2026-10-23 / Task 0 re-review:** Second independent review returned Approved, no issues. Advisory notes folded into Task 1 (which file holds which pack-id case; stop if `_pack_id_name` is missing) and Task 2 (assert both claim statuses with the mixed exit code). No third review.
