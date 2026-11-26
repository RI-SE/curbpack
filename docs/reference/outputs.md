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
| `id` | Claim id. |
| `digest` | Claim digest: version digest of the whole Claim with its entire `signed` block removed, using Packs v2 §2.6. |
| `namespace` | Requirement namespace recorded on the Claim. Present on a new result. |
| `pack_id` | Pack id recorded on the Claim. Present on a new result. |
| `requirement_id` | Requirement id recorded on the Claim. Present on a new result. |
| `requirement_digest` | Requirement digest recorded on the Claim. Present on a new result. |
| `actual_digest` | Digest of the Requirement that resolved. Present for `match` and `stale`. Omitted for `missing`. |
| `binding` | `match`, `stale`, or `missing`. Separate from `status`. Present on a new result. |
| `status` | Aggregate of the nested Check outcomes: `fail` if any failed; otherwise `skipped` if any was skipped; otherwise `pass`. |
| `checks` | One result per configured Check, including passing Checks. A Check row does not repeat the binding fields. |

A new Claim row carries the Requirement identity, the recorded Requirement digest, the Claim digest in `digest`, and the binding status. `actual_digest` is included only when the Requirement resolves. A historical row with only `id`, `digest`, `status`, and `checks` still validates. Reading that file does not rewrite it. Claims with `checks: []` and Claims outside the selected Requirements are omitted by the repository runner. A selected Requirement without an executed Claim produces no row.

### Check results

| Field | Meaning |
| --- | --- |
| `index` | Zero-based index in the Claim's configured `checks[]` array. |
| `check` | Check id, such as `exist` or `contents`. |
| `args` | The configured arguments used for this Check. Shapes are defined in Packs v2 §4 and the Check registry. |
| `status` | `pass`, `fail`, or `skipped`. |
| `detail` | Explanation, required and non-empty for `fail` and `skipped`; omitted for `pass`. |
| `remediation_hint` | Optional guidance from the Check tool. A non-empty string on `fail` only. Omitted on `pass` and `skipped`. The runner copies the tool's string and does not invent, trim, or apply it. This is not the Requirement's `remediation_hint`. |

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
      "namespace": "RISE/House Policy Example",
      "pack_id": "house-policy",
      "requirement_id": "HOUSE-SECURITY-MD",
      "requirement_digest": "<recorded requirement digest>",
      "actual_digest": "<current requirement digest>",
      "binding": "match",
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

Each Check status is `pass`, `fail`, or `skipped`. A missing required file is `fail`; unavailable/unsupported execution must be explicit and non-passing. `detail` is omitted for `pass`, required for `skipped`, and included for `fail` to explain the cause. `skipped` is never `pass`. `remediation_hint` does not change that status. A historical result that omits it remains valid.

The enclosing Claim status is **`fail` if any Check fails; otherwise `skipped` if any Check is skipped; otherwise `pass`**. No Claim with empty Checks is evaluated or reported as a passing Claim. Process exit is 0 only when at least one Check actually executed and every included Claim and Check passed. Otherwise it is nonzero; exit code is not a JSON field. These are mechanical Check outcomes, not legal compliance judgments.

The run result references the Claim digests actually executed. A compiler or reviewer must not silently associate a result with a newer Claim carrying the same `id` but a different digest. If the exact Claim version cannot be retrieved, report the provenance gap rather than claiming that a changed Claim was checked. The later Review Report reports these outcomes and separately provides an appendix of **unsigned Claims** and **Claims with unverifiable signatures** within the reported/published Claim set, naming the related Requirement ids and Claim ids. Unpublished, unchecked researcher proposals are outside that report scope. Missing or invalid signatures must not be silently converted into failed Check outcomes. This appendix belongs to the review/reporting output, **not** the `curbcheck` run-result JSON.


## Review report

Compile copies an existing run result into one JSON object together with the Requirements and Claims needed to review it. It does not execute Checks or change their outcomes. `validate_report` validates the report before it is saved. The per-check decision `review_item` is defined in [Studio-internal](studio-internal.md).

| Field | Meaning |
| --- | --- |
| `run_result` | The existing [run result](#run-result), copied into the report. |
| `requirements` | Requirement versions recorded by the Claims that ran, in the order each version first appears. One Requirement id may appear more than once when Claims recorded different digests. A Claim is tied to the object whose digest is that Claim's `requirement_digest`. |
| `claims` | The Claims that ran, one per run-result row, in row order. |
| `appendix` | List of evaluated Claims that are unsigned or whose signature does not verify. Each entry has `id`, `requirement_id`, and `reason`. |
| `assessments` | Optional list of reviewer assessments on this run. Absent means no `accepted` or `must_fix` decision was copied. Each entry is one Check, or one `stale` or `missing` binding. A Check entry has `kind` `check`, `claim_id`, `claim_digest`, `index`, `disposition`, and `text`. A binding entry has `kind` `binding`, `claim_id`, `claim_digest`, `namespace`, `pack_id`, `requirement_id`, `requirement_digest`, `binding`, `disposition`, and `text`. On the page, `disposition` is `accept` or `must_fix`. `accept` applies only to a failed or skipped Check, or a `stale` or `missing` binding. `must_fix` applies to those and also to a Check whose technical status is `pass`. `text` is required for `accept` on a failing Check. Other assessments may leave `text` empty. `pass` and `not_assessed` add no assessment. An assessment does not change Check status, binding, or the embedded run result. `validate_report` still accepts an older Check entry whose `disposition` is `retire`, including a passing Check, and not a binding. That entry requires `text`. The Review page does not post it. Remediation Retire is `action` `retire` on `review_item`, not this field. |
| `remove_retired_checks` | Present only when an assessment has `disposition` `retire`. `true` or `false`. Absent on every other report. `true` means review-sign, after the report signature is written, removes those Checks from the live Claim files. A Claim with any Check left is signed again. A Claim with none left is deleted. `false` records the older choice and does not change Claim files. The Review page does not set this field. A report that already has it `true` still applies it at review-sign. The signature covers this field when it is present. |
| `decision` | The reviewer's words for the whole review. Absent until Sign writes the report. On the page these words are the Notes. Save stores them on `review_items.json` and does not write this field. |
| `items_digest` | Version digest of the sealed items object `{ "items": [ ... ] }` with `signed` removed. Sign writes that object as `review-report_<stamp>.items.json` beside the report. Present when Sign seals the items. The report signature covers this field. The signed items' `decision` values are what reporting reads. The working file `review_items.json` is not this object. |
| `signed` | Report signature, absent until signed. Same `at`, `name`, and `signature` shape as Packs v2 §2.6. The version digest is the report with `signed` removed, so `assessments`, `items_digest`, `decision`, and `remove_retired_checks` are covered when they are present. Reading uses `what` `review report`. |

Unknown report keys are rejected. A report may contain a run with failed or skipped Checks. Producing the report does not turn that run into a pass.

Compile rejects a missing run result, a missing Claim or Requirement needed for the report, a Claim digest that differs from the result row, or a nested Check that differs from the Claim configuration. Each embedded Requirement is a version whose digest is a Claim's `requirement_digest`. Claims that recorded different versions of one Requirement id each keep their own embedded object. A current Requirement with the same id and a different digest is not substituted for either of them. When a recorded version is not in the supplied Requirements, Compile recovers it from local Git history. If it cannot be recovered, Compile fails and names the recorded digest. It does not rewrite the live Claim or Requirement files. A failed compile leaves existing report files in place.

Assessments submitted with Compile are stored on the new report only. They are not copied onto another run. A report that has no `assessments` field remains valid. An unsigned report can be given a new `assessments` list. A signed report is unchanged.

Sign copies the working `review_item` decisions into that list. `accepted` is stored as `accept`. `must_fix` is stored as `must_fix`. `pass` and `not_assessed` are not stored. The sealed items file keeps the decisions themselves. See [Studio-internal](studio-internal.md).

### Verified compilation

The Compile function was checked against `run-result_20261029T135239Z.json` and the test product's current Claim and Requirement files. The generated report contained 13 Claims, 13 Requirements, and 13 appendix entries. Its embedded `run_result` was unchanged. It had no `decision` or `signed` field and passed report validation after writing and reloading. This check used an empty certificate trust map; the appendix is not a verification against a configured Studio trust store. The generated report was temporary, outside the product repository.

## Remedy report

Sign Off writes `remedy-report_<YYYYMMDDTHHMMSSZ>.json` in the Studio Check directory. It does not change the signed review report or the sealed review items. Reading the seal uses `what` `remedy report`. The version digest is the object with `signed` removed, the same rule as Packs v2 §2.6.

| Field | Meaning |
| --- | --- |
| `items` | The remediation copy of the `review_item` list at Sign Off. A `decision` here is the recommendation. It does not replace the signed review decision. |
| `remedy` | `true`. |
| `outside` | Present when this round acknowledged a Check outside the original deviations. Each entry has `run`, `checks`, and `choice`. `choice` is `ok` or `rolled_back`. Each check has `claim_id`, `check`, and `digest`. `studio`, when present, has `claim_id` and `check` for the Studio change the warning named. Absent when nothing was acknowledged. |
| `notes` | The round's words. Absent when empty. |
| `reference` | The Check and the signed review this work closes. `run` is the Check directory name. `review` is the signed review report's file name, or empty when that directory has none. `reviewer` and `reviewed_at` are copied from that report's `signed` block when it has one, and omitted otherwise. |
| `full_checks` | Names of the full Check runs recorded for this round. An empty list means none was recorded. |
| `signed` | Same `at`, `name`, and `signature` shape as Packs v2 §2.6. |

The page also writes `remedy-report_<stamp>.md` and `remedy-report_<stamp>.pdf` beside that JSON. The signature does not cover those bytes. Publish refuses a Markdown or PDF name that already exists.

## Review PDF

```sh
python3 compile-pdf.py --report /path/to/review-report.json --out /path/to/review-report.pdf
```

Install runtime dependencies from `requirements.txt` first. The output parent directory must exist. Exit 0 means the PDF was written, 1 means rendering or input failed, and 2 means invalid command-line arguments. An existing output is refused and left unchanged.

The PDF opens with a plain-language management summary: compact run identity, scope and counts, items needing follow-up, separate approval gaps, and the recorded reviewer decision. A failed Check that was retired is not counted as an outstanding correction. Review findings then list outstanding deviations that must be fixed or are not assessed, accepted deviations with their justification, retired Checks with the recorded result and the retirement justification, and passing Checks. A finding shows a failed or skipped Check, or a passing Check whose stored binding is `stale` or `missing`. It includes the checker's recorded reasons, a Check `remediation_hint` when the result has one, the Requirement `remediation_hint` when the embedded Requirement is the recorded version, the stored Requirement identity and digests, neutral questions for human review, and references to the detailed records. A passing Check stays `pass`. The PDF does not invent business risk, ownership, deadlines, or decisions.

Technical details follow on new pages in appendix tables: A — run metadata and loaded Pack versions/digests; B — a compact reviewed-item index, embedded Requirements/source passages, Claims/evidence, the stored binding, and indexed Check arguments/outcomes; C — recorded signature gaps and seal metadata. Tables repeat headers and split long records across pages. Everything is monochrome and visible without controls. The input JSON and historical grouping are unchanged; the exporter does not open live evidence or run Checks. Changes since the run and unresolved current evidence are explicitly not assessed.

The PDF is a readable companion to the original report. It does not independently verify signatures, and the JSON signature does not cover the PDF bytes. Keep the original JSON for verification. Implementation: `studio/compile/impl/pdf.py`. `compile/pdf.py` is the import `compile-pdf.py` uses. Ownership: [Compile architecture](../../compile/ARCHITECTURE.md).

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

A failing response may also carry the tool's own guidance:

```json
{"status": "fail", "detail": "SECURITY.md is absent", "remediation_hint": "Add SECURITY.md."}
```

`remediation_hint` is optional. When present it is a non-empty string. The runner copies that string onto the fail row, including surrounding spaces. A blank, whitespace-only, or non-string value is omitted. The Check still fails with the tool's `detail`. A pass response that includes the key is stored as `{"status": "pass"}`. Any other extra key is ignored. The runner does not write a hint of its own when the tool is missing, the response is unusable, or the arguments are invalid.

These responses have no Claim id, digest, index, or copied arguments. The runner adds that context in the [Check result](#check-results). `skipped` is produced by the runner for a skipped Claim, rather than by these tool handlers. A skip does not carry `remediation_hint`.

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
| Compile | Reads the posted run-result path. With a signer name, writes a new dated `review-report_<stamp>.json` in that Check's directory, or under `reports_dir` when the run is not a Studio Check directory. Copies posted assessments onto that report. Writes `remove_retired_checks` only when a posted assessment has `disposition` `retire`. The Review page does not post that disposition. Does not re-run Checks, edit Claim files, or overwrite a previous dated report. Without a signer name, writes no report. |
| Open Review | Lists the dated run results and review reports, and opens only the requested document. Opening the page does not write a report. |
| Save | Writes the decisions and the notes into that Check's `review_items.json`. Does not write a report and does not change a signature. A review that already has `review_locked` true, or a `signed` block on that file, is left unchanged. |
| review-sign | Page Sign is Compile with a signer name. It signs the new report, writes `review-report_<stamp>.items.json` as the sealed items, sets `review_locked` on `review_items.json`, and returns to Check. `pass` and `not_assessed` add no assessment. `accepted` is stored as `accept`. `must_fix` is stored as `must_fix`. POST `/review/sign` signs an already saved report. A signed report is not signed again. When that report has `remove_retired_checks` true, the same call removes those Checks from the live Claim files after the signature, or finishes the Claims a previous call did not update. A Claim with a Check left is signed again. A Claim with none left is deleted. `false` signs the report and does not change Claim files. A Claim that no longer matches the run blocks every write. If a Claim write fails after the report is signed, the report stays signed and a later review-sign finishes only the Claims that were not updated. Remediation Retire is a different action: it removes the Check when the action is taken and records `action` `retire` on `review_item`. See [Reviewing](../user-guides/reviewers.md). |
| Sign Off | Writes `remedy-report_<stamp>.json` in the Check directory, then the Markdown and PDF beside it. Sets `remedy_locked` on `review_items.json`. Does not change the signed review decisions. Returns to Check. |

A finished CLI run can write JSON even when Checks failed or were skipped, or no Check ran. A run that stops before saving leaves an existing output file in place. The process exit code is not a JSON field; see [curbcheck — Exit codes](curbcheck-cli.md#exit-codes).

A passing Check records a mechanical outcome for its arguments and the evaluated repository state. Curbpack prepares review material; the reviewer decides what it means. A Requirement Pack defines Requirements; the review report contains the material assembled for human review.
