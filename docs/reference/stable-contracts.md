# Stable contracts

The Review page and a recipient may rely on this shape. An unknown key is rejected, and the file is not written.

Code cites: [`review/compile.py`](../../review/compile.py) · [`common/validate.py`](../../common/validate.py).

## Review report (Compile)

Compile (`POST /review/compile`) writes `<product-repo>/docs/reports/review-report.json`. **Not** a product verdict or conformity assessment. `validate_report` checks the object before the file is written.

| Contract | Rule |
|----------|------|
| Path | `<product-repo>/docs/reports/review-report.json` |
| Object | One JSON object: `run_result`, `requirements`, `claims`, `appendix`. `decision` and `signed` only when recorded |
| `run_result` | The run that was reviewed. Compile copies it. `validate_run_result` checks the copy |
| Run result fields | `packs`, `tool` (`curbcheck`), `tool_version`, `claims`. `commit` and `worktree` (`clean` or `dirty`) are present together only when `git rev-parse HEAD` and `git status --porcelain` both succeed, and omitted together otherwise. `tool_version` is the build string; in this tree, `0.0.1a`, from `common/version.py`. The validator requires `tool` and `tool_version` to be non-empty strings |
| `packs[]` entry | `id`, `version`, `digest` |
| Claim row | `id`, `digest`, `status`, `checks`. `status` is `fail` if any Check failed, otherwise `skipped` if any Check was skipped, otherwise `pass`. Each row has one or more Check results |
| Check result | `index`, `check`, `args`, `status` (`pass`/`fail`/`skipped`). `index` is that Check's position in `checks`, starting at 0. `detail` is omitted on `pass` and required on `fail` and `skipped` |
| `requirements` | Requirements named by the Claims that ran, in the order those ids first appear |
| `claims` | The Claims that ran, one per run-result row, in row order |
| `appendix` | Always a list. Each item is `id`, `requirement_id`, `reason`. Executed Claims that are unsigned or whose signature does not verify |
| `decision` | The reviewer's words. Absent until they are saved. A non-empty string |
| `signed` | `at`, `name`, `signature`. Absent until `review-sign`. Requires a saved `decision` |
| Unknown keys | Rejected, including `packs`, `git_note`, `limits`, `exit`, `compliant`, and `meets_cra`. The file is not written |
| Replace | An existing file is replaced only when the form sends `confirm=yes`. The previous `decision` is not copied |
| Check run | A Check run leaves the report file as it was |
| No result | Compile writes nothing when no run-result file is loaded, or when no pack directory is available to load. The error names `run_result` |
| Mismatch | Compile leaves the previous report file in place when a row's Claim file is missing, when that Claim's digest does not match the row, or when a nested Check does not match the row |
| Open `/review` | When no report file exists, the page shows a preview and does not write |
