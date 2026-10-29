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

The cover's **Developer** section links the Claim editor, Scaffold, a sample Requirement editor, and **Prepare sample workspace**. Prepare builds a small demo workspace. It does not select the Pack for a product repository.

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

On macOS ARM64 or Windows x64:

```sh
make package
```

This builds the Studio binary and a separate curbcheck binary for the current host, then smoke-tests both. See [Install](../user-guides/install.md) for artifact names and checksum commands. Linux uses the source checkout.

## Maintainer notes

| Document | Purpose |
| --- | --- |
| [Official XML sources](xml-sources.md) | Obtain, refresh, and verify the pinned CRA and NIS2 Formex XML. |
