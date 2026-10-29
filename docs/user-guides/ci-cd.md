# CI/CD

A product pipeline downloads a pinned release of `curbcheck`, runs it against the product checkout, and uses its process exit status as the gate. It does not install Studio, clone the Studio source, or build the checker.

```sh
curbcheck --repo "$PWD" --out ci-artifacts/run-result.json
```

The product must already contain `curbpack.json`, the Packs under its configured `packs_dir`, and the Claims under its configured `claims_dir`. The checker does not fetch Packs. `--packs` and `--requirements` select comma-separated ids; they do not set directories. JSON is written only with `-j` or `--out`. See [curbcheck](../reference/curbcheck-cli.md) for the CLI and [Outputs](../reference/outputs.md#run-result) for the JSON contract.

## Before using the examples

The examples below use Linux x64, Ubuntu 22.04 or newer with glibc, Git, curl, CA certificates, and GNU `sha256sum`. No Python installation is needed to run the packaged checker. Alpine/musl and Linux ARM64 are not targets of these examples.

Replace `REPLACE_WITH_RELEASE_TAG` with a specific tag from [Curbpack releases](https://github.com/RI-SE/curbpack/releases) containing **both** `curbcheck-linux-x64` and `SHA256SUMS`. Use the same tag for the binary and its checksum file. The release `2026-10-28a-test-release` contains macOS and Windows binaries, not Linux. Linux build support has been added to the build workflow; the examples require a release that actually publishes that binary. A missing asset makes the download step fail.

Commit the pipeline configuration. For the GitLab and Jenkins examples, add this entry to the product's `.gitignore`:

```gitignore
/ci-artifacts/
```

All examples download the executable into a temporary directory outside the product checkout. The GitHub Action also writes its result there. GitLab and Jenkins write their result to `ci-artifacts/`; ignoring that directory keeps repeated runs from making the product worktree dirty. Start from a clean checkout; Git history must include the commits your configured Git Checks need. The GitHub and GitLab examples request full history. Configure the Jenkins SCM checkout without shallow cloning.

Each example verifies the downloaded binary against that release's checksum file before executing it. Artifact retention is configured to run even when a Check fails. A startup, download, or argument error can stop the job before any result JSON exists; the job log then contains the failure.

## GitHub Actions

The root [`action.yml`](../../action.yml) in this repository downloads and verifies `curbcheck`, runs it against the product checkout, and saves its JSON result as the `curbcheck-result` artifact even when a Check fails. Its only optional input is `release`; there are no heal, signing, release-preparation, SARIF, or PR-comment steps.

Save this as `.github/workflows/curbcheck.yml` in the **product** repository:

```yaml
name: curbcheck

on:
  push:
  pull_request:

permissions:
  contents: read

jobs:
  check:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: RI-SE/curbpack@REPLACE_WITH_RELEASE_TAG
```

Choose a release tag containing the new root `action.yml` as well as the Linux binary and `SHA256SUMS`. The Action downloads the binary from that same tag by default; the product does not need to repeat the download or artifact-upload steps. A non-zero checker exit fails the Action and the job. The product checkout is not changed.

When pinning the Action to a commit SHA instead of a release tag, specify the release to download explicitly:

```yaml
      - uses: RI-SE/curbpack@REPLACE_WITH_COMMIT_SHA
        with:
          release: REPLACE_WITH_RELEASE_TAG
```

The same `release` input is required when invoking the Action locally with `uses: ./`. This Action currently targets Linux x64 runners. Its result upload uses GitHub's [upload-artifact action](https://github.com/actions/upload-artifact).

## GitLab CI

Save as `.gitlab-ci.yml`, or add this job to the product's existing configuration. The `linux-x64` tag must match a Linux x64 runner in your GitLab installation using the Docker executor; change the tag to your runner's tag. `ubuntu:22.04` is the job environment, not a Curbpack Docker image.

```yaml
curbcheck:
  stage: test
  image: ubuntu:22.04
  tags:
    - linux-x64
  variables:
    GIT_DEPTH: "0"
    CURBCHECK_RELEASE: REPLACE_WITH_RELEASE_TAG
  before_script:
    - apt-get update
    - apt-get install -y --no-install-recommends ca-certificates curl git
  script:
    - |
      set -eu
      tool_dir="$(mktemp -d)"
      base="https://github.com/RI-SE/curbpack/releases/download/$CURBCHECK_RELEASE"
      curl -fsSL "$base/curbcheck-linux-x64" -o "$tool_dir/curbcheck-linux-x64"
      curl -fsSL "$base/SHA256SUMS" -o "$tool_dir/SHA256SUMS"
      (
        cd "$tool_dir"
        awk '$2 == "curbcheck-linux-x64" { print }' SHA256SUMS > curbcheck.sha256
        test -s curbcheck.sha256
        sha256sum -c curbcheck.sha256
      )
      chmod +x "$tool_dir/curbcheck-linux-x64"
      "$tool_dir/curbcheck-linux-x64" --repo "$CI_PROJECT_DIR" --out "$CI_PROJECT_DIR/ci-artifacts/run-result.json"
  artifacts:
    when: always
    paths:
      - ci-artifacts/run-result.json
```

The checker is the final command in the script, so its non-zero exit fails the job. GitLab's [`artifacts:when: always`](https://docs.gitlab.com/ci/jobs/job_artifacts/#with-upload-conditions) retains the result on success or failure. If your pipeline defines custom stages, add `test` or put this job in an existing stage.

## Jenkins

Save as `Jenkinsfile` in the product repository and use a Pipeline from SCM or a Multibranch Pipeline. Assign the `linux-x64` label to an Ubuntu 22.04-or-newer x64 agent with Git, curl, CA certificates, and GNU `sha256sum` installed. Change the label to match your installation.

```groovy
pipeline {
    agent { label 'linux-x64' }
    options { skipDefaultCheckout(true) }
    environment {
        CURBCHECK_RELEASE = 'REPLACE_WITH_RELEASE_TAG'
    }
    stages {
        stage('Checkout') {
            steps {
                deleteDir()
                checkout scm
            }
        }
        stage('Check product') {
            steps {
                sh '''
                    set -eu
                    tool_dir="$(mktemp -d)"
                    base="https://github.com/RI-SE/curbpack/releases/download/$CURBCHECK_RELEASE"
                    curl -fsSL "$base/curbcheck-linux-x64" -o "$tool_dir/curbcheck-linux-x64"
                    curl -fsSL "$base/SHA256SUMS" -o "$tool_dir/SHA256SUMS"
                    (
                        cd "$tool_dir"
                        awk '$2 == "curbcheck-linux-x64" { print }' SHA256SUMS > curbcheck.sha256
                        test -s curbcheck.sha256
                        sha256sum -c curbcheck.sha256
                    )
                    chmod +x "$tool_dir/curbcheck-linux-x64"
                    "$tool_dir/curbcheck-linux-x64" --repo "$WORKSPACE" --out "$WORKSPACE/ci-artifacts/run-result.json"
                '''
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'ci-artifacts/run-result.json', allowEmptyArchive: true
        }
    }
}
```

The Checkout stage clears the allocated job workspace before checking out the product, preventing an old result from being archived after a later download failure. A non-zero checker exit fails the `sh` step and the build. Jenkins's [`post { always { ... } }`](https://www.jenkins.io/doc/book/pipeline/syntax/#post) runs [`archiveArtifacts`](https://www.jenkins.io/doc/pipeline/steps/core/#archiveartifacts-archive-the-artifacts) even after that failure.

## Reading the outcome

| Process exit | Meaning |
| --- | --- |
| `0` | At least one Check ran, and every evaluated Claim and every Check passed. |
| `1` | A Check failed or was skipped, no Check ran, or execution stopped with an error. |
| `2` | Invalid command-line arguments. |

Use the repository command's exit status as the job result. Do not use `continue-on-error`, `allow_failure`, or `|| true` to turn a failed Check into a passing gate. `--skip claim-id=reason` records a skipped Claim and still exits non-zero.

Retain the run result and the release tag used by the job. The result records the product commit and worktree state when available, loaded Pack ids, versions and directory digests, and the evaluated Claim digests. A dirty worktree can still exit 0; that is not verification of the commit's exact content. Exit 0 describes the executed Checks, not coverage of every Requirement or a legal compliance decision.

Extract, Scaffold, signing, review decisions and review-sign stay outside this gate. A failure is investigated by a person; the pipeline does not rewrite the Claim or its evidence.

## Building Curbpack itself

The examples above belong to product repositories. Curbpack's own `.github/workflows/ci.yml` tests this repository and builds Studio and `curbcheck` in separate jobs. `make package-curbcheck` builds only the checker; `make package-studio` builds only Studio. `.github/workflows/release.yml` publishes the tested artifacts when authorized. `make test` and `make ci-tests` test Curbpack itself; they do not check a product.

Curbpack Docker images, SBOM generation, artifact signing and vulnerability scanning of the Studio build remain future scope in [Future CI/CD](../agile/future_cicd.md).
