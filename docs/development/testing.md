# Testing Curbpack during development

This page describes the normal test workflow when developing Curbpack itself.

For the formal verification suites, test procedures, traceability, and test records, see [Independent verification](../testing/README.md).

## During development

Run the fast local test target frequently:

```sh
make unittest
```

This is the normal feedback loop while changing Curbpack. E.g. if you use anything remotely like AI agents to modify things, this is a good thing to do after each iteration. 

## Before committing

Before committing a completed change, run the complete test collection untill all implemented automatic tests report passed:

```sh
DEVELOPER_MODE=TRUE make start-verification-run
make test
```
`DEVELOPER_MODE=TRUE` allows you to set up a verification run with a dirty repository (i.e. uncomitted changes). `make start-verification-run` prepares a cleanup script and pulls a reference product fort test purposes into `<gitroot>/tmp`
`make test` is intended to be the complete local pre-commit test entry point. It should test the current Curbpack working state using the versions of related test repositories selected by Curbpack. 

CI should run the same repository test entry points in a clean environment rather than defining a separate test model in workflow files.

*The test structure is currently being simplified. Some checks still live in separate scripts or verification suites. If a change affects one of those areas, run the relevant check in addition to the normal test target until it has been integrated into `make test`.*

## Start an official verification run as it will be run in the ci env
Make sure the repo is clean (everything committed and local temporary files are deleted )
A verification run is created from the current Curbpack revision and the currently selected reference-product revision. If you need to change the reference product, please note that you need to update the `tests/cyberready-test-product.pin`. The test scripts will erase whatever under `/tmp/cyberready-test-product` and clone the pinned version before each test case is run.  The command is as before (but without `DEVELOPER_MODE`)

```sh
make start-verification-run
```

This ,again, creates the run-specific verification configuration under `tmp/` and prepares the disposable reference-product checkout used by the broader verification suites.

## Review baselines

Baselines are for freezing a known multi-repository state for later review or reproduction, for example before a demo or an independent review.
A named baseline is optional. Use one when a multi-repository state must be recorded and restored later, for example for a demo, review, or release verification.

Create a named baseline with:

```sh
make baseline NAME=<name>  CONFIRM_TESTS_PASSED=TRUE
```
`NAME=<name>` is a human-readable name for the baseline, for example demo-2026-10-02. ` CONFIRM_TESTS_PASSED=TRUE` confirms that you have run the required tests on the clean repositories before creating the baseline.

These baselines are not official releases. They are simply a convenient way to preserve a known-good combination of repository revisions, for example a successful demo setup or a state used for an independent review.

The baseline command records revisions. It does not run tests itself, so run the required tests before creating the baseline.

Check a baseline with:

```sh
make baseline-check NAME=<name>
```

Restore it later with:

```sh
make checkout-baseline NAME=<name>
make start-verification-run
```

Normal development does not require a new baseline for every commit.
