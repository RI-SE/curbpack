# Architecture

This page describes how Curbpack is currently implemented.

Curbpack is a local CLI that checks repository content against versioned packs and produces results and files for human review.

## Main flow

The main evaluation flow is:

```text
curbpack CLI
    |
    v
configuration + pack selection
    |
    v
pack composition
    |
    v
rule evaluation
    |
    v
Evaluation
    |
    +---- RunReceipt
    |
    +---- terminal output
    +---- cache files
    +---- export, sharing, and review
```

`cmd/curbpack/main.go` is small. Most command handling lives in `internal/cli/`.

## CLI

```text
cmd/curbpack/
internal/cli/
```

The CLI:

* parses command options;
* resolves command inputs;
* calls the relevant implementation;
* prints results;
* maps results and errors to process exit codes.

Commands are registered in `internal/cli/registry.go`.

Rule evaluation itself lives outside the CLI.

## Configuration and packs

```text
internal/config/
internal/packs/
internal/packscmd/
```

`internal/config/` reads `.curbpack.json` and resolves configured packs.

Pack selection depends on the command. For example, `check` and `scan` use different defaults when no pack is configured.

`internal/packs/` contains pack definitions, loading, composition, inheritance, and rules.

The currently embedded packs include:

```text
house-policy
cra-baseline
medtech-iec62304
```

Packs define what Curbpack checks. The evaluator performs the checks.

## Evaluation

```text
internal/validate/
```

`validate.Run` is the main evaluation function.

It:

1. resolves the selected packs;
2. composes them;
3. records the repository state being evaluated;
4. evaluates each rule;
5. checks that the evaluated inputs did not change during the run;
6. creates an `Evaluation`;
7. computes its digest;
8. creates a `RunReceipt`;
9. writes cache files unless running read-only.

The evaluator currently supports these check kinds:

```text
annex_file
file_present
anti_placeholder
npm_dep_ban
manifest_dep_ban
text_forbid
fresh
owned
```

`scan` uses the same evaluator in read-only mode.

## Evaluation data

```text
internal/ir/
```

The result data is split between the evaluation result and information about the individual run.

### `ir.Evaluation`

`Evaluation` contains the result of evaluating a particular repository state.

It includes information such as:

* evaluated repository state;
* selected pack;
* failures;
* result;
* numbers of failed, skipped, and evaluated rules;
* comparison information;
* evaluation time reference (`as_of`);
* conformity-related result data.

Execution-specific information such as wall-clock duration and agent identity is not included in the hashed evaluation data.

This allows the same evaluation data to produce the same digest.

### `ir.RunReceipt`

`RunReceipt` records information about a particular execution, including:

* evaluation digest;
* timestamp;
* agent identity;
* platform;
* tool version;
* evaluation duration.

The receipt refers to its evaluation through `evaluation_digest`.

### Older result format

`ir.GateFailurePayload` remains for code that still expects the older combined result format.

Curbpack can convert between the `Evaluation`/`RunReceipt` pair and this older representation.

New code should normally use `Evaluation` and `RunReceipt`.

## Cache

Evaluation files are stored below:

```text
.github/curbpack/cache/
```

Evaluation and receipt objects are stored by digest:

```text
evaluations/<evaluation-digest>.json
receipts/<receipt-digest>.json
```

Curbpack also writes current-result files:

```text
latest_evaluation.json
latest_receipt.json
latest_failure.json
latest_result.json
latest_action_report.md
latest.json
```

`latest.json` points to the current evaluation and receipt digests.

The digest-named evaluation and receipt files are written before `latest.json` is updated.

`latest_failure.json` and `latest_result.json` currently use the older `GateFailurePayload` format.

## File writes

```text
internal/outwrite/
internal/pathjail/
```

`internal/outwrite/` coordinates writes and repository locking.

`internal/pathjail/` checks paths before repository-relative files are written.

These packages are used to prevent writes outside the intended repository area, including writes through path traversal or symlinks.

## Automatic fixes

```text
internal/formhints/
internal/remediation/
```

`check --heal` first evaluates the repository.

If findings remain, Curbpack can create missing starter files and then run the checks again.

It does not automatically attest, approve, or create approved legal content.

After writing files, Curbpack performs a full check of the changed repository state.

## Export and release files

```text
internal/exportx/
internal/release/
```

`internal/exportx/` creates reports and other exported representations of Curbpack results.

`internal/release/` assembles files intended for review or sharing.

These packages use evaluation results produced by the evaluator.

## Review

```text
internal/review/
```

Review works with previously produced or received material.

It includes functionality for:

* repository review;
* digest verification;
* historical comparison;
* pack auditing;
* parent/child relationships;
* comparison bundles.

Review is separate from the normal repository evaluation performed by `validate.Run`.

## Attestation

```text
internal/attest/
```

Attestation and signature verification are separate from rule evaluation.

A signature shows that particular data was signed with a particular key.

It does not by itself show that:

* the repository complies with a regulation;
* the underlying claims are correct;
* a human approved the result.

Human approval is handled separately from evaluation.

## Other packages

Other packages provide additional functions outside the main evaluation flow:

```text
internal/pathway/     guided workflow and confirmation state
internal/research/    research and source lookup
internal/ask/         question and assistance functions
internal/sbom/        SBOM generation
internal/vex/         VEX generation
internal/drift/       change analysis
internal/instrument/  repository inspection and state mapping
internal/doctor/      installation and environment checks
internal/githook/     Git hook integration
internal/platform/    platform-specific integration
```

## Package responsibilities

The main package responsibilities are:

```text
config       reads configuration
packs        defines and loads rules
validate     runs the rules
ir           defines evaluation data
cli          handles commands and output

outwrite     coordinates writes
pathjail     checks file paths

exportx      creates exported output
release      assembles files for review or sharing

review       reviews and compares existing material
attest       signs and verifies data
```

In short:

> Packs define what to check.
> Validate runs the checks.
> IR stores the result.
> Other packages display, store, export, review, or sign it.

## Human approval

Curbpack produces information for human review.

A successful evaluation does not itself authorize:

* merge;
* release;
* confirmation;
* attestation;
* regulatory approval.

Those are separate decisions.

For public command behavior and data formats, see:

* `reference/cli.md`
* `reference/configuration.md`
* `reference/outputs.md`
