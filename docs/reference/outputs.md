# Outputs reference

## Scope

* Output artifacts, schemas, and documented production points only.
* Compact reference format; no workflow tutorial content.

## How the outputs relate

`curbcheck` evaluates the current repository state against the selected packs and reports whether the Checks pass, fail, or were skipped. Compile creates the review report from that result.

```text
selected packs
        +
product repository
        ↓
curbcheck
        ↓
pass / fail / skipped, with detail when a Check did not pass
        ↓
run result
        ↓
Compile
        ↓
docs/reports/review-report.json
        ↓
recipient / reviewer
```

Compile does not perform a different evaluation from `curbcheck`.

A **pack** defines Requirements. Claims in the product repository select the Checks `curbcheck` evaluates.

A **review report** is different. It is the material Curbpack Studio prepares so that another person can review the result and its supporting evidence.

Curbpack Studio prepares review material. The reviewer decides what the result means.

## Primary artifacts

| Artifact | Format / path | Producer | Purpose |
| --- | --- | --- | --- |
| Run result | `<product-repo>/<curbpack>/run-result.json` from `curbcheck`; `<product-repo>/.curbpack/run-result.json` from the Check page | Check page or `curbcheck` | Result for the checked repository state |
| Review report | `<product-repo>/docs/reports/review-report.json` | Compile on `/review` | The run result together with the Requirements, Claims, and signature appendix for review |

`.curbpack/` is temporary working data. The review report is the durable file in the product repository. Its location is fixed in the review compiler.

## Review report

Compile on `/review` writes `<product-repo>/docs/reports/review-report.json`.

The review report is intended to be given to another person for review. It contains the run result together with material that helps the reviewer understand the result and inspect its supporting evidence.

The current implementation writes one JSON object. `validate_report` accepts these fields:

| Field | Purpose |
| --- | --- |
| `run_result` | The run that was reviewed. Compile copies it. |
| `requirements` | Requirements named by the Claims that ran, in the order those ids first appear |
| `claims` | The Claims that ran, one per run-result row, in row order |
| `appendix` | Executed Claims that are unsigned or whose signature does not verify |
| `decision` | The reviewer's words. Absent until they are saved. |
| `signed` | `review-sign`. Absent until the report is signed. |

`appendix` is a list on every compiled report. Each item is `id`, `requirement_id`, and `reason`. `signed` is `at`, `name`, and `signature`. Any other key is rejected, and the file is not written.

A review report can also be created for a repository that does not pass all Checks. Creating the review report does not change the run result.

Opening `/review` when no report file exists shows a preview and does not write. Replacing an existing report requires confirmation (`confirm=yes`). The previous `decision` is not copied. A Check run leaves the report file as it was. Compile leaves the previous report file in place when a row's Claim file is missing, when that Claim's digest does not match the row, or when a nested Check does not match the row.

## Check and Compile

`curbcheck` writes the run result:

```text
curbcheck --repo <product>
        ↓
<product>/<curbpack>/run-result.json
```

`--packs` and `--out` are optional. `--out` replaces that file. The Check page writes `<product-repo>/.curbpack/run-result.json`. A packaged `curbcheck` file takes the same arguments.

Check and Compile are separate actions. Compile builds the review report from the run result. It does not run Checks.

```text
Compile on /review
        ↓
docs/reports/review-report.json
```

Compile writes that file from the current run result, including a run whose Checks did not pass. It writes nothing when there is no run-result file to load, or when no pack directory is available to load; the error names `run_result`. An existing report is replaced only after confirmation.

Compile does not perform a different check from `curbcheck`.

## Reviewing a received review report

A recipient can inspect a received review report at:

```text
<product-repo>/docs/reports/review-report.json
```

This is the material contained in that file.

It is different from:

```bash
curbcheck --repo <product>
```

`curbcheck` evaluates the product repository against selected packs.

The review report is material that someone else has already prepared. The Review page records `decision` and can sign the report. It does not re-run Checks.

The file is one JSON object with the fields in [Stable output contracts](#stable-output-contracts).

## Stable output contracts

The run result is [Packs v2](packs2.md) §3.1. `validate_run_result` checks it before the file is replaced. `validate_report` checks the review report the same way. How the program is started is [curbcheck](curbcheck-cli.md). Pack selection and the conventional paths are [Configuration](configuration.md).

| Contract area | Value |
| --- | --- |
| Run result document | One JSON object: `packs`, `tool`, `tool_version`, `claims`. `commit` and `worktree` are present together when `git rev-parse HEAD` and `git status --porcelain` both succeed, and omitted together otherwise. `worktree` is `clean` or `dirty`. |
| `tool` | `curbcheck` |
| `tool_version` | The build string. In this tree, `0.0.1a`, from `common/version.py`. |
| `packs[]` entry | `id`, `version`, `digest` |
| Claim row | `id`, `digest`, `status`, `checks`. `status` is `fail` if any Check failed, otherwise `skipped` if any Check was skipped, otherwise `pass`. |
| Check result | `index`, `check`, `args`, `status`. `status` is `pass`, `fail`, or `skipped`. `detail` is omitted on `pass` and required on `fail` and `skipped`. |
| Process exit | The process status. The CLI summary prints it after a result has been written. |
| Run result path (Check page) | `<product-repo>/.curbpack/run-result.json` |
| Run result path (`curbcheck`) | `<product>/<curbpack>/run-result.json`, or the `--out` path when that flag is set. Parent directories are created. The file is replaced in one step after the result has been validated. |
| Review report path | `<product-repo>/docs/reports/review-report.json` |
| Review report fields | `run_result`, `requirements`, `claims`, `appendix`. `decision` and `signed` when recorded. |
| Appendix item | `id`, `requirement_id`, `reason` |
| `signed` | `at`, `name`, `signature` |

## Consumer-facing interpretation

| Output | Intended use |
| --- | --- |
| Run result | Machine-readable Check outcomes from `curbcheck` and the Check page; read by Compile |
| Review report | Material sent to a reviewer. `decision` and `signed` are recorded on that same file. |

## Exit and output behavior

| Command | Behavior |
| --- | --- |
| `curbcheck` | Exit `0` when at least one Check ran and every Claim and every Check is `pass`. A dirty worktree does not change this. Exit `1` when a Check failed or was skipped, when no Check ran, or when the run stops with an exception before writing. Exit `2` when the arguments could not be parsed, or `--skip` has no `=`. Exit `2`, and a stop before the result is saved, leave `--out` as it was. A finished run replaces `--out`, including a run that exits `1` because a Check failed or was skipped. After the file is written, stdout is a short summary. |
| Check page | `POST /check` writes `<product-repo>/.curbpack/run-result.json` through the same runner and leaves the review report as it was. A run that stops before the result is saved leaves the run-result file as it was. |
| Compile | `POST /review/compile` writes the review report from the current run result, including a run that did not pass. It writes nothing when no run-result file is loaded, or when no pack directory is available to load. An existing file is replaced only when the form sends `confirm=yes`. |
| Save decision | `POST /review` requires the report file, sets `decision`, and removes the report `signed`. |
| review-sign | `POST /review/sign` requires the report file and a saved `decision`, then writes `signed`. |

## Important distinction

The current terminology uses the word **pack** for two different things:

```text
pack
    ↓
defines Requirements. Claims select the Checks curbcheck evaluates.

review report
    ↓
generated material sent to a reviewer
```

They are separate concepts.
