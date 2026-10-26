# Contributing

Curbpack Studio and curbcheck live in this repository. The license is Apache-2.0 (`LICENSE`).

This page is how a change gets in. It is not a second data contract. Persistent Pack, Requirement, Claim, signature, and result fields are [Packs v2](docs/reference/packs2.md). Product use is [docs/README.md](docs/README.md). How to run the suites is [Development](docs/development/README.md).

Approved story work follows [AGENTS.md](AGENTS.md) and `.cursor/skills/story-workflow/SKILL.md`. Engineering rules are in `policies/`. Open product questions are in [docs/agile/DECISIONS.md](docs/agile/DECISIONS.md). Do not decide one of those by opening a pull request.

## What a change needs

| Change | Required control |
| --- | --- |
| A change to behavior | A test that shows the new behavior, tied to the story that asked for it. Record the command and the result before and after, so a person can read what moved. |
| A change to a requirement, or a fix for a defect the checks did not catch | The failing test is committed before the fix. |
| A new check id | Change [Packs v2 §4](docs/reference/packs2.md) in this repository first. An id that section does not name is not registered. `exist` and `contents` already compose presence, size, headings, and a token. |
| Trust, digests, attestation, or cryptography | A person who did not write the change reviews it before merge. Signing stays the `signed` block in Packs v2 §2.6. DSSE and Sigstore are not a prerequisite. Negative tests cover changed content and a signature that does not verify. |
| The persistent format | Edit Packs v2 here, and keep a checked-in example in that file valid. Do not add a second schema beside it. |
| A new required CI context | Three clean runs while that context is not yet required. Then a person changes the ruleset. |

Story execution is stricter than the first row: write the failing test, make the smallest change, run the regression that story touches, then one local commit for that step. The skill has the sequence.

## Tests

Two suites. They do not call each other.

| Command | What it runs |
| --- | --- |
| `make test` | Studio. `tests/`. Does not clone a product. |
| `make test-curbcheck` | curbcheck against a fresh clone of the pinned product. Start from [Testing curbcheck](docs/testing/README.md). |
| `make ci-tests` | The mandatory CI checks. `ONLY=name` runs one. |

A green Studio run is not a curbcheck pass. A passing Check is not a legal conformity determination.

## Git

Local commits for a verified story step are part of the workflow.

Do not push, open a pull request, tag, publish, rewrite history, or force-push unless someone asked for that. Do not commit private keys, credentials, or a generated workspace.
