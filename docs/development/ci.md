# Check in CI

A product pipeline runs the same Check as the shell command in the [developer guide](../user-guides/developers.md).

The job checks out three sibling directories. Studio and the packs root stay outside the product tree, so `git status` in the product still describes the commit under test.

1. `product/` is the product repository, which contains `curbpack.json`.
2. `studio/` is a Studio source tree, pinned to one commit. `curbcheck` is started from that directory, so `scripts/bin` is on `PATH`.
3. `packs/` is the packs root, pinned to one commit. That directory contains `<pack-id>/pack.json` for every id named in the product's `curbpack.json`. The job does not fetch a newer Pack by itself.

From the Studio tree, after `python3 -m pip install -r requirements.txt`:

```sh
curbcheck --repo /path/to/product --packs /path/to/packs
```

Exit 0 means at least one Check ran and every Claim and every Check passed, and the job continues. Any other outcome, including a run with no rows, is exit 1 and the job fails. A usage error from the argument parser is exit 2, including a `--skip` value without `claim-id=reason`. The exit code is not a field in the JSON. `--skip claim-id=reason` marks that Claim skipped and stores the reason as the detail.

Keep the run-result file with the product commit, the Pack id, `version`, and the directory digest. A dirty runner workspace is a check of that workspace.

Scaffold, Extract, and signing stay outside the job. A review decision and review-sign stay outside the job.

The examples use a Linux runner and `curbcheck`. On macOS ARM64 the packaged checker is `curbcheck-macos-arm64`. On Windows x64 it is `curbcheck-windows-x64.exe`. `--packs` and `--out` are optional on every one of them. When the packs root already sits inside the product tree, drop `--packs`.

Copy the job into the product repository. `.github/workflows/ci.yml` in the Studio repository runs `make ci-tests` and `make package` for Studio.

Studio is `RI-SE/curbpack`. Replace `STUDIO_COMMIT`, `OWNER/packs`, and `PACKS_COMMIT` before use. The job's Git credentials must be able to read those two repositories. When the packs root already sits at `<product>/<curbpack>/packs`, drop the packs checkout and omit `--packs`. The run result is then `<product>/<curbpack>/run-result.json`.

## GitHub

```yaml
name: curbcheck

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout product
        uses: actions/checkout@v4
        with:
          path: product

      - name: Checkout Studio
        uses: actions/checkout@v4
        with:
          repository: RI-SE/curbpack
          ref: STUDIO_COMMIT
          path: studio

      - name: Checkout packs
        uses: actions/checkout@v4
        with:
          repository: OWNER/packs
          ref: PACKS_COMMIT
          path: packs

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install Studio dependencies
        run: python3 -m pip install -r studio/requirements.txt

      - name: Check
        working-directory: studio
        run: |
          export PATH="$GITHUB_WORKSPACE/studio/scripts/bin:$PATH"
          curbcheck \
            --repo "$GITHUB_WORKSPACE/product" \
            --packs "$GITHUB_WORKSPACE/packs"

      - name: Keep the run result
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: run-result
          path: product/curbpack/run-result.json
          if-no-files-found: ignore
```

A non-zero status fails the Check step.

## GitLab

```yaml
variables:
  STUDIO_REPOSITORY: "https://github.com/RI-SE/curbpack.git"
  STUDIO_COMMIT: "STUDIO_COMMIT"
  PACKS_REPOSITORY: "https://github.com/OWNER/packs.git"
  PACKS_COMMIT: "PACKS_COMMIT"

check:
  image: python:3.12
  script:
    - git clone "$STUDIO_REPOSITORY" "$CI_PROJECT_DIR/../studio"
    - git -C "$CI_PROJECT_DIR/../studio" checkout "$STUDIO_COMMIT"
    - git clone "$PACKS_REPOSITORY" "$CI_PROJECT_DIR/../packs"
    - git -C "$CI_PROJECT_DIR/../packs" checkout "$PACKS_COMMIT"
    - python3 -m pip install -r "$CI_PROJECT_DIR/../studio/requirements.txt"
    - |
      cd "$CI_PROJECT_DIR/../studio"
      export PATH="$CI_PROJECT_DIR/../studio/scripts/bin:$PATH"
      curbcheck \
        --repo "$CI_PROJECT_DIR" \
        --packs "$CI_PROJECT_DIR/../packs"
  artifacts:
    when: always
    paths:
      - curbpack/run-result.json
```

Put this in the product repository's `.gitlab-ci.yml`. A non-zero status fails the job.

## Jenkins

The agent needs Git and Python 3.12. `checkout scm` inside `product/` is the product repository.

```groovy
pipeline {
    agent any
    environment {
        STUDIO_REPOSITORY = 'https://github.com/RI-SE/curbpack.git'
        STUDIO_COMMIT = 'STUDIO_COMMIT'
        PACKS_REPOSITORY = 'https://github.com/OWNER/packs.git'
        PACKS_COMMIT = 'PACKS_COMMIT'
    }
    stages {
        stage('Check') {
            steps {
                dir('product') {
                    checkout scm
                }
                sh '''
                    git clone "$STUDIO_REPOSITORY" studio
                    git -C studio checkout "$STUDIO_COMMIT"
                    git clone "$PACKS_REPOSITORY" packs
                    git -C packs checkout "$PACKS_COMMIT"
                    python3 -m pip install -r studio/requirements.txt
                    cd studio
                    export PATH="$WORKSPACE/studio/scripts/bin:$PATH"
                    curbcheck \
                      --repo "$WORKSPACE/product" \
                      --packs "$WORKSPACE/packs"
                '''
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'product/.curbpack/run-result.json', allowEmptyArchive: true
        }
    }
}
```

A non-zero status fails the Check stage. The `post` block still archives the run result when the file was written.
