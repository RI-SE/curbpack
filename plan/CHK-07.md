# CHK-07 — curbcheck uses curbpack.json paths, owns defaults, updates CLI docs

## Summary

- **Story:** `docs/agile/epics/01-pack-editor/stories/CHK-07-curbcheck-workspace.md`
- **Goal:** `curbcheck` / `python3 -m checks` always reads product `curbpack.json` path fields, prints created-file defaults from one factory, uses stdout / `-j` / `-o`, and treats `--packs` / `--requirements` as comma-separated id lists.
- **Scope / exclusions:** Story CHK-R01–CHK-R06. Rewrite `docs/reference/curbcheck-cli.md`. Inventory and retarget curbcheck CLI tests and the suite argv this plan lists. Do **not** implement `unsigned_requirements` behaviour. Do **not** change Studio door UI (SYS-03). Do **not** rewire Studio Check/Review call sites (CHK-08). Do **not** change Packs v2 Claim / run-result object shapes. Do **not** implement unavailable Check ids. Python `run_repository(..., packs_root=)` stays for Studio until CHK-08; the CLI stops passing a packs directory.
- **Baseline:** Branch `main` at `39c2669`. Unrelated dirty WIP preserved (not reset, not committed): `requirements/extract/assemble.py`, `requirements/ui/try_discovery.py`, `scripts/release/publish.py`, `tests/test_release_publish.py`, `tests/test_requirements_produce.py`, untracked `requirements/extract/adapters/manual/`. `python3 -m unittest tests.test_curbcheck_package tests.test_curbcheck_catalogue tests.test_m4_checks` — Ran 23 tests, OK. Current CLI (`checks/__main__.py` `_cli`): `--packs` is `type=Path` (directory); `--out` defaults to `<results_dir>/run-result.json` (undated); always calls `run_and_write`; no `--defaults`, `-j`/`--json`, or `--requirements`. `run_repository` already loads `packs_dir` / `claims_dir` from `curbpack.json` (SYS-03 Task 1). `created_curbpack()` lives in `discovery/door.py`. `docs/reference/curbcheck-cli.md` still has the pending-CHK-07 banner and directory `--packs` wording.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | APPROVED |
| Approved by | danielfl, 2026-10-29 (CHK-07 decided in walkthrough; “kör vidare med curbcheck” after SYS-03 Task 7 — proceed Task 1–5; OPEN-1–OPEN-6 as this plan) |
| Current task | Close story |
| Last completed task | Task 5 |
| Last verified tests | 2026-10-29: `python3 -m unittest tests.test_chk07_curbcheck tests.test_curbcheck_catalogue tests.test_curbcheck_package tests.test_m4_checks` — Ran 39 tests, OK |
| Last checkpoint commit | This commit. Resolve with `git log -1 --format=%H -- plan/CHK-07.md`. |
| Requirements | Story CHK-R01–CHK-R06 in `CHK-07-curbcheck-workspace.md`. No new `docs/req/` row. Legacy `docs/req/checks.md` CHK-R01–CHK-R17 are CHK-05/CHK-06 Check-execution requirements, not this CLI contract. |
| Packs v2 | `docs/reference/workspace.md` owns path fields, created-file values, and CLI channels (§2.2, §2.3, §3). `docs/reference/packs2.md` §2.3 owns pack/requirement selection; §3.1 owns the run-result object. This plan edits neither. |
| Blockers | None |
| Exact next action | Move `plan/CHK-07.md` to `impl/CHK-07.md` and run `python3 scripts/check_story_plan.py CHK-07 --phase done`. |

## Requirements and acceptance mapping

Requirements live in the story. This table only maps each id to its acceptance test.

| Requirement ID | Story | Test / observed evidence | Status |
| --- | --- | --- | --- |
| CHK-R01 | CHK-07 | `tests/test_chk07_curbcheck.py` (load from `packs_dir`/`claims_dir`; missing/invalid file writes nothing) | Task 2 (stop-before-write); Task 3 (no directory `--packs`) |
| CHK-R02 | CHK-07 | `tests/test_chk07_curbcheck.py` (stdout only; `-j` dated file; `-o PATH`) | Task 2 |
| CHK-R03 | CHK-07 | `tests/test_chk07_curbcheck.py` (`created_curbpack()` + `curbcheck --defaults`) | Task 1 + Task 4 |
| CHK-R04 | CHK-07 | `tests/test_chk07_curbcheck.py` (id-list `--packs`/`--requirements`; `/` or `\` exits 2) | Task 3 |
| CHK-R05 | CHK-07 | `docs/reference/curbcheck-cli.md` describes R01–R04; pending banner gone | Task 5 |
| CHK-R06 | CHK-07 | Inventory below retargeted; `tests.test_curbcheck_package` / catalogue / listed suite argv green without a packs-directory `--packs` | Task 5 |

### CHK-R06 inventory (this plan)

Files that still assume a packs **directory** `--packs`, a single `curbpack` key, and/or a default undated `<curbpack>/run-result.json` write, and that this story updates:

| Path | What is wrong today | Task |
| --- | --- | --- |
| `tests/test_curbcheck_package.py` | CLI tests pass `--packs` as a directory; assert a default `run-result.json` write and `wrote {path}` | 2, 3, 4 |
| `tests/test_curbcheck_catalogue.py` | Does not pass directory `--packs` itself; it locks copied procedure text. EV.md argv in the catalogue must stay consistent after EV.md is updated | 5 |
| `docs/testing/README.md` | Suite argv uses `--packs` directory and `--out` | 5 |
| `docs/testing/strategy.md` | Same directory-override wording | 5 |
| `docs/testing/procedures/README.md` | Same argv; `curbpack.json` example missing §2.2 path fields | 5 |
| `docs/testing/procedures/1_pack_template_instantiation.md` | PF-01 still names `--packs docs/reference/test-packs` as a directory | 5 |
| `docs/testing/procedures/cases.md` | Carried cases still name `--packs docs/reference/test-packs` as a directory | 5 |
| `docs/testing/generated_test_record_template.md` | Argv still uses `--packs docs/reference/test-packs` | 5 |
| `tests/check/run.sh` | Runs `curbcheck --packs "$fixture/packs"` | 5 |
| `tests/check/automation/studio-pf01.sh` | Same directory `--packs` | 5 |
| `tests/check/suites/EV.md` | Copied procedure argv uses directory `--packs` | 5 |
| `tests/check/automation/ev.sh` | Comments describe `--repo/--packs/--out` as the JSON channel | 5 |
| `checks/ARCHITECTURE.md` | Still says CLI writes undated `run-result.json`; dated names marked CHK-07 | 5 |
| `docs/reference/curbcheck-cli.md` | Pending banner; directory `--packs`; always-write JSON | 5 |

Out of this story (do not retarget here): Studio Check/Review (`app/server.py`, `tests/test_check_editor.py`, review tests) — CHK-08. User guides (`docs/user-guides/developers.md`, `install.md`, `troubleshooting.md`), development CLI notes (`docs/development/cli.md`, `docs/development/ci.md`), and historical stories (`TST-01`, `VER-01`, `PK2-01`). `tests/test_m4_checks.py` Python `run_and_write(repo, packs_root, out)` — keep `packs_root` until CHK-08. Copied `curbpack check --packs` rows in `tests/check/suites/FS.md` / `PK.md` are the old product CLI, not this program.

## Tasks

### Task 0 — approve this plan

**Inputs / contracts:** CHK-07 story (decided 2026-10-29); `docs/reference/workspace.md` §§2–3; `docs/reference/packs2.md` §2.3 and §3.1; `docs/reference/curbcheck-cli.md`; `checks/__main__.py` `_cli`; `checks/run.py` `run_repository` / `run_and_write`; `discovery/door.py` `created_curbpack`; `tests/test_curbcheck_package.py`; inventory above.
**Change files:** `plan/CHK-07.md` only.
**Acceptance / stop:** human approval recorded, including OPEN-1–OPEN-6. No product code in this task.

- [x] Independent plan review completed.
- [x] Baseline observed; OPEN items recorded.
- [x] Plan approved (record approver).

### Task 1 — Defaults factory and `curbcheck --defaults`

**Requirements:** CHK-R03
**Files:** `checks/defaults.py` (new; `created_curbpack` and the created-file `search_hints` live here). `discovery/door.py` `created_curbpack` becomes a call-through to that function (no second document). `checks/__main__.py` `--defaults`. `tests/test_chk07_curbcheck.py` (new).
**Test first:** `created_curbpack()` with no overrides returns every required workspace.md §2.2 key. Path fields and `unsigned_requirements` match the created-file column / §2.3 example (`packs_dir` `curbpack/packs`, `claims_dir` `curbpack/claims`, `results_dir` `.curbpack`, `reports_dir` `curbpack/reports`, `unsigned_requirements` `"reject"`). `packs` is `[]`. `search_hints` matches the §2.3 created-file shape (sources documents+git; the exclude/prefer globs in that example). `curbcheck --defaults` (and `python3 -m checks --defaults`) from a directory that has **no** `curbpack.json` prints that same JSON on stdout, requires no repository, writes no run-result file, exits 0. `discovery.door.created_curbpack()` is the same object (Studio keeps importing door until CHK-08; it must not keep a second literal).
**Validation:** `python3 -m unittest tests.test_chk07_curbcheck tests.test_sys03_door.StudioConfigTest tests.test_curbcheck_package`
**Stop if:** the factory would need a key or created-file value that is not in workspace.md §2.2 / §2.3.

- [x] RED observed for the intended behavior (or existing PASS demonstrated).
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

### Task 2 — Output channels: stdout, `-j`/`--json`, `-o`/`--out`

**Requirements:** CHK-R02. Also the CHK-R01 “stop before writing” clause for a missing/invalid `curbpack.json`.
**Files:** `checks/__main__.py` `_cli`; `checks/run.py` (dated `run-result_<UTC>.json` helper used by the CLI only; do not change `app/server.py` `_new_run_result_path` — CHK-08). `checks/ARCHITECTURE.md` sentence that says the CLI writes undated `run-result.json` when `--out` is omitted (replace with CHK-R02: no file unless `-j`/`-o`). `tests/test_chk07_curbcheck.py`. Retarget `tests/test_curbcheck_package.py` tests that assume a default undated write: `test_omitting_packs_and_out_uses_the_directory_in_the_file`, `test_no_arguments_use_the_current_directory`. `--packs` may still be a Path in this task; those two tests already omit `--packs` and read `curbpack.json`.
**Test first:** A valid repo run with neither `-j`/`--json` nor `-o`/`--out` prints the existing text summary (claim/check lines, `claims N exit C`, dirty warning when applicable) and writes **no** run-result JSON anywhere under the repo (not `results_dir/run-result.json`, not a dated file). The same run with `-j` or `--json` still prints that summary and writes a new `{results_dir}/run-result_<YYYYMMDDTHHMMSSZ>.json`. A second `-j` run writes a second dated file and leaves the first byte-for-byte (drive or mock the clock so the two UTC second stamps cannot collide). The same run with `-o PATH` / `--out PATH` still prints the summary and writes the run-result object to `PATH` (relative or absolute; parent dirs created). `-j` plus `-o` writes both (OPEN-1). Missing `<repo>/curbpack.json`, or a file that fails workspace §2 validation, stops before any run-result file is written. Omit the `wrote {path}` stdout line when no JSON file is written; print it for each path that was written (OPEN-5).
**Validation:** `python3 -m unittest tests.test_chk07_curbcheck tests.test_curbcheck_package tests.test_m4_checks`
**Stop if:** JSON-on-stdout would be required, or a dated name other than `run-result_<YYYYMMDDTHHMMSSZ>.json` would be invented.

- [x] RED observed for the intended behavior (or existing PASS demonstrated).
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

### Task 3 — `--packs` / `--requirements` are id lists

**Requirements:** CHK-R04, remainder of CHK-R01 (CLI never takes a packs directory).
**Files:** `checks/__main__.py`; `checks/run.py` `run_repository` and `run_and_write` (optional **keyword-only** `pack_ids` / `requirement_ids` overlays; `run_and_write` must forward them so `-j`/`-o` plus those flags cannot drop the overlay; positional `packs_root` callers stay valid; do not write `curbpack.json`). `tests/test_chk07_curbcheck.py`. Retarget `tests/test_curbcheck_package.py` `test_skip_stores_the_reason` (today passes `--packs` as a directory plus `--out`) and `test_packs_and_out_still_override` (the latter becomes: a path-like `--packs` exits 2 and writes nothing; an id-list `--packs` still loads under `packs_dir`).
**Test first:** `--packs id-a,id-b` checks those pack ids and still loads `<packs_dir>/<id>/<version>/pack.json`. `--requirements req-a,req-b` checks those requirement ids and still loads claims from `claims_dir`. Either flag whose value contains `/` or `\` exits 2 and writes no run-result file. Without the flags, selection is the file’s `packs` / `requirements` / `exclude_requirements`. Overlays are in-memory only (OPEN-2, OPEN-3). `--packs` is no longer `type=Path`.
**Validation:** `python3 -m unittest tests.test_chk07_curbcheck tests.test_curbcheck_package tests.test_m4_checks`
**Stop if:** honouring the flags would need a new `curbpack.json` field or would write the file.

- [x] RED observed for the intended behavior (or existing PASS demonstrated).
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

### Task 4 — Studio door uses the checks factory (no second document)

**Requirements:** CHK-R03 caller clause. SYS-03 create dialog already calls `discovery.door.created_curbpack`; Task 1 made that a call-through. This task only fails if a second literal created-file document remains in Studio.
**Files:** confirm `app/server.py` / `demo_setup.py` still import `created_curbpack` from door (or switch them to `checks.defaults` if a second literal survived Task 1). `tests/test_chk07_curbcheck.py` asserts `discovery.door.created_curbpack is checks.defaults.created_curbpack` or that both return equal documents from the same function.
**Test first:** already covered in Task 1 if door is a call-through. If Task 1 left a copied dict in door, this task deletes the copy.
**Validation:** `python3 -m unittest tests.test_chk07_curbcheck tests.test_sys03_door`
**Stop if:** Studio UI would need to change (that is SYS-03 / CHK-08).

- [x] RED observed for the intended behavior (or existing PASS demonstrated).
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

### Task 5 — Rewrite `curbcheck-cli.md` and retarget the inventory

**Requirements:** CHK-R05, CHK-R06
**Files:** `docs/reference/curbcheck-cli.md` (remove the pending banner; describe path fields, stdout / `-j` / `-o`, `--defaults`, id-list `--packs` / `--requirements`; keep skip/exit-code/Check-id sections that remain true). Inventory rows in the table above, including `checks/ARCHITECTURE.md` CLI output sentence. Do not rewrite user guides or historical stories.
**Test first:** A doc/inventory assertion in `tests/test_chk07_curbcheck.py`: `curbcheck-cli.md` has no pending-CHK-07 banner, does not describe `--packs` as a directory, and names `-j`/`--json`, `-o`/`--out`, `--defaults`, and comma-separated ids. Catalogue still finds every suite id after EV.md argv is updated. Package tests and listed `docs/testing/` / `tests/check/` argv no longer require a packs-directory `--packs`.

**Fixture recipe (do not reinvent a directory `--packs`, do not set `packs_dir` to an absolute Studio path or a `..` segment — `validate_curbpack_config` rejects those):**

1. **Carried seven-claim run** (`tests/check/run.sh`, `docs/testing/*`, EV.md step 1, `install_pf01`): write a complete workspace.md §2.2 `curbpack.json` (created-file path fields + `unsigned_requirements` + `search_hints`; `packs` the three carried ids). Probe the clone fixture once: if `$REFERENCE_PRODUCT_ROOT/external_test/curbpack/packs/<id>/<version>/pack.json` already exists, set `packs_dir` to `external_test/curbpack/packs`. If that tree is unversioned (`<id>/pack.json` only), copy each selected pack into `$REFERENCE_PRODUCT_ROOT/curbpack/packs/<id>/<version>/` using `version` from that `pack.json`, and leave `packs_dir` at the created-file value `curbpack/packs`. Drop `--packs`. Keep the result location with `-o PATH` (today `run-result.json` at the product root, or `.curbpack/run-result.json` in `run_curbcheck_json`).

2. **Studio `docs/reference/test-packs` runs** (`install_house_claims`, `install_md_sw_class`, `install_claim`, `run_house_curbcheck_json`, `run_studio_packs_curbcheck_json`, `CURBCHECK_PACKS=$CURBPACK_ROOT/docs/reference/test-packs` in `suit-runner.sh` / `studio-pf01.sh`): that tree is `<id>/pack.json` (not versioned) and lives **outside** the product repo (EV-003 clone medtech pack is metadata-only; `fresh-owned-test` and `ev-008-order` exist only there). Before curbcheck, copy each needed pack directory into `$REFERENCE_PRODUCT_ROOT/curbpack/packs/<id>/<version>/` (`version` from `pack.json`; copy `pack.json` and the requirement `*.json` beside it). Write a complete §2.2 `curbpack.json` with created-file `packs_dir` `curbpack/packs` and the case’s `packs` ids. Delete `CURBCHECK_PACKS`. `run_curbcheck_json` calls `curbcheck --repo … -o "$_out"` with no `--packs`.

**Validation:** `python3 -m unittest tests.test_chk07_curbcheck tests.test_curbcheck_package tests.test_curbcheck_catalogue`
**Stop if:** a copied `curbpack check` procedure in FS/PK would have to be rewritten as if it were this program, or installing Studio packs would need a `curbpack.json` path that is absolute or contains `..`.

- [x] RED observed for the intended behavior (or existing PASS demonstrated).
- [x] Minimal implementation and GREEN verified.
- [x] Relevant regressions and review complete.
- [x] Checkpoint saved and verified local commit created.

## Open decisions

Proposals below are this plan’s intended implementation. They are not a new Packs v2 field. Stop rather than invent a different contract if review or the maintainer rejects one.

**OPEN-1 — `-j` and `-o` together.** Story and workspace.md list them independently (“also write”). **Proposal:** write the dated `results_dir` file and also write `PATH`.

**OPEN-2 — `--packs` ids not in the file’s `packs` array.** Story says this run checks those ids and still loads under `packs_dir`. **Proposal:** in-memory overlay replaces `config["packs"]` for this run. A missing version directory is the existing `ModelError`. The file is not written.

**OPEN-3 — `--requirements` when the file has `exclude_requirements`.** Both keys together are already invalid on disk. **Proposal:** in-memory overlay drops `exclude_requirements` and sets `requirements` to the CLI list for this run. The file is not written.

**OPEN-4 — `--defaults` plus run flags.** Story: no repository is required. **Proposal:** `--defaults` short-circuits: print the JSON, exit 0, do not run, do not write a run-result. Other flags are ignored.

**OPEN-5 — `wrote {path}` on stdout.** Today the CLI always prints it because it always writes. CHK-R02: stdout is the text summary even when no JSON is written. **Proposal:** print `wrote {path}` only for files this run actually wrote (once per `-j` file and once per `-o` path). Keep the claim/check lines unchanged.

**OPEN-6 — empty or whitespace tokens in an id list.** Story does not say. **Proposal:** split on comma, strip whitespace, reject a value that contains `/` or `\`, reject an empty token; exit 2, write nothing.

## Work log

- **2026-10-29 / Task 5:** CHK-R05 + CHK-R06. RED: `CliDocsTest` failed on the pending banner and directory `--packs` argv. GREEN: rewrote `curbcheck-cli.md`; retargeted listed `docs/testing/` and `tests/check/` argv; carried PF-01 copies fixture packs into `curbpack/packs/<id>/<version>/`; Studio test-packs use the same helper; `run_curbcheck_json` is `-o` only. Command: `python3 -m unittest tests.test_chk07_curbcheck tests.test_curbcheck_catalogue tests.test_curbcheck_package tests.test_m4_checks` — Ran 39 tests, OK. First review Important (`b8314f1f`): unversioned fixture as `packs_dir`; weak inventory regex. Fixed; re-review (`6c37faa8`) no Critical/Important. Minors: leftover `run.sh` copy duplication, inventory test does not lock §2.2 construction. `make test-curbcheck` not run in this step.
- **2026-10-29 / Task 4:** CHK-R03 caller clause. Already present: `discovery.door.created_curbpack is checks.defaults.created_curbpack`; `app/server.py` and `demo_setup.py` import that function, no second created-file literal. Command: `python3 -m unittest tests.test_chk07_curbcheck.DefaultsFactoryTest.test_studio_calls_the_same_defaults_function tests.test_sys03_door.StudioConfigTest` — Ran 2 tests, OK. No production diff. Independent review of Task 1 (`218c3e76`) already covered the call-through; no second review of an empty diff.
- **2026-10-29 / Task 3:** CHK-R04 + remainder of CHK-R01 (CLI never takes a packs directory). RED: `--packs cra-baseline` was treated as a Path (`cra-baseline/cra-baseline`); `--requirements` unrecognized; path `--packs` still exited 0. GREEN: `_id_list` rejects `/`, `\\`, and empty tokens (exit 2); `run_repository` / `run_and_write` take keyword-only `pack_ids` / `requirement_ids` overlays; CLI always passes `packs_root=None`. Command: `python3 -m unittest tests.test_chk07_curbcheck tests.test_curbcheck_package tests.test_m4_checks` — Ran 34 tests, OK. First review Important (`e5792d1a`): comma-separated success argv missing; house-policy fixture had the wrong `pack_id`. Fixed; re-review (`3bb6d6f6`) no Critical/Important. Minors left: package test name leftover, no OPEN-6 empty-token test, `--requirements` does not prove OPEN-3 exclude replacement.
- **2026-10-29 / Task 2:** CHK-R02 + CHK-R01 stop-before-write. RED: stdout-only tests failed because the CLI still wrote `run-result.json` and printed `wrote`; `-j`/`-o` were unrecognized. GREEN: `_cli` runs `run_repository`, writes only with `-j` (dated `results_dir` file) or `-o PATH`; both write both. `new_run_result_path` in `checks/run.py`. Command: `python3 -m unittest tests.test_chk07_curbcheck tests.test_curbcheck_package tests.test_m4_checks` — Ran 30 tests, OK. Review (`bd045bdc`) no Critical/Important. Minor fixed: captured stdout on the two leaky tests; parser description no longer says it always writes JSON. `app/server.py` dated helper untouched.
- **2026-10-29 / Task 1:** CHK-R03. RED: `python3 -m unittest tests.test_chk07_curbcheck` — Ran 3 tests, 3 errors (`No module named 'checks.defaults'`). GREEN: `checks/defaults.py` `created_curbpack`; `discovery.door.created_curbpack` is that function; `curbcheck --defaults` prints `dump_text` of it and exits 0 before repo resolution. Command: `python3 -m unittest tests.test_chk07_curbcheck tests.test_sys03_door tests.test_curbcheck_package` — Ran 32 tests, OK. First review (`218c3e76`) no Critical/Important. Minor: dropped unused `CREATED_SEARCH_HINTS` re-export from door. Task 4 caller clause is already satisfied by the `assertIs` check.
- **2026-10-29 / Task 0:** Inspected `checks/__main__.py` `_cli` (`--packs` Path, always `run_and_write` to undated `results_dir/run-result.json`, no `--defaults`/`-j`/`--requirements`). `run_repository` already resolves `packs_dir`/`claims_dir` from `curbpack.json`. `created_curbpack` is in `discovery/door.py`. Baseline `python3 -m unittest tests.test_curbcheck_package tests.test_curbcheck_catalogue tests.test_m4_checks` — Ran 23 tests, OK. Drafted this plan from `plan/TEMPLATE.md`. Unrelated WIP left uncommitted. First plan review Issues Found (`4008c220`): Task 3 named non-existent `test_cli_skip`. Fixed to `test_skip_stores_the_reason`. Added `docs/testing/procedures/cases.md` and `docs/testing/generated_test_record_template.md` to the CHK-R06 inventory. Folded advisory notes: keyword-only overlays, `--defaults` from a directory without `curbpack.json`, clock for two `-j` stamps. Re-review Issues Found (`bf9235f5`): Task 5 had no recipe for Studio `docs/reference/test-packs` (outside the product repo, unversioned `<id>/pack.json`). Fixed: copy into `$REFERENCE_PRODUCT_ROOT/curbpack/packs/<id>/<version>/`; `run_and_write` forwards overlays; ARCHITECTURE CLI sentence moves to Task 2; `docs/development/cli.md` / `ci.md` recorded out of scope. No third review.
