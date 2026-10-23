# Checks architecture

Status: design decision for the check runner. Sentences that describe `poc2/checks/` are confirmed by that code. The contracts here are what implementation follows. `poc2/checks/` does not follow the alias rule yet.

Normative domain model: `docs/reference/packs2.md` in this repository, §2.5, §3.1, and §4. The run result and the check args are those structs. This file does not add a result shape.

Sibling documents:

- `poc2/doc/ARCHITECTURE.md` — how a run result joins the other activities, and the cover page.
- `poc2/review/ARCHITECTURE.md` — compile and final review. They read a run result. They do not produce one.
- `poc2/claims/ARCHITECTURE.md` — Claim files this runner reads. Claim sealing stays there.

`poc/` did not run these checks. Its review screen read a prepared `scan.json`.

## Responsibilities

The runner evaluates Claim files that the repo selects and writes one run result. A test or `python -m checks` calls the same functions. The page does not walk the tree, compare bytes, or decide `pass` / `fail` / `skipped`.

| Function | Caller passes | Returns |
| --- | --- | --- |
| `validate_check_args(check, args)` | Check id and args. | Raises `CheckError` or `ModelError`. Claims Editor calls this before it writes a Claim. |
| `run_claim(repo, claim)` | Product repo and one Claim. | One row. |
| `build_run_result(repo, claims, packs, *, skip=None)` | Claims, the pack rows below, and an optional map of claim id to skip reason. | A value `validate_run_result` accepts. |
| `run_repository(repo, packs_root, *, skip=None)` | Product repo and the directory that contains `<pack-id>/pack.json`. | The result and `process_exit_code`. Writes nothing. |
| `run_and_write(repo, packs_root, out, *, skip=None)` | Those, plus the output path. | Writes that path only after the result validates. Returns the result and the exit code. |
| `process_exit_code(result)` | A run result. | `0` or `1`. |
| `git_snapshot(repo)` | A directory. | `commit` and `worktree`, or absent when Git has no HEAD. |

`available_checks.json` is the registry of Check ids, commands, and args JSON Schemas. `validate_check_args` reads it. This build executes `exist` and `contents` in-process. A registered id with no in-process implementation, including `fresh`, `owned`, and `dep_ban`, is a non-passing Check result. An id absent from the registry is rejected when the Claim is saved.

The runner does not read `discovery_hints`, `note`, `remediation_hint`, or Claim `description`. It does not write Requirements, Claims, packs, or the review report.

## What the runner loads

`curbpack.json` selects packs and requirements (`packs2.md` §2.3). `run_repository` loads each `packs_root/<id>/pack.json` and the Requirement files beside it.

Each `packs` entry on the result is that pack's `id`, its `version`, and `pack_directory_digest` of that directory. `version` is the hand-set label. A missing pack directory, or a `requirements` id that is not in the loaded files, raises `ModelError` and writes nothing.

Selected ids are `requirements` when that key is set, otherwise every loaded id minus `exclude_requirements`. Both keys together are already rejected by `validate_curbpack_config`.

Every Claim file under the repo's `claims/` directory is loaded. A Claim whose `requirement_id` is not selected raises `ModelError` and writes nothing. A Claim with `checks: []` is omitted. A selected Requirement with no executed Claim produces no row. The runner does not invent a row for it.

`skip` is a map the caller builds for this run. A listed id marks every configured Check `skipped` and `run_claim` is not called. The reason is stripped and stored as each Check's `detail`. An empty reason raises `ModelError` and writes nothing.

## Run result

The JSON is `packs2.md` §3.1. `validate_run_result` is the check. `save_run_result` and `load_run_result` are the IO.

`tool` is `curbcheck` and `tool_version` is the PoC2 build string in `common.version`. Checks do not have versions of their own. The exit code is not a field. `process_exit_code` returns 0 only when at least one Check actually ran and every Claim and every Check is `pass`. Dirty does not change that. A result with no rows is not a successful verification, and the exit code is 1.

`commit` and `worktree` are present together when `git_snapshot` returns them, and omitted together otherwise. `worktree` is `clean` or `dirty` from `git status --porcelain`. A dirty result is a real result. The page says it is not verification of that commit's content. The runner does not refuse a dirty tree.

One result per executed Claim, including passes. `digest` is `version_digest` of that whole Claim. Claim `status` is `fail` if any Check fails, otherwise `skipped` if any Check is skipped, otherwise `pass`. Each configured Check has `index`, `check`, `args`, `status`, and `detail` when required. `detail` is omitted on `pass`, required on `fail` and `skipped`. A `pattern` probe fails when the expression matches.

The output path is an argument. The demo writes `<product-repo>/.curbpack/run-result.json`. That directory is temporary working data, not the durable review report, and the file is not inside the pack directory. A failed run leaves the previous file in place. A run does not write or delete the review report.

## Checks this build runs

`exist` and `contents` follow `packs2.md` §4. `validate_check_args` is the schema check. Paths are relative, and a path that escapes the repo raises `ModelError` before any row is written.

| Check | Observable result |
| --- | --- |
| `exist` | `pass` when every path is a file. Otherwise `fail`, and `detail` names each absent path. The bytes are not read. |
| `contents` | A missing file is `fail`, and `detail` says the file is absent. Probe failures are not added for that file. When every file is present, each probe runs, and the first failures are joined into `detail`. `pass` has no `detail`. |
| `token` probe | The file contains the repo directory name, a `package.json` `name`, or a `go.mod` module line. |
| `placeholder` probe | The file matches one of the patterns in `checks/run.py`. That list is this build's list. |
| `headers` probe | Each string is a literal substring. |

`fresh`, `owned`, and `dep_ban` are specified in `packs2.md` §4 and are not implemented. `npm_dep_ban` and `manifest_dep_ban` are aliases of `dep_ban`, so they use the same not-implemented error. Any other id is an unknown check type. Both errors are `CheckError`, raised before a result file is written. The runner does not record them as `skipped`.

`file_present` is not a check id.

## UI

Checks owns this rendering. Target path: `poc2/checks/ui/`. Until migration the page still renders from `poc2/app/pages.py` `check_page`. The route stays in `app/`.

The check page renders a run result and posts a run. It does not decide status.

**Shown.** The rows: claim id, check index, check, status, detail. The exit code from `process_exit_code`. When `commit` is present, the commit and `worktree`. When `worktree` is `dirty`, the page states that the result is not verification of that commit's content. Pack id, `version`, and digest from `packs`. An empty row list states that the run is not a successful verification.

**Actions.**

| Action | Function | Result on the page |
| --- | --- | --- |
| Run | `run_and_write` for the open repo and packs root. | The new result. The review report file is left as it was. |
| Skip and run | The same call, with `skip` built from the claim id and the reason the person typed. | A `skipped` row whose `detail` is that reason. |
| Open the Claim | Navigation. | Claims Editor for that id. |

A `CheckError` or `ModelError` is the red error, and the previous result file stays. The page has no field for a legal conclusion. `skipped` is shown as its own status.

## PoC1

PoC1's review queue and the SCAN panel read `poc/components/review/scan.json`. Statuses there are prepared data. Nothing in that screen evaluated a working tree. The behaviour worth keeping from that demo is on the review page: failed rows stay visible. It is specified in `poc2/review/ARCHITECTURE.md`. The fake scan file, the fake wait, and `file_present` are not part of this runner.

## Acceptance tests

Direct calls, no UI. `tests/test_m4_checks.py` already covers the `exist` and `contents` rows below.

1. A missing file is `fail` on `exist` and on `contents`. The `contents` detail says the file is absent and does not mention a header.
2. A short file, or a file missing a header named in `args`, is `fail` on `contents`. A file that meets every probe is `pass` with no `detail`.
3. Two Checks on one Claim produce one row with two indexed Check results. A second Claim for other evidence produces a second row. A Claim with no Checks is omitted. A Claim whose Requirement is not selected raises, and no result file is written.
4. `skip` with a reason writes `skipped` and does not read the file. An empty reason raises and does not write. A skip id that is not a Claim in this run raises and does not write. A result whose only row is `skipped` exits 1. A result with no rows exits 1.
5. `fresh`, `owned`, `dep_ban`, `npm_dep_ban`, and `manifest_dep_ban` are registered and produce a non-passing Check result. An unknown id is rejected by `validate_check_args`. Neither is a pass.
6. A Git repo records `commit` and `worktree`. A dirty tree can still exit 0 when every row is `pass`. A directory that is not a Git checkout omits both keys.
7. The written file passes `validate_run_result` and round-trips through `load_run_result`.

## Current code

`exist`, `contents`, nested results, the exit code, and the Git snapshot match this file. A skip reason is stored as each Check's `detail`. A skip id that matches no Claim is ignored. Registered ids without an in-process implementation fail that Check and do not pass. The check page has no skip form. The Check action deletes the review report after a successful run; this is a **verified implementation defect** contradicting the normative contract in `poc2/review/ARCHITECTURE.md`. A corrective implementation change and regression test must preserve the report. Checks do not compute Discovery candidate-grey-out; the Claims UI derives that from an existing run result.

## Unresolved

None. `fresh`, `owned`, and `dep_ban` wait for implementation of the schemas `packs2.md` already states. They are not a new result field.
