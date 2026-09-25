# CI/CD

Run the same check in CI that you run locally:

```bash
curbpack check
```

Use its exit status to determine whether the CI job passes or fails.

## 1) CI/CD model
* Run `curbpack check` in the CI pipeline.
* If `curbpack check` passes, the pipeline continues.
* If `curbpack check` fails, the pipeline fails. The developer investigates the finding locally, makes any required changes, and pushes a new revision for CI to check.
* Remediation commands such as `heal` are not part of the automated CI flow.
* Human approval steps (for example attestation) stay outside CI.


## 2) Generic pipeline

A Curbpack CI job needs to:

```text
checkout repository
        ↓
make Curbpack available
        ↓
curbpack check
        ↓
use exit status as the CI result
```

This applies to any CI platform that can run the Curbpack CLI.

## 3) GitHub Actions

Curbpack also provides a GitHub Action.

A basic use is:

```yaml
- name: Curbpack check
  uses: RI-SE/curbpack@v0.5.2
  with:
    version: v0.5.2
```

Reference workflow: [`examples/workflows/curbpack-check.yml`](../../examples/workflows/curbpack-check.yml).

The current Action also supports optional inputs including:

* `heal`
* `prepare_release`
* `comment_on`
* `upload_sarif`
* `packs`

Current defaults from [`action.yml`](../../action.yml) are:

* `heal`: `false`
* `prepare_release`: `true`
* `comment_on`: `red`
* `upload_sarif`: `true`

The Action supports Linux and macOS runners.

## 4) CI result and outputs

`curbpack check` provides the pass/fail signal for the CI job.

The GitHub Action also exposes the check result and can produce additional report and review outputs depending on its configuration.

For the generated files and their meaning, see [`../reference/outputs.md`](../reference/outputs.md).

## 5) Other CI systems

For GitLab CI, Jenkins, Azure Pipelines, CircleCI, or other systems, use the same basic flow:

```text
checkout
→ make Curbpack available
→ curbpack check
→ use the exit status as the CI result
```
