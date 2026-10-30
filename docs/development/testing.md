# Testing Curbpack during development

This page describes testing while developing Studio and curbcheck. Formal curbcheck procedures, traceability, and test records are in [Testing curbcheck](../testing/README.md). Test coverage and acceptance evidence follow the [Testing policy](../../policies/testing.md).

## During development

From the repository root, run the Studio functional suite:

```sh
make test
```

This discovers the Python tests under `tests/` through `scripts/ci/checks/tests.py`. It does not clone the reference product or run the separate `tests/check/` verification tree. For a focused change, run the relevant Python unittest module before the affected regression suite.

## Before completing a change

Run the checks required by the affected story and subsystem. Studio's required CI checks run locally with:

```sh
make ci-tests
```

The currently registered check is `tests`, which runs the same Studio suite as `make test`. `ONLY=tests make ci-tests` selects it explicitly. Record the commands and actual results, including failures, skips, and manual steps not executed. Approved story work also requires the review and verification steps in [the story workflow](../../.cursor/skills/story-workflow/SKILL.md).

For changes affecting curbcheck, also run its verification below. The Studio suite and curbcheck verification are separate; passing one does not establish that the other passed.

## Verify curbcheck during development

For a working tree with local changes:

```sh
DEVELOPER_MODE=TRUE make test-curbcheck
```

This starts a verification run, prepares R1 in the pinned reference product, runs the seven carried Checks, and reports the catalogue. It deletes and recreates this checkout's `tmp/`, clones the public HTTPS URL in `tests/cyberready-test-product.pin`, and writes `tmp/verification-run.sh`. Developer mode uses the current Studio working tree and records HEAD; it does not make those local changes part of the recorded commit.

The runner reads Packs and Claims from the clone's `external_test/curbpack/` fixture and copies them into the product's configured directories. Manual and outside catalogue rows are not passing automated evidence.

## Verify the installers

The [SYS-05](../agile/epics/01-pack-editor/stories/SYS-05-simple-installation.md) installer tests use temporary directories and fixture downloads:

```sh
python3 -m unittest tests.test_installers tests.test_release_publish
python3 scripts/build/package_installers.py
```

This verifies Studio-with-checker and checker-only selection, stable names, checksum failures, preservation of existing programs, version selection, repeat installation, Linux libc rejection, and the packaged installer/checksum artifacts. It does not establish native Windows behavior or publication of a release.

On a Windows CI agent, run the PowerShell scenarios too:

```powershell
powershell -NoProfile -File tests/installers-windows.ps1
```

Downloads and installation directories are fixtures. The native Windows PATH check saves and restores the agent's user and process PATH in `finally`; on a non-Windows runtime it explicitly reports that check as not run. The installer CI job runs the Unix fixture tests and the native Windows scenarios independently of the program build jobs.

Before calling a platform supported, verify a published release on that platform: follow the user installation command, start Studio, run `curbcheck --help`, and check the commands remain discoverable from a new terminal. Record the release tag, OS, architecture and actual result. Fixture success, an emulated Linux-container run and a native published-release check are distinct evidence.

## Run verification from a clean revision

For verification tied to the recorded Studio commit, tracked files must match HEAD. Untracked files may remain. From the repository root:

```sh
make start-verification-run
source tmp/verification-run.sh
```

The start command asks before replacing an existing `tmp/`. For non-interactive use, `CONFIRM_TMP_WIPE=1 make start-verification-run` confirms its deletion. Sourcing the generated file verifies the run configuration and recreates the disposable product clone at the pin. Follow [Test setup](../testing/procedures/README.md) for preparation and execution.

For the scripted carried verification from a clean revision:

```sh
DEVELOPER_MODE=FALSE make test-curbcheck
```

The explicit value overrides developer mode retained in an earlier run file. This target starts its own run and recreates `tmp/`; it does not require the manual setup above first. The product pin is in `tests/cyberready-test-product.pin`. Changing that pin is a separate maintainer decision.
