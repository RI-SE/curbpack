# CLI disposition

Temporary maintainer note. Delete `docs/development/` when this crosswalk is no longer needed. The user guides do not link here.

The previous product's binary was `curbpack`. Its commands covered environment setup, repository inspection, handoff, receiving a review pack, and pack maintenance. The normal path was `scan`, `init`, `check`.

Studio does not provide that binary. The jobs that still exist have a page or `curbcheck`. The jobs that do not exist are listed here so they are not rediscovered as missing features.

Packs v2 is the contract for the objects those jobs read and write. See [the product flow](../reference/packs2.md).

## Command overview

| Command | What it did | Studio |
| --- | --- | --- |
| `curbpack` with no command | `doctor` when uninitialized, otherwise `check` | No default command. `make start` or `python3 -m app` starts the UI. Check is a separate action. |
| `curbpack doctor` | Inspect the local installation. `--repair` fixed local settings and did not download a binary. Missing binary exited 2. | No doctor. [Install](../user-guides/install.md) and [Troubleshooting](../user-guides/troubleshooting.md). |
| `curbpack demo` | Isolated sandbox check. Flags `--open`, `--keep`, `--out`. | **Prepare sample workspace** on the cover. It is a small demo workspace, not Glucose Log, and it does not become the Check Pack unless you select it. No `--keep`. |
| `curbpack scan` | Read-only diagnosis. Exit 0 even when evidence was missing. Alias `reality-check`. Flags `--packs`, `--badge`, `--format markdown`. From v0.5.3. | No scan. Discovery lists candidates. Check evaluates Claims. A finished Discovery is not a pass. |
| `curbpack init` | Wrote `.curbpack.json` and could add scaffold, hooks, IDE files. Flags `--profile house\|cra\|medtech`, `--packs`, `--workflow`, `--bare`, `--dry-run`, `--yes`, `--hooks` / `--no-hooks`, `--skill` / `--no-skill`, `--ide` / `--no-ide`. | No init. Write `curbpack.json` yourself. Pack Editor registers documents. Studio does not install hooks. |
| `curbpack check` | Evaluated composed rules. The repository gate. Exit 1 on gate failure. | **Run `curbcheck`.** `--repo` is required when the current directory has no `curbpack.json`. `--packs` and `--out` are optional. Exit 0 only when at least one Check ran and every row passed. Exit 1 otherwise. Exit 2 is a usage error from the argument parser. |
| `curbpack ask` | Explained a GateFailure. `--propose` suggested text. | No ask. Read the row detail, `law_text`, and `remediation_hint`. Nothing writes a proposed file from a failure JSON. |
| `curbpack fix` | Templated remediation, narrowly `--art14`, with preview and `--yes`. | No fix. Scaffold can write a new stub and refuses to overwrite. Automatic remediation is deferred. |
| `curbpack validate` | Full dual-representation gate. Shared many flags with `check`, including `--heal` and `--diff`. | No second gate. One run result is the evaluation. |
| `curbpack share` | Prepared the handoff. Flags `--skip-prepare-release`, `--bundle`, `--reveal`, `--as-of`, `--packs`. | **Compile** on `/review`. One report JSON. No bundle and no reveal switch. |
| `curbpack prepare-release` | Built `review-pack/` artifacts. `--allow-failing-gates`, `--out`, `--as-of`. | No review-pack build. Publish release in Pack Editor publishes a Requirements Pack. It does not build a buyer bundle, and it is not required to finish a product Check. |
| `curbpack ask-my-suppliers` | Supplier evidence checklist. `--stdout-only`, `--out`. | No supplier checklist generator. |
| `curbpack attest` | Human attestation, Git notes capsule. `--allow-dirty`, `--reviewed-by`. | Review `decision` and review-sign. Signing does not write a Git note and does not require a clean tree. A dirty tree must be described as dirty. |
| `curbpack drift` | Evidence-drift signals. Informational, always exit 0. `--json`. | No drift command. Keep the earlier report and run Check again. Review says `same run: yes` or `same run: no. This saved report is an older run.` |
| `curbpack review` | Offline triage of a review pack, or governed prose in a repo. States `confirmed`, `unconfirmed`, `contradicted`. Exit 1 when contradicted. `--verify-chain` exit 1 when the digest chain fails. Flags `--repo`, `--json`, `--full`, `--since`, `--batch`, `--edges`. | `/review` compiles and signs. It does not emit those three states. It does not verify a chain of review-pack digests. |
| `curbpack view` | Show the attest capsule for `HEAD`. | No capsule. The report file is the record. |
| `curbpack packs` | `list`, `update`, `import`, `export-graph`, `doctor`. | Pack Editor lists documents and publishes a working copy. No export-graph, no packs doctor, and no catalog button labeled Import. Copying a published directory unchanged is specified in the requirements architecture. It is not a control on the current catalog. |
| `curbpack export` | Context pack, buyer questions, SARIF, and other selections. `--holding-report` required `--since`. | No export command. The report embeds the run result, Requirements, and Claims. SARIF, SBOM, and VEX are not written. |
| `curbpack pathway` | Warm-start suggestions and human confirmation ticks. `status`, `suggest`, `confirm-packs`, `confirm-prose`, `confirm-share`, `note`. `--i-am-human` or `CURBPACK_ALLOW_CONFIRM=1`. `--agent` was a deprecated alias of `--technical`. | No pathway. Confirmation is signing a Requirement, a Claim, or a report. A typed name does not grant a role. |
| `curbpack research` | Citation material. `--fetch`, `--cite-check`, `--list-sources`, `--open-sources`, `--gate-id`. | No research command. Extract uses a configured adapter and can call a model to propose Requirements. Diagnostics stay outside the sealed Pack. |
| `curbpack completion` | Shell completion for `bash`, `zsh`, or `fish`. `-h` was a usage error because a shell argument was required. | No completion script. |
| `curbpack recover-lock` | Cleared a stale writer lock under a permitted output root. | No lock file and no recover command. |

## Flags that used to change `check`

| Flag | What it did | Studio |
| --- | --- | --- |
| `--heal` | Wrote stubs. Not part of CI. | No heal. Scaffold is a separate, optional write of a new file. |
| `--diff`, `--delta` | Incremental evaluation. `file_present` and `annex_file` still ran for the whole tree. Not for release. | No incremental mode. The selection in `curbpack.json` is the whole run. |
| `--as-of` | Fixed the clock for reproducibility. | `git_fresh` takes `as_of` on that Check's arguments. The runner does not have a global `--as-of`. |
| `--packs`, `--pack` | Selected packs for that invocation. | The product file `curbpack.json` selects ids. `--packs` on `curbcheck` is optional. It is the directory that contains those Packs, not a comma-separated id list. |
| `--score` | Scoring output. | No score flag. Optional Discovery assessment shows score and rank only when assessment ran. |
| `--json` | Machine-readable check output. | The run result file is the JSON. The process also prints a short text summary. |
| `--form-hints` | Form hints. | `discovery_hints` live on the Requirement. |
| `--apply-stub` | Applied a stub. | Scaffold, and only for a path that does not already exist. |
| `--skip` | Not the same as a rule waiver in the old CLI. | `--skip claim-id=reason` on `curbcheck`. The reason is stored. An empty reason writes nothing. The Check page has no skip form. |

## Aliases

| Old alias | Of | Studio |
| --- | --- | --- |
| `reality-check` | `scan` | No scan. |
| `help`, `-h`, `--help` | top-level help | `python3 -m app -h`, `curbcheck -h`, `make` with no target. |
| `version`, `-v`, `--version` | top-level version | No `curbpack version`. The run result has `tool` and `tool_version`. |
| `--delta` | `--diff` | No diff mode. |
| `pathway status --tech` | `--technical` | No pathway. |
| `pathway status --agent` | deprecated alias of `--technical` | No pathway. |
| `npm_dep_ban`, `manifest_dep_ban` | `dep_ban` | Still aliases in the Check registry. Not executed as a pass in this build. |

## Exit codes

The old global mapping was 0 success, 1 gate failure or a contradicted review, 2 usage or environment. Scan returned 0 when diagnosis finished. Drift always returned 0. `review --verify-chain` returned 1 when the chain failed. `doctor --repair` returned 2 when the binary was missing.

`curbcheck` uses 0, 1, and 2 as follows.

* 0: at least one Check ran, and every Claim and every Check passed. A dirty worktree does not change this.
* 1: a Check failed or was skipped, or no Check ran. A Claim whose Requirement is not selected raises before a result file is written. That failure is the exception text, not a formatted status line.
* 2: the process could not parse arguments, including a `--skip` value without `claim-id=reason`.

Do not map a Studio test's `[PASS]` onto these codes. `make test` can pass because a negative case failed as specified. That is the test runner, not curbcheck.

## Environment variables

`CURBPACK_PACKS_DIR` pointed at local v1 packs. `CURBPACK_ALLOWED_SIGNERS` had to be an absolute file outside the repository. `CURBPACK_SIGNER_ID` was supplied independently. `CURBPACK_ALLOW_CONFIRM=1` confirmed pathway ticks. `SOURCE_DATE_EPOCH` participated in the old `--as-of` clock.

Studio does not read those variables to select Packs, to sign, or to confirm a review. Pack selection is `curbpack.json` plus the `--packs` directory. Signing uses the local key created for the person who signs. `git_signed` and `git_signer` take their trust input in Check arguments (`allowed_signers` or `openpgp`), which is Packs v2 §4.1, not an environment variable documented here as implemented behavior.

## Help text you will not see

Top-level `curbpack --help` listed workflow commands, advanced commands, and exit codes, and warned that `completion -h` was a usage error. None of that text is Studio's help. `curbcheck -h` documents `--repo`, `--packs`, `--out`, and `--skip`. `--packs` and `--out` are optional.
