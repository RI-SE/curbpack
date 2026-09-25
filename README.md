# Curbpack

> **Source:** [RI-SE/curbpack](https://github.com/RI-SE/curbpack) contains the code, releases, and documentation. Development is supported by RISE as an applied research / competence object; see [NOTICE](NOTICE). RISE does not certify products that use Curbpack gate results. The GitHub Action remains pinned to `RI-SE/curbpack@v0.5.2` until the next human tabletop permits a version bump.

Curbpack checks your repository against local rule packs and writes a review pack you can hand to a buyer or auditor — on your machine, without claiming certification.

> Not conformity assessment. Not CE marking. Not a notified-body opinion.

[Documentation](docs/README.md) · [White paper](papers/curbpack-whitepaper.md) · [Site](https://ri-se.github.io/curbpack/) · [Voice and terms](policies/voice-and-terms.md) · [Repository](https://github.com/RI-SE/curbpack)

## Friendly Pre-Beta: Start Testing Here

**Testing the latest hardening work? Use the [pre-beta guide](vision/docs/getting-started/prebeta.md).**

From this checkout:

```bash
./scripts/test-prebeta.sh
```

It builds a labelled source version, prepares a sandbox, and records the exact build and results.

Use this path when testing the current source tree. The released installer below supplies an older released build.

## Release Status

The installer currently supplies **v0.5.5**. The GitHub Action remains pinned to `RI-SE/curbpack@v0.5.2`.

See [launch status and audit limitations](vision/docs/launch-status.md) for the current qualification status and known limitations.

## Released v0.5.5: Start With a Read-Only Scan

Install Curbpack, change to any Git repository, and run `scan`.

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/RI-SE/curbpack/main/scripts/install.sh | sh
cd /path/to/your/git/repo
curbpack scan
```



### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/RI-SE/curbpack/main/scripts/install.ps1 | iex
cd C:\path\to\your\git\repo
curbpack scan
```

`scan` is read-only. It does not initialize Curbpack or install hooks in the repository.

Exit `0` from `scan` means the scan completed; findings may still remain. Use `curbpack check` when you need repository gate pass/fail.

Installation problems: [Troubleshooting](docs/user-guides/troubleshooting.md).

## Choose the Relevant Guide


| You are                      | Start here                                                                                                          |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **New user**                 | [Install](docs/user-guides/install.md) · [Getting Started](docs/user-guides/getting-started.md)                     |
| **Developer / product team** | [Developer Guide](docs/user-guides/developers.md) · [CI/CD](docs/user-guides/ci-cd.md)                              |
| **Buyer / reviewer**         | [Reviewer Guide](docs/user-guides/reviewers.md) · [For Reviewers](https://ri-se.github.io/curbpack/for-reviewers/)  |
| **Authority / auditor**      | [For Authorities](https://ri-se.github.io/curbpack/for-authorities/) · [Background](vision/docs/for-authorities.md) |
| **Pack developer**           | [Pack Development](docs/user-guides/pack-developers.md)                                                             |
| **Curbpack contributor**     | [Development](docs/development/README.md) · [Testing](docs/testing/README.md)                                       |


For an overview of the product model, see [Concepts](docs/concepts/README.md).

For exact command, configuration, pack, and output details, see the [Technical Reference](docs/reference/README.md).

For the longer technical background, read the [white paper](papers/curbpack-whitepaper.md).

## Continue to the Full Workflow

After installation, the normal flow is:

```bash
curbpack doctor
curbpack demo

cd /path/to/your/product

curbpack scan
curbpack init
curbpack check
```

`scan` lets you inspect the repository before initialization.

`init` creates the Curbpack configuration for the product repository.

`check` evaluates the selected packs against the repository and produces the gate result.

If findings remain, inspect them, change the repository or configuration as appropriate, and run `curbpack check` again.

When the result is ready to hand to another person:

```bash
curbpack share
```

Human attestation is separate:

```bash
curbpack attest
```

For the step-by-step product workflow, see the [Developer Guide](docs/user-guides/developers.md).

An older, more detailed description of the optional pathway flow remains available at [vision/docs/getting-started/pathway.md](vision/docs/getting-started/pathway.md) while that material is being reviewed for migration.

## What You Get


| Artifact            | When                         | What it is                                                     |
| ------------------- | ---------------------------- | -------------------------------------------------------------- |
| **Gate report**     | `curbpack check`             | Findings and result from the selected rules                    |
| **Review pack**     | `prepare-release` or `share` | Material prepared for human review                             |
| **Buyer one-pager** | `share`                      | Supplier evidence summary                                      |
| **Evidence bundle** | `share --bundle`             | Offline review material                                        |
| **ContextPack**     | export/share flow            | Structured context for other tools                             |
| **Buyer questions** | export/share flow            | Questions for supplier/reviewer handoff                        |
| **Attest capsule**  | Human `attest`               | Record bound to the reviewed repository state                  |
| **Proof page**      | After attest                 | Local page for inspecting the attestation and evidence pointer |


For exact generated files and locations, see [Outputs](docs/reference/outputs.md).

These artifacts are review material. They are not certification or conformity decisions.

## How to Interpret Results


| Signal                | Meaning                                                      |
| --------------------- | ------------------------------------------------------------ |
| Exit **0** on `check` | Selected gates passed on this repository state               |
| Exit **1** on `check` | Findings remain or the check could not complete successfully |
| Exit **2**            | Usage or environment error                                   |
| Exit **0** on `scan`  | Scan completed; findings may still remain                    |
| **Unsigned** attest   | Attestation exists but is not cryptographically signed       |
| **ssh-agent-signed**  | An SSH signature was produced                                |


Only `check` provides repository gate pass/fail.

Gate pass is **not** certification, CE marking, or notified-body approval. Humans decide what claims to make from the evidence.

## GitHub Action

The public Action remains pinned to:

```yaml
- uses: RI-SE/curbpack@v0.5.2
  with:
    heal: "true"
    comment_on: red
    upload_sarif: "true"
```

Drop-in example:

`[examples/workflows/curbpack-check.yml](examples/workflows/curbpack-check.yml)`

For the normal CI model, see the [CI/CD Guide](docs/user-guides/ci-cd.md).

## Main Commands


| Command    | Purpose                                              |
| ---------- | ---------------------------------------------------- |
| `doctor`   | Inspect the local Curbpack environment               |
| `demo`     | Run the bundled demonstration                        |
| `scan`     | Inspect a repository without initializing Curbpack   |
| `init`     | Initialize Curbpack in a product repository          |
| `check`    | Evaluate the selected packs and produce gate results |
| `share`    | Prepare review material for handoff                  |
| `review`   | Review a received pack or repository evidence        |
| `attest`   | Human attestation of the reviewed state              |
| `export`   | Produce additional outputs                           |
| `packs`    | Inspect and manage packs                             |
| `pathway`  | Optional pathway workflow                            |
| `research` | Optional research and citation support               |


For the complete CLI reference, see [CLI Reference](docs/reference/cli.md) or run:

```bash
curbpack --help
curbpack <command> --help
```



## Documentation



### Current Documentation

- [Documentation Index](docs/README.md)
- [User Guides](docs/user-guides/README.md)
- [Concepts](docs/concepts/README.md)
- [Technical Reference](docs/reference/README.md)
- [Development](docs/development/README.md)
- [Testing](docs/testing/README.md)
- [White Paper](papers/curbpack-whitepaper.md)



### Policies and Agent Guidance

- [Claim Discipline](policies/claim-discipline.md)
- [Voice and Terms](policies/voice-and-terms.md)
- [Strategy Boundary](policies/strategy-boundary.md)
- [Agent Guidance](AGENTS.md)
- [Assistant Loop](agents/assistant-loop.md)



### Detailed Material Still Under `vision/docs`

Some useful material from the previous documentation structure has not yet been migrated. It remains available while the current documentation is filled out.

- [Pre-Beta Testing](vision/docs/getting-started/prebeta.md)
- [Launch Status](vision/docs/launch-status.md)
- [Pathway](vision/docs/getting-started/pathway.md)
- [Security Model](vision/docs/security-model.md)
- [Intent vs Scope](vision/docs/intent-vs-scope.md)
- [Write Your Own Pack](vision/docs/write-your-own-pack.md)
- [Shared Frame](vision/docs/shared-frame.md)
- [Review Method 1.3.0](vision/docs/method/review-method-1.3.0.md)

Curbpack prepares structural evidence for human review. It does not replace legal interpretation, software composition analysis, secret scanning, or other specialist assurance activities.