# Developing Curbpack

This guide is for people changing Curbpack Studio and curbcheck in this repository. Product teams using Studio on their own repository start with [Install](../user-guides/install.md) and [Using Studio in a product repository](../user-guides/developers.md).

## Run from a checkout

Run these commands from the repository root. Studio's Python dependency is `cryptography`, listed in `requirements.txt`.

macOS or Linux:

```sh
python3 -m pip install -r requirements.txt
make start
```

Windows:

```powershell
python -m pip install -r requirements.txt
python -m app
```

`make start` runs `python3 -m app`, or `python -m app` on Windows. Open the URL printed at startup, usually `http://127.0.0.1:8770`. `make stop` stops the process listening on port 8770.

A checkout uses `data/workspace` inside the repository. For a disposable Studio workspace:

```sh
python3 -m app --workspace /absolute/path/to/disposable-workspace
```

Product data paths come from the chosen product repository's `curbpack.json`. See [Workspace configuration](../reference/workspace.md).

The cover shows Pack Editor, Discovery & Claims, Check, and Review. Developer routes (`/claims`, `/scaffold`, `/requirement`, `/prepare`) are not linked from the cover; they remain reachable by URL. Prepare builds a small demo workspace and does not select the Pack for a product repository.

## Run curbcheck from source

The checkout's command is `scripts/bin/curbcheck`. It takes the same arguments as the packaged binary:

```sh
scripts/bin/curbcheck --repo /path/to/product-repo -j
```

It reads the product's `curbpack.json` directory fields. `--packs` and `--requirements` take comma-separated id lists for one run. JSON output requires `-j` or `-o`; otherwise the result is printed on stdout. See [curbcheck](../reference/curbcheck-cli.md) for arguments, output, and exit codes.

## Make a change

Follow [CONTRIBUTING.md](../../CONTRIBUTING.md), [AGENTS.md](../../AGENTS.md), and the [engineering policies](../../policies/). Approved story work follows [the story workflow](../../.cursor/skills/story-workflow/SKILL.md); stories live in [Agile](../agile/README.md).

Read the [system and subsystem architecture](../arch/README.md) before changing affected code. [Packs v2](../reference/packs2.md) owns the persistent data formats; [Workspace configuration](../reference/workspace.md) owns configuration and path locations.

## Test a change

[Testing during development](testing.md) describes the local feedback loop, checks for a completed change, and the separate curbcheck verification run. Formal procedures and traceability are in [Testing curbcheck](../testing/README.md).

## Build the programs

On Linux x64, macOS ARM64 or Windows x64:

```sh
make package-curbcheck
make package-studio
```

Each command builds and smoke-tests only its own program, using a separate script under `scripts/build/` and output directory under `dist/`. `make package` runs both. The CI jobs and platform matrices are separate too. See [Install](../user-guides/install.md) for released artifacts and checksum commands; build support does not mean a binary has already been published.

`python3 scripts/build/package_installers.py` packages four standalone installer scripts under `dist/installers/`, with `SHA256SUMS`. The Studio installers select both programs; the curbcheck installers select only the checker. The shared implementations are `scripts/install/unix.sh` and `scripts/install/windows.ps1`; packaging adds a fixed program selection to each standalone script, so installed users do not need these source files. The independent installer CI job tests and uploads those exact scripts. Release publishing reuses the tested scripts alongside the binaries. See [Install](../user-guides/install.md) for installer commands and the manual alternative.

## Product CI integration

The root [`action.yml`](../../action.yml) provides `uses: RI-SE/curbpack@<release-tag>` for GitHub Actions. It downloads the released checker, verifies its checksum, runs it against the product checkout, and retains the JSON result even when Checks fail. Its shell script is [`scripts/ci/curbcheck-action.sh`](../../scripts/ci/curbcheck-action.sh). Product workflow examples for GitHub, GitLab and Jenkins are in [CI/CD](../user-guides/ci-cd.md).

`curbcheck` supplies Check outcomes and a process exit status. The product team's own policies determine how those outcomes affect release decisions, approvals and publishing. Curbpack does not prescribe or execute the product's release process. The legacy Action's `prepare-release` step generated review material; it is not part of this Action. This repository's release workflow publishes Curbpack itself and is separate from any product release process.

## Maintainer notes

| Document | Purpose |
| --- | --- |
| [Official XML sources](xml-sources.md) | Obtain, refresh, and verify the pinned CRA and NIS2 Formex XML. |
