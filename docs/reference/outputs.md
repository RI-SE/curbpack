# Outputs reference

## Scope

* Output artifacts, schemas, and documented production points only.
* Compact reference format; no workflow tutorial content.

## How the outputs relate

`curbpack check` evaluates the current repository state against the selected packs and reports whether the checks pass or fail. Other commands create reports and review material from that result.

```text
selected packs
        +
product repository
        ↓
curbpack check
        ↓
pass / fail + findings explaining why
        ↓
optional outputs for review/tools:
    ContextPack
    buyer-questions
    SARIF
        ↓
curbpack prepare-release
        ↓
review-pack/
        ↓
recipient / reviewer
        ↓
curbpack review <review-pack>
```

`curbpack share` is a convenience workflow around this model:

```text
check
  → context-pack
  → buyer-questions
  → prepare-release
```

It does not perform a different evaluation from `curbpack check`.

A **pack** defines rules evaluated by `curbpack check`.

A **review pack** is different. It is the material Curbpack prepares so that another person can review the result and its supporting evidence.

Curbpack prepares review material. The reviewer decides what the result means.

## Primary artifacts

| Artifact                | Format / path                                                                    | Producer                                                    | Purpose                                                                      |
| ----------------------- | -------------------------------------------------------------------------------- | ----------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Check result / findings | `.github/curbpack/cache/latest_failure.json` and related cache data              | `curbpack check`                                            | Result and findings for the checked repository state                         |
| ContextPack             | `.github/curbpack/cache/context-pack.json` + `.md`                               | `export --context-pack` or `share`                          | Optional export for tools that explain or process findings                   |
| Buyer questions         | `.github/curbpack/cache/buyer-questions.json` + `.md`                            | `export --buyer-questions` or `share`                       | Human Q&A checklist for review and discussion                                |
| Supplier checklist      | `review-pack/supplier-checklist.json` + `.md`                                    | `ask-my-suppliers`                                          | Questions intended to be sent to suppliers                                   |
| Review pack             | `review-pack/`                                                                   | `prepare-release` or `share`                                | Package containing the result and supporting review material                 |
| Buyer one-pager         | `review-pack/buyer-onepager.html`                                                | `prepare-release` or `share`                                | Human-readable summary for the recipient                                     |
| Evidence bundle         | `review-pack/evidence-bundle.html`                                               | `share --bundle` or release preparation with bundle enabled | Offline page containing review evidence                                      |
| Proof page              | `proof/index.html` and `review-pack/proof-index.html` during release preparation | release/attest support flow                                 | Local verification page                                                      |
| SARIF                   | `.github/curbpack/cache/curbpack.sarif`                                          | `prepare-release` and `export --sarif`                      | Machine-readable findings for tools such as CI and code scanning             |
| Drift report            | JSON, schema `curbpack-drift-report:1`                                           | `curbpack drift --json`                                     | Informational evidence-drift report                                          |
| Review report           | JSON, schema `curbpack-review-report:2`                                          | `curbpack review --json`                                    | Result of reviewing a received review pack                                   |
| Explain packet          | `.github/curbpack/cache/explain-packet.json`                                     | `export --explain-packet`                                   | Optional export for tools that explain or process findings; does not affect `check` |


## Review pack

`curbpack prepare-release` creates the `review-pack/` directory.

The review pack is intended to be given to another person for review. It contains the Curbpack result together with material that helps the reviewer understand the result and inspect its supporting evidence.

The current implementation writes several files, including:

| File                          | Purpose                                           |
| ----------------------------- | ------------------------------------------------- |
| `01-gate-failures.json`       | Machine-readable check findings                   |
| `02-action-report.md`         | Detailed report of findings and suggested actions |
| `03-executive-summary.md`     | Short human-readable summary                      |
| `04-sbom-summary.json`        | SBOM summary                                      |
| `04-sbom.cdx.json`            | CycloneDX SBOM when available                     |
| `05-vex-draft.json`           | Draft OpenVEX data derived from relevant findings |
| `06-gate-failures.sarif`      | SARIF representation of findings                  |
| `07-watchlist-sbom-join.json` | Informational watchlist/SBOM join                 |
| `buyer-onepager.html`         | Human-readable summary for the recipient          |
| `proof-index.html`            | Local verification page                           |
| `evaluation.json`             | Evaluation data when available                    |
| `run-receipt.json`            | Receipt associated with the evaluation            |

A review pack can also be created for a repository that does not pass all checks. Creating the review pack does not change the result.

## ContextPack

The ContextPack contains a structured snapshot of the current Curbpack result. It is an optional export for tools that explain or process findings.

Default outputs:

```text
.github/curbpack/cache/context-pack.json
.github/curbpack/cache/context-pack.md
```

It is supporting context, not a separate evaluation and not a certification or conformity statement.

It can be created directly with:

```bash
curbpack export --context-pack
```

and is also generated by:

```bash
curbpack share
```

## Buyer questions

`buyer-questions` is a separate review aid. It is not a check result and it is not the review pack itself.

Default outputs:

```text
.github/curbpack/cache/buyer-questions.json
.github/curbpack/cache/buyer-questions.md
```

It provides a human Q&A checklist intended to support discussion with a buyer or reviewer.

It can be created directly with:

```bash
curbpack export --buyer-questions
```

and is also generated by:

```bash
curbpack share
```

## Supplier checklist

`curbpack ask-my-suppliers` creates a related supplier-facing checklist.

Default outputs:

```text
review-pack/supplier-checklist.json
review-pack/supplier-checklist.md
```

The command also prints checklist and supplier communication text to stdout.

With `--stdout-only`, it does not write the review-pack files.

## `share` and `prepare-release`

`prepare-release` builds the review pack:

```text
curbpack prepare-release
        ↓
review-pack/
```

`share` is a convenience command that runs the current review-material workflow:

```text
curbpack share
   ↓
check
   ↓
context-pack
   ↓
buyer-questions
   ↓
prepare-release
   ↓
review-pack/
```

`share --skip-prepare-release` skips creation of the review pack while still creating the other share outputs.

`share` does not perform a different check from `curbpack check`.

## Reviewing a received review pack

A recipient can inspect a received review pack with:

```bash
curbpack review <review-pack>
```

This reviews the material contained in the received review pack.

It is different from:

```bash
curbpack check
```

`check` evaluates the product repository against selected packs.

`review` examines material that someone else has already prepared and sent for review.

JSON output from `review` uses:

```text
curbpack-review-report:2
```

## Explain packet

The explain packet is an optional machine-readable export for tools that explain or process findings.

It is created with:

```bash
curbpack export --explain-packet
```

Default output:

```text
.github/curbpack/cache/explain-packet.json
```

It contains sanitized information derived from the Curbpack result so that another tool can help explain the findings.

It does not change the result of `curbpack check`.

## Stable output contracts

| Contract area                 | Value                                                                                          |
| ----------------------------- | ---------------------------------------------------------------------------------------------- |
| Install marker schema         | `curbpack-install-marker:1`                                                                    |
| Install marker path (Unix)    | `~/.local/share/curbpack/install-marker.json` or `$XDG_DATA_HOME/curbpack/install-marker.json` |
| Install marker path (Windows) | `%LOCALAPPDATA%\Programs\Curbpack\install-marker.json`                                         |
| Evidence bundle marker        | `<!-- curbpack-bundle-schema:1 -->` in `review-pack/evidence-bundle.html`                      |
| Drift schema                  | `curbpack-drift-report:1`                                                                      |
| Review schema                 | `curbpack-review-report:2`                                                                     |
| GateFailure schema version    | `"1"`                                                                                          |
| GateFailure timestamp field   | `timestamp`                                                                                    |

## Consumer-facing interpretation

| Output                     | Intended use                                                                 |
| -------------------------- | ---------------------------------------------------------------------------- |
| Check result / GateFailure | Machine-readable findings from `curbpack check`; used by CLI, CI, and other tools |
| ContextPack                | Optional export for tools that explain or process findings                        |
| Buyer questions            | Human discussion with buyers or reviewers                                         |
| Supplier checklist         | Questions and communication for suppliers                                         |
| Review pack                | Material sent to a reviewer                                                       |
| Buyer one-pager            | Human-readable summary of the review material                                     |
| Explain packet             | Optional export for tools that explain or process findings                        |
| Review report              | Result of reviewing a received review pack                                        |
| Drift report               | Informational report about evidence drift                                         |

## Exit and output behavior

| Command                          | Behavior                                                                                     |
| -------------------------------- | -------------------------------------------------------------------------------------------- |
| `curbpack check`                 | Exit `0` when checks pass; exit `1` when findings remain or the command fails                |
| `curbpack scan`                  | Read-only diagnosis; findings do not make it a pass/fail check                               |
| `curbpack share`                 | Creates review material and returns non-zero when the underlying check fails             |
| `curbpack prepare-release`       | Creates `review-pack/`; failing checks require `--allow-failing-gates` when invoked directly |
| `curbpack review --json`         | Produces `curbpack-review-report:2`                                                          |
| `curbpack drift`                 | Informational; exit code remains `0`                                                         |
| `curbpack review --verify-chain` | Exit `0` for a valid chain, `1` for mismatch/break, `2` for usage error                      |

## Important distinction

The current terminology uses the word **pack** for two different things:

```text
pack
    ↓
defines rules used by curbpack check

review pack
    ↓
generated material sent to a reviewer
```

They are separate concepts.
