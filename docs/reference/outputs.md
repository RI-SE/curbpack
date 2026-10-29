# Outputs reference

This page owns the run-result and review-report JSON structures and their interpretation. It describes the current output. Changes to these output contracts belong here. Pack, Requirement, Claim, Check, and signature definitions remain in [Packs v2](packs2.md). Directory configuration and filename policy are defined in [Workspace](workspace.md) §2–§3. The Check-tool response and Pack export/publication layouts are also described below. CLI arguments, terminal output, and exit codes are defined in [curbcheck](curbcheck-cli.md).

## Primary artifacts

| Artifact | Path relative to the product repository | Producer |
| --- | --- | --- |
| Run result | `<results_dir>/run-result_<YYYYMMDDTHHMMSSZ>.json` | Check page, or `curbcheck -j` / `--json` |
| Explicit run result | The path passed to `-o` / `--out` | `curbcheck` |
| Review report | `<reports_dir>/review-report_<YYYYMMDDTHHMMSSZ>.json` | Compile on `/review` |
| Review PDF | Explicit `--out` path | `compile-pdf.py` from a saved review report |

`results_dir` and `reports_dir` come from the product's `curbpack.json`. Created-file defaults are `.curbpack` and `curbpack/reports`. A run-result JSON file is written by the CLI only when `-j` or `-o` is requested. Without those flags the CLI prints a text summary. The Check page writes a new dated run-result file. Compile writes a new dated review-report file.

## Run result

One JSON object describing the repository state checked, the loaded Packs, and the outcomes of the selected Claims' Checks. `validate_run_result` in `common/validate.py` validates the object before it is saved.

### Top-level fields

| Field | Meaning |
| --- | --- |
| `commit` | Git HEAD at the run's repository snapshot. Present only together with `worktree`. |
| `worktree` | `clean` or `dirty` at that snapshot. Present only together with `commit`. |
| `packs` | Array of loaded Requirement collections. Each entry has `id`, `version`, and `digest`. |
| `tool` | `curbcheck`. |
| `tool_version` | Checker build string. The observed example below uses `0.0.1a`. |
| `claims` | Array of evaluated Claim rows. May be empty; an empty result is not successful verification. |

### Pack entries

| Field | Meaning |
| --- | --- |
| `id` | Loaded Pack id. |
| `version` | Publisher's version label from the loaded `pack.json`. |
| `digest` | Digest of the loaded Pack directory. |

A loaded Pack may have no Claim rows. Selection of a Pack does not create Claims or demonstrate that its Requirements have been fulfilled.

### Claim rows

| Field | Meaning |
| --- | --- |
| `id` | Claim id, not a separate Requirement-id field. |
| `digest` | Version digest of the whole Claim with its entire `signed` block removed, using Packs v2 §2.6. |
| `status` | Aggregate of the nested Check outcomes: `fail` if any failed; otherwise `skipped` if any was skipped; otherwise `pass`. |
| `checks` | One result per configured Check, including passing Checks. |

The Claim's `requirement_id`, source, rationale, and signature are in the Claim object, not duplicated on the result row. Claims with `checks: []` and Claims outside the selected Requirements are omitted by the repository runner. A selected Requirement without an executed Claim produces no row.

### Check results

| Field | Meaning |
| --- | --- |
| `index` | Zero-based index in the Claim's configured `checks[]` array. |
| `check` | Check id, such as `exist` or `contents`. |
| `args` | The configured arguments used for this Check. Shapes are defined in Packs v2 §4 and the Check registry. |
| `status` | `pass`, `fail`, or `skipped`. |
| `detail` | Explanation, required and non-empty for `fail` and `skipped`; omitted for `pass`. |

### Example structure

Simplified from `run-result_20261029T135239Z.json`: one Pack, one Claim, and one Check. Digests and commit are abbreviated placeholders; this is a format example, not the original run.

```json
{
  "commit": "<HEAD>",
  "worktree": "dirty",
  "packs": [
    { "id": "house-policy", "version": "0.1.0", "digest": "<pack digest>" }
  ],
  "tool": "curbcheck",
  "tool_version": "0.0.1a",
  "claims": [
    {
      "id": "HOUSE-SECURITY-MD",
      "digest": "<claim digest>",
      "status": "pass",
      "checks": [
        { "index": 0, "check": "exist", "args": { "paths": ["SECURITY.md"] }, "status": "pass" }
      ]
    }
  ]
}
```

A failed Check also carries `detail`, for example `"detail": "SECURITY.md is absent"`, and has `"status": "fail"`. The filename carries the output timestamp; there is no run timestamp field in the JSON.

### Status and provenance

`commit` and `worktree` are present together when `git rev-parse HEAD` and `git status --porcelain` both succeed, and omitted together otherwise. `worktree` is `clean` or `dirty` according to uncommitted local changes. A dirty run is allowed, but it must not be presented as verification of the referenced commit's exact content. `packs[]` identifies loaded Requirement collections by `id`, their local `pack.version`, and directory digest. It does not report `origin.version`. `tool` and `tool_version` identify the checker build; Check types do not have independent version fields in the Claim format.

There is **one result entry per executed Claim**, with a `checks[]` result for **each configured Check**, including passes. Each Check result includes `index`, `check`, the `args` used, `status`, and a `detail` when required. `index` disambiguates repeated Check ids and is interpreted only together with the Claim `id` and `digest`.

Each Check status is `pass`, `fail`, or `skipped`. A missing required file is `fail`; unavailable/unsupported execution must be explicit and non-passing. `detail` is omitted for `pass`, required for `skipped`, and included for `fail` to explain the cause. `skipped` is never `pass`.

The enclosing Claim status is **`fail` if any Check fails; otherwise `skipped` if any Check is skipped; otherwise `pass`**. No Claim with empty Checks is evaluated or reported as a passing Claim. Process exit is 0 only when at least one Check actually executed and every included Claim and Check passed. Otherwise it is nonzero; exit code is not a JSON field. These are mechanical Check outcomes, not legal compliance judgments.

The run result references the Claim digests actually executed. A compiler or reviewer must not silently associate a result with a newer Claim carrying the same `id` but a different digest. If the exact Claim version cannot be retrieved, report the provenance gap rather than claiming that a changed Claim was checked. The later Review Report reports these outcomes and separately provides an appendix of **unsigned Claims** and **Claims with unverifiable signatures** within the reported/published Claim set, naming the related Requirement ids and Claim ids. Unpublished, unchecked researcher proposals are outside that report scope. Missing or invalid signatures must not be silently converted into failed Check outcomes. This appendix belongs to the review/reporting output, **not** the `curbcheck` run-result JSON.


## Review report

Compile copies an existing run result into one JSON object together with the Requirements and Claims needed to review it. It does not execute Checks or change their outcomes. `validate_report` validates the report before it is saved.

| Field | Meaning |
| --- | --- |
| `run_result` | The existing [run result](#run-result), copied into the report. |
| `requirements` | Requirements named by the Claims that ran, in the order their ids first appear. |
| `claims` | The Claims that ran, one per run-result row, in row order. |
| `appendix` | List of evaluated Claims that are unsigned or whose signature does not verify. Each entry has `id`, `requirement_id`, and `reason`. |
| `decision` | The reviewer's words. Absent until saved. |
| `signed` | Report signature, absent until signed. Same `at`, `name`, and `signature` shape as Packs v2 §2.6. |

Unknown report keys are rejected. A report may contain a run with failed or skipped Checks. Producing the report does not turn that run into a pass.

Compile rejects a missing run result, a missing Claim or Requirement needed for the report, a Claim digest that differs from the result row, or a nested Check that differs from the Claim configuration. It does not rewrite the live Claim or Requirement files. A failed compile leaves existing report files in place.

### Verified compilation

The Compile function was checked against `run-result_20261029T135239Z.json` and the test product's current Claim and Requirement files. The generated report contained 13 Claims, 13 Requirements, and 13 appendix entries. Its embedded `run_result` was unchanged. It had no `decision` or `signed` field and passed report validation after writing and reloading. This check used an empty certificate trust map; the appendix is not a verification against a configured Studio trust store. The generated report was temporary, outside the product repository.

## Review PDF

```sh
python3 compile-pdf.py --report /path/to/review-report.json --out /path/to/review-report.pdf
```

Install runtime dependencies from `requirements.txt` first. The output parent directory must exist. Exit 0 means the PDF was written, 1 means rendering or input failed, and 2 means invalid command-line arguments. An existing output is refused and left unchanged.

The PDF presents the saved JSON report in monochrome: run metadata and outcome counts, loaded Packs, Requirements with source passages, their Claims and Check results, recorded signature gaps, reviewer decision, and signature metadata. Everything is visible without buttons or expanding sections. It uses the embedded historical objects and does not open product evidence or run Checks. The input JSON is unchanged.

The PDF is a readable companion to the original report. It does not independently verify signatures, and the JSON signature does not cover the PDF bytes. Keep the original JSON for verification. Implementation: `compile/pdf.py`; ownership: [Compile architecture](../../compile/ARCHITECTURE.md).

## Check-tool response

The runner invokes each registry command as:

```text
<command> <check-id> --repo <path> --args <JSON object>
```

The tool writes one JSON object to stdout:

```json
{"status": "pass"}
```

or:

```json
{"status": "fail", "detail": "SECURITY.md is absent"}
```

These responses have no Claim id, digest, index, or copied arguments. The runner adds that context in the [Check result](#check-results). `skipped` is produced by the runner for a skipped Claim, rather than by these tool handlers.

The shipped tool wrapper exits 0 after writing either response; argument-parser errors exit 2. The runner accepts a pass only with both `status: pass` and process exit 0. A failed response with a non-empty `detail` is preserved. An unavailable command, invalid JSON, or other unusable response becomes a failed Check. The implementation is `checks/toolmain.py` and `checks/dispatch.py`. Repository-level exit codes are defined in the CLI reference.

## Pack export and publication

These outputs contain Pack and Requirement objects defined in Packs v2; they do not introduce another JSON schema.

| Action | Current output | Meaning |
| --- | --- | --- |
| Export Pack | `<destination>/<pack-id>/pack.json` and the working copy's other top-level `*.json` files | Copies the file bytes unchanged. Does not publish a release or require all Requirements to be signed. The destination directory must already exist. |
| Publish release | `<workspace>/published/<pack-id>/<version>/pack.json` and the working copy's other top-level `*.json` files | Requires verifiable Requirement signatures and Pack seal, and refuses an existing release version. |

Export refuses an existing `<destination>/<pack-id>` unless overwrite is explicitly selected. Overwrite replaces that directory rather than merging files. Subdirectories are not copied by these operations. The implementation is `requirements/workspace.py` (`export_pack` and `publish_pack`).

The export directory currently has no version segment. The product Pack-tree contract is `<packs_dir>/<pack-id>/<pack-version>/` (Workspace §2); Export does not itself install the directory into that layout. Neither operation creates a run result or review report.

## Production and review

| Action | Output behavior |
| --- | --- |
| `curbcheck` | Prints a text summary. `-j` adds a new dated JSON file under `results_dir`; `-o PATH` writes the same object to that path. Both flags may be used together. |
| Check page | Writes a new dated run-result JSON under the selected product's `results_dir`. Leaves existing review reports in place. |
| Compile | Reads the current dated run result under `results_dir` and writes a new dated report under `reports_dir`. Does not re-run Checks or overwrite the previous dated report. |
| Open Review | Reads the selected report, or the latest dated report when none is selected. Opening the page does not write a report. |
| Save decision | Updates the selected report's `decision` and removes that report's `signed` block. Embedded Claim and Requirement signatures remain. |
| review-sign | Requires a saved decision and signs that same report. |

A finished CLI run can write JSON even when Checks failed or were skipped, or no Check ran. A run that stops before saving leaves an existing output file in place. The process exit code is not a JSON field; see [curbcheck — Exit codes](curbcheck-cli.md#exit-codes).

A passing Check records a mechanical outcome for its arguments and the evaluated repository state. Curbpack prepares review material; the reviewer decides what it means. A Requirement Pack defines Requirements; the review report contains the material assembled for human review.
