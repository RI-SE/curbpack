# CLI Reference

Primary binary: `curbpack`.

Curbpack commands fall roughly into five parts of the workflow:

* environment and first use;
* repository inspection and checking;
* handoff and release preparation;
* receiving and reviewing material;
* advanced support tooling.

For the normal developer workflow, start with `scan`, `init`, and `check`. See the developer guide for the step-by-step workflow.

## Command overview

| Command                     | Purpose                                                            | Advanced |
| --------------------------- | ------------------------------------------------------------------ | -------- |
| `curbpack` (no command)     | Runs `doctor` when uninitialized, otherwise `check`                | No       |
| `curbpack doctor`           | Inspect the local Curbpack environment                             | No       |
| `curbpack demo`             | Run an isolated sandbox check                                      | No       |
| `curbpack scan`             | Inspect a repository without changing it                           | No       |
| `curbpack init`             | Add the initial Curbpack configuration and scaffolding             | No       |
| `curbpack check`            | Evaluate the repository against the selected packs                 | No       |
| `curbpack ask`              | Explain a GateFailure result                                       | Yes      |
| `curbpack fix`              | Write supported templated remediation material                     | Yes      |
| `curbpack validate`         | Run the full dual-representation gate path                         | Yes      |
| `curbpack share`            | Prepare the current result for handoff                             | No       |
| `curbpack prepare-release`  | Build review-pack artifacts                                        | No       |
| `curbpack ask-my-suppliers` | Generate a supplier evidence checklist                             | No       |
| `curbpack attest`           | Record a human Git Notes attest capsule                            | No       |
| `curbpack drift`            | Inspect evidence-drift signals                                     | No       |
| `curbpack review`           | Triage received review material or governed repository prose       | No       |
| `curbpack view`             | Show the attest capsule for `HEAD`                                 | Yes      |
| `curbpack packs`            | Inspect and maintain packs                                         | Yes      |
| `curbpack export`           | Generate specific Curbpack export artifacts                        | Yes      |
| `curbpack pathway`          | Manage warm-start suggestions, notes, and human confirmation ticks | Yes      |
| `curbpack research`         | Build and check citation material                                  | Yes      |
| `curbpack completion`       | Print shell completion scripts                                     | Yes      |
| `curbpack recover-lock`     | Recover a stale Curbpack writer lock                               | Yes      |

## Environment and first use

### `curbpack`

Running Curbpack without a command chooses the next basic action from repository state.

If the repository is not initialized, it runs `doctor`. Otherwise it runs `check`.

### `curbpack doctor`

Checks the local Curbpack environment.

```bash
curbpack doctor
```

Use `--repair` for local installation repair such as PATH or alias state:

```bash
curbpack doctor --repair
```

Repair is local only and does not download or update Curbpack. If the binary itself cannot be found, use the installer instead.

### `curbpack demo`

Runs Curbpack in an isolated sandbox.

```bash
curbpack demo
```

`--open` opens the generated result in a browser. `--keep` preserves the sandbox and `--out <path>` selects its output location.

The normal introduction to Curbpack is the getting-started guide and reference product; `demo` is a separate sandbox path.

## Repository workflow

### `curbpack scan`

Inspects the current repository without initializing Curbpack or writing repository files.

```bash
curbpack scan
```

Use it to see what Curbpack can observe before changing the repository.

A completed scan is **not** a passing Curbpack check. `scan` returns exit `0` when diagnosis completes even when findings remain.

`reality-check` is an alias for `scan`.

### `curbpack init`

Prepares a repository for the current Curbpack workflow.

```bash
curbpack init
```

Initialization creates `.curbpack.json` if it does not already exist and writes the selected scaffolding and integrations.

The default setup uses `house-policy` and enables hooks, skill, and IDE integration. Packs and initialization components can be selected explicitly with flags.

Scaffold created by `init` is starter material. It is not automatically valid product evidence.

### `curbpack check`

Evaluates the current repository against the selected packs.

```bash
curbpack check
```

This is the normal local repository gate. Its exit code is authoritative for the result.

`--heal` may create missing starter material. Any generated content must still be reviewed and replaced with information that is true for the product.

`--diff` (`--delta`) evaluates the delta path and is not release-gate safe.

### `curbpack ask`

Explains a GateFailure JSON result.

```bash
curbpack ask .github/curbpack/cache/latest_failure.json
```

With `--propose`, Curbpack can also provide proposed remediation guidance:

```bash
curbpack ask .github/curbpack/cache/latest_failure.json --propose
```

A proposal is guidance, not an automatic fix or an assertion that the proposed content is correct for the product.

### `curbpack fix`

Writes remediation material for explicitly supported cases.

Currently the documented path is:

```bash
curbpack fix --art14
```

The command shows the proposed content and, when replacing existing content, a diff before writing. In a non-interactive shell, `--yes` is required to write.

A generated file is still product material that must be reviewed. Running `fix` does not establish that a gate passes.

### `curbpack validate`

Runs the full dual-representation gate path.

```bash
curbpack validate
```

It supports most of the same evaluation controls as `check`, including JSON output, pack selection, healing, and delta evaluation.

This is an advanced gate path. `--diff` is not release-gate safe.

## Handoff and release

### `curbpack share`

Runs the current handoff recipe:

```text
check
  ↓
context-pack
  ↓
buyer-questions
  ↓
prepare-release
```

Run:

```bash
curbpack share
```

`share` does not introduce another evaluation model. It runs the check and prepares handoff artifacts from the result.

If the check is red, the command still writes a ContextPack representing that state, but the command exits non-zero.

`--bundle` also builds the evidence bundle. `--reveal` reveals the generated review material in the platform file manager.

### `curbpack prepare-release`

Builds the current `review-pack/` and associated evidence artifacts.

```bash
curbpack prepare-release
```

Normally this is reached through `curbpack share`, which runs the complete handoff recipe. Use `prepare-release` directly when only that stage is needed.

By default release preparation expects the relevant gates to pass. `--allow-failing-gates` explicitly permits generation from a failing state.

### `curbpack ask-my-suppliers`

Generates a checklist of information or evidence to request from suppliers.

```bash
curbpack ask-my-suppliers
```

By default the command can write supplier material under `review-pack/` as well as produce command output. `--stdout-only` suppresses file output and `--out <path>` selects an output path.

### `curbpack attest`

Records a human attest capsule using Git Notes.

```bash
curbpack attest
```

Attestation is deliberately human-only and must never be automated by an agent.

`--reviewed-by <name>` records the reviewer and `--allow-dirty` permits the supported dirty-tree path.

Attestation is separate from `check` and from generation of review material.

### `curbpack drift`

Produces an informational checklist of signals that may indicate evidence drift.

```bash
curbpack drift
```

For example, the report can identify that the repository has moved since the last attest or that generated review material may be stale.

`drift` is not a gate and always exits `0`.

## Receiving and review

### `curbpack review`

Reviews material without turning the result into a product verdict.

For a received review pack:

```bash
curbpack review review-pack
```

This mode performs offline triage and does not require Git or network access. Findings are classified as `confirmed`, `unconfirmed`, or `contradicted`.

For repository prose governed by pack `ProsePaths`:

```bash
curbpack review --repo
```

Repository mode is also write-free. `--packs` can override the configured pack selection.

To verify the digest relationship between two review records:

```bash
curbpack review --verify-chain <parent.json> <child.json>
```

This is an exclusive chain-integrity operation rather than document triage.

### `curbpack view`

Shows the attest capsule associated with the current `HEAD`.

```bash
curbpack view
```

This is a view operation; it does not create an attest.

## Pack and support tooling

### `curbpack packs`

Provides pack inspection and maintenance commands.

```bash
curbpack packs list
```

lists packs currently available to Curbpack.

```bash
curbpack packs import <directory>
```

imports local pack definitions for air-gapped use.

```bash
curbpack packs update
```

supports a pinned network update path only when both `CURBPACK_PACKS_URL` and `CURBPACK_PACKS_SHA256` are supplied. Network update is refused without a valid SHA-256 pin.

```bash
curbpack packs export-graph
```

writes the policy graph for the active packs.

```bash
curbpack packs doctor
```

reports pack validity, supersession, pin-skew, and citation-currency issues. It is diagnostic rather than a repository gate.

### `curbpack export`

Generates specific artifacts from the current Curbpack state.

Supported export selections include:

* `--sarif`
* `--explain-packet`
* `--watchlist-join`
* `--buyer-questions`
* `--lay-of-land`
* `--context-pack`
* `--holding-report`
* `--spdx`
* `--slsa`

Multiple export flags may be selected in one invocation.

These are output surfaces for review, integration, or handoff. They do not replace `curbpack check`.

### `curbpack pathway`

Maintains the warm-start pathway state used for pack suggestions, human checkpoints, and session notes.

The main subcommands are:

```text
status
suggest
confirm-packs
confirm-prose
confirm-share
note
```

`status` reports the current phase and next action.

`suggest` produces a closed-world pack proposal from the supplied answers; it does not invent arbitrary pack IDs.

The `confirm-*` operations are human-only. They require `--i-am-human` or `CURBPACK_ALLOW_CONFIRM=1`.

`note` stores session notes, corrections, and draft-selection state.

Pathway state does not affect `check` pass/fail.

### `curbpack research`

Builds an allowlisted citation packet and human research brief.

```bash
curbpack research
```

Optional `--fetch` retrieves supported source material.

After drafting, citation grounding can be checked with:

```bash
curbpack research --cite-check <draft.md>
```

`--list-sources` lists the allowlisted source IDs and URLs; `--open-sources` also attempts to open them.

Research is informational and never controls `curbpack check` pass/fail.

### `curbpack completion`

Prints a completion script for a supported shell:

```bash
curbpack completion bash
curbpack completion zsh
curbpack completion fish
```

The script is written to stdout so it can be installed using the normal mechanism for the selected shell.

### `curbpack recover-lock`

Recovers a stale Curbpack writer lock:

```bash
curbpack recover-lock <permitted-output-root>
```

Recovery only removes a lock whose recorded owner is known to have exited.

After recovery, rerun the interrupted command and verify its outputs.

## Key flags by command

* `doctor`: `--repair`.
* `demo`: `--open`, `--keep`, `--out <path>`.
* `scan`: `--packs a,b`, `--badge`, `--format markdown`.
* `init`: `--profile house|cra|medtech`, `--packs a,b`, `--workflow`, `--bare`, `--dry-run`, `--yes`, `--hooks/--no-hooks`, `--skill/--no-skill`, `--ide/--no-ide`.
* `check`: `--heal`, `--score`, `--json`, `--as-of <RFC3339|YYYY-MM-DD>`, `--packs a,b`, `--pack <id>`, `--diff` (`--delta` alias), `--form-hints`, `--apply-stub`.
* `ask`: `[file]`, `--propose`.
* `fix`: `--art14`, `--yes`.
* `validate`: `--json`, `--as-of <RFC3339|YYYY-MM-DD>`, `--packs a,b`, `--pack <id>`, `--diff`, `--form-hints`, `--apply-stub`, `--heal`.
* `share`: `--packs a,b`, `--skip-prepare-release`, `--bundle`, `--reveal`, `--as-of <RFC3339|YYYY-MM-DD>`.
* `prepare-release`: `--as-of <RFC3339|YYYY-MM-DD>`, `--pack <id>`, `--packs a,b`, `--out <path>`, `--allow-failing-gates`.
* `ask-my-suppliers`: `--packs a,b`, `--stdout-only`, `--out <path>`.
* `attest`: `--allow-dirty`, `--reviewed-by <name>`.
* `drift`: `--json`.
* `review`: `<received-pack>`, `--repo [path]`, `--packs a,b` in repo mode, `--json`, `--full`, `--since <prior-report.json>`, `--verify-chain <parent.json> <child.json>`, `--batch <path...>`, `--edges <edges.json>`. `--edges` requires `--repo --json`.
* `packs`: subcommands `list`, `update`, `import <directory>`, `export-graph`, `doctor`.
* `export`: one or more export selections plus `--out <path>`, `--packs a,b`, `--since <prior-report.json>`. `--holding-report` requires `--since`.
* `pathway`:

  * `status`: `--human`, `--technical` (`--tech` alias), `--agent` (deprecated alias of `--technical`)
  * `suggest`: `--product=...`, `--eu-docs=...`, `--medtech=...`, `--sector=...`, `--house-first=...`, optional `--ce-context=...`
  * `confirm-packs|confirm-prose|confirm-share`: `--i-am-human` or `CURBPACK_ALLOW_CONFIRM=1`
  * `note`: `--set|-s`, `--forget|-f`
* `research`: `--packs a,b`, `--gate-id <id[,id...]>` (`--gate-ids` alias), `--fetch`, `--cite-check <draft.md>`, `--list-sources`, `--open-sources`.
* `completion`: positional shell `bash|zsh|fish`.
* `recover-lock`: positional `<permitted-output-root>`.

## Aliases

* `scan` alias: `reality-check`.
* Top-level help aliases: `help`, `-h`, `--help`.
* Top-level version aliases: `version`, `-v`, `--version`.
* `check --delta` is an alias of `check --diff`.
* `pathway status --tech` is an alias of `pathway status --technical`.
* `pathway status --agent` is a deprecated alias of `pathway status --technical`.

## Exit codes

Global mapping:

* `0`: success / soft-ok.
* `1`: gate failure, contradicted review result, or operational error mapped to the failure class.
* `2`: usage/environment error.

Important command-specific behavior:

* `scan` returns `0` when diagnosis completes, even when findings remain.
* `drift` is informational and always returns `0`.
* `review` returns `1` when contradicted findings exist and `2` on usage errors.
* `review --verify-chain` returns `1` when the digest chain does not verify.
* `check` and `validate` return `1` when their gates fail.
* `doctor --repair` maps a missing-binary failure to `2`.

`check` is the normal repository gate. `validate` is the advanced dual-representation gate path.

## Runtime help notes

* Top-level `curbpack --help` includes the normal workflow commands, advanced commands, and exit-code semantics.
* `completion -h` returns a usage error because `completion` expects a positional shell argument.
* Some commands currently expose usage text through parser errors rather than dedicated `-h` text.
