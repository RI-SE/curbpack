# Development

How to work in a Studio checkout. Product teams using Studio on their own repository start in [Install](../user-guides/install.md) and the [developer guide](../user-guides/developers.md).

## Two test targets

Studio and curbcheck stay in this repository. Their tests do not call each other.

| Command | What it verifies | Where it lives |
| --- | --- | --- |
| `make test` | Studio functional tests | `tests/` via `scripts/ci/checks/tests.py` |
| `make test-curbcheck` | curbcheck on a fresh product clone | `tests/check/`, preparation in [testing/README.md](../testing/README.md) |
| `make ci-tests` | The mandatory CI checks | `scripts/ci/run.py`. `ONLY=tests` selects the Studio suite |

`make test` does not run `tests/check/`. `make test-curbcheck` does not start the Studio application.

### Studio

From the repository root:

```sh
make test
```

That is the same suite CI runs for the `tests` check. It does not clone the reference product.

### curbcheck

Follow [testing/README.md](../testing/README.md). From the repository root, start the run first:

```sh
CONFIRM_TMP_WIPE=1 make start-verification-run
source tmp/verification-run.sh
```

Then prepare R1 and run the seven carried checks as that document states, or run the same sequence with:

```sh
make test-curbcheck
```

Packs and claims come from the clone's `external_test/curbpack-studio/`. A catalogue row whose procedure still calls `curbpack` is outside the pass. SSH access to `git@github.com:RI-SE/cyberready-test-product.git` is required for the clone.

## Package

`make package` builds the Studio binary and a separate curbcheck binary for this host, then smokes both. See [Install](../user-guides/install.md) and [CI/CD](../user-guides/ci-cd.md).

## Check in a product pipeline

[Check in CI](ci.md) is the job a product repository runs on GitHub Actions, GitLab CI, and Jenkins. `make test` and `make ci-tests` test this repository.

## Temporary notes

Delete a note when it is no longer needed. [Official XML sources](xml-sources.md) stays; it is the procedure for the pinned Formex XML.

| Note | What it keeps |
| --- | --- |
| [Official XML sources](xml-sources.md) | How to obtain, refresh, and verify the pinned CRA and NIS2 Formex XML. |
| [CLI disposition](cli.md) | Previous commands and which Studio page or command does that job now. |
| [Pack authoring crosswalk](pack-authoring-crosswalk.md) | Previous pack JSON beside the Requirement and Claim objects Studio stores. |
