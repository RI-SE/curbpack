# Curbpack Studio

Curbpack Studio is the local application for Requirements, evidence Discovery and Claims, Checks, and review. curbcheck is the check program in the same repository. The PoC2 pilot code and tests are already here. Curbpack and CTAM are being retired; neither is a required runtime dependency.

## Where to start

- [Documentation index](docs/README.md) — install, product use, and how this repository is tested.
- [Development](docs/development/README.md) — how to run Studio tests and curbcheck verification from a checkout.
- [Testing curbcheck](docs/testing/README.md) — `make test-curbcheck`, the seven carried checks, and the copied catalogue under `tests/check/`.
- [CONTRIBUTING.md](CONTRIBUTING.md) — what a change needs before it lands.
- `AGENTS.md` — agent entry point; `.cursor/skills/story-workflow/SKILL.md` governs approved story execution.
- `policies/` — project-wide engineering rules.
- `docs/arch/ARCHITECTURE.md` and subsystem `ARCHITECTURE.md` — current architecture contracts.
- `docs/reference/packs2.md` — Packs v2 data-model reference; provenance in `docs/reference/README.md`.
- `docs/agile/`, `docs/req/` — user stories and derived requirements.
- `plan/` — active story plans. `impl/` — finished story plans. `impl/pilot/` — imported pilot protocols, not the live board.
- `app/`, `requirements/`, `claims/`, `discovery/`, `checks/`, `review/`, `common/` — implementation.
- `tests/` — Studio functional tests. `tests/check/` — curbcheck verification procedures.

## Commands

| Command | What it does |
| --- | --- |
| `make start` | Start the Studio application |
| `make test` | Studio functional tests (`scripts/ci/checks/tests.py`). Does not run `tests/check/` |
| `make test-curbcheck` | Clone the pinned product, apply R1, run the seven carried checks, then report the copied catalogue |
| `make ci-tests` | Mandatory CI checks. `ONLY=name` runs one check |
| `make package` | Build and smoke-test Studio and curbcheck binaries for this host |

License: Apache-2.0 (`LICENSE`).
