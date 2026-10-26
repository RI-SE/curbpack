# CI/CD

Run the same Check in CI that you run locally:

```sh
python3 -m checks --repo "$PWD" \
  --packs /path/to/packs-root \
  --out "$PWD/.curbpack/run-result.json"
```

Use the process exit status as the job result. Exit 0 means at least one Check ran and every Claim and every Check passed. Any other outcome, including a run with no rows, is exit 1. Usage errors from the argument parser are exit 2, including a `--skip` value without `claim-id=reason`. The exit code is not a field in the JSON.

## 1. What belongs in the pipeline

* Run `python3 -m checks` on the product repository.
* If it exits 0, the pipeline continues.
* If it exits non-zero, the pipeline fails. Someone reads the rows, changes the product or the Claim, and pushes a revision to be checked again.
* Scaffold, Extract, and signing are not CI steps.
* A review decision and review-sign stay outside CI.

A failing Check is not a legal finding the pipeline is allowed to rewrite.

## 2. Generic pipeline

```text
checkout the product repository
        ↓
make the Studio tree, or a packaged build, available
        ↓
python3 -m checks --repo ... --packs ... --out ...
        ↓
exit status is the CI result
```

Any CI system that can run that process can host it. The packs root has to contain the Pack directories the product's `curbpack.json` names. The job does not fetch a newer Pack by itself.

`--skip claim-id=reason` marks that Claim skipped and stores the reason as the detail. Do not use an empty reason. Do not use skip to hide a missing file.

## 3. GitHub Actions

Call `python3 -m checks` from a step and fail the step on a non-zero status. Depending on Studio does not add SARIF upload, a pull-request comment, or a second report format. Copy-paste jobs for GitHub Actions, GitLab CI, and Jenkins are in [Check in CI](../development/ci.md).

Studio's own workflows are a different pipeline. `.github/workflows/ci.yml` runs Studio's tests on the Studio repository, then builds two files for that host: `curbpack-studio-<host>` is the application and `curbcheck-<host>` is the checker. A product job that has the source tree still runs `python3 -m checks`. A job that has the packaged checker runs `curbcheck-macos-arm64 --repo --packs --out` on macOS ARM64, or `curbcheck-windows-x64.exe --repo --packs --out` on Windows x64, with the same arguments. `.github/workflows/release.yml` publishes Studio artifacts when that workflow is authorized. Their existence does not mean a product Check ran, and it does not mean binaries were published for every operating system.

## 4. Results

Preserve the source commit of the product, the Pack id, `version`, directory digest, and the run-result file. A dirty runner workspace must not be described as a clean verification of the commit under test.

`make test` and `make ci-tests` belong to the Studio repository. They are how Studio itself is tested. They are not a Check of your product. A negative test that is specified to fail is a passing test when it fails as specified. The runner's exit status is the result that matters.

Release jobs for Studio are supposed to reuse the bytes that were tested. That rule is about Studio's own packages. It does not rebuild your product's evidence.

## 5. Other CI systems

GitLab, Jenkins, Azure Pipelines, CircleCI and others use the same flow: checkout, run `python3 -m checks`, use the exit status. GitHub Actions, GitLab CI, and Jenkins examples are in [Check in CI](../development/ci.md).

Docker images, SBOM generation, artifact signing and vulnerability scanning of the Studio build are future scope described in `docs/agile/future_cicd.md`. They are not current product features, and they are not substitutes for a product Check.
