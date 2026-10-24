# Curbpack Studio

Curbpack Studio provides a local UI for Requirements, evidence Discovery and Claims, Checks, and review of results. The PoC2 pilot code and tests are already present in this repository. Curbpack and CTAM are being retired; neither is a required runtime dependency.

## Where to start

- `AGENTS.md` - agent entry point; `.cursor/skills/story-workflow/SKILL.md` governs approved story execution.
- `policies/` - project-wide engineering rules.
- `docs/arch/ARCHITECTURE.md` and subsystem `ARCHITECTURE.md` - current system/subsystem architecture contracts.
- `docs/reference/packs2.md` - imported Packs v2 data-model reference; provenance and status in `docs/reference/README.md`.
- `docs/agile/`, `docs/req/`, `docs/test/` - user stories, derived requirements, and acceptance evidence.
- `plan/` - active story plans. `impl/` - finished story plans. `impl/pilot/` - imported pilot protocols, not the live board.
- `app/`, `requirements/`, `claims/`, `discovery/`, `checks/`, `review/`, `common/` - actual pilot implementation.
- `tests/` - existing Python tests.

`make start` starts the pilot. `make test` and `make ci-tests` run the same tests. `make package` builds a binary for the operating system it is run on. License: Apache-2.0 (`LICENSE`).
