# Install and start Curbpack Studio

The first way to start is the program built for your computer. Download it and run it. A source checkout is for people changing this repository, and for Linux, which has no packaged file.

## 1. Download and start

The [latest release](https://github.com/RI-SE/curbpack/releases) has the commands. `curl` downloads the file so you can run it. The hash command is there if you want to compare.

| Computer | Curbpack Studio | curbcheck |
| --- | --- | --- |
| Windows x64 | `curbpack-studio-windows-x64.exe` | `curbcheck-windows-x64.exe` |
| macOS ARM64 | `curbpack-studio-macos-arm64` | `curbcheck-macos-arm64` |

macOS. To download and run:

```sh
curl -fsSL -O https://github.com/RI-SE/curbpack/releases/download/<tag>/curbpack-studio-macos-arm64
curl -fsSL -O https://github.com/RI-SE/curbpack/releases/download/<tag>/curbcheck-macos-arm64
chmod +x curbpack-studio-macos-arm64 curbcheck-macos-arm64
./curbpack-studio-macos-arm64
```

To compare the hash. The digits under each command are an example. The release page prints the hash for that release.

```sh
shasum -a 256 curbpack-studio-macos-arm64
<64 hex digits>

shasum -a 256 curbcheck-macos-arm64
<64 hex digits>
```

Windows. `curl.exe` is curl. `curl` in PowerShell is a different command. To download and run:

```powershell
curl.exe -fsSL -O https://github.com/RI-SE/curbpack/releases/download/<tag>/curbpack-studio-windows-x64.exe
curl.exe -fsSL -O https://github.com/RI-SE/curbpack/releases/download/<tag>/curbcheck-windows-x64.exe
.\curbpack-studio-windows-x64.exe
```

To compare the hash. Same example digits. Use the hash on the release page.

```powershell
Get-FileHash -Algorithm SHA256 .\curbpack-studio-windows-x64.exe
<64 hex digits>

Get-FileHash -Algorithm SHA256 .\curbcheck-windows-x64.exe
<64 hex digits>
```

The process prints a local URL. Open it. The usual one is `http://127.0.0.1:8770`. This program keeps its workspace in `~/curbpack-studio/workspace`. Pass `--port` if 8770 is taken, or `--workspace` to use another directory.

`curbcheck` is the other file. It does not open Studio. A product check reads `curbpack.json` in the repository:

```sh
./curbcheck-macos-arm64 --repo /path/to/product
```

`--packs` and `--out` are optional. They replace `<curbpack>/packs` and `<curbpack>/run-result.json`.

On Windows the program is `curbcheck-windows-x64.exe`.

In the browser, confirm the cover loads and that **Pack Editor**, **Discovery & Claims**, **Check**, and **Review** open. Continue with [Getting started](getting-started.md).

## 2. If it does not start

Record the program, the platform, the command, and the error. Do not delete a workspace or regenerate Packs as a generic fix. If the port is taken, start with `--port` set to a free port. More cases are in [Troubleshooting](troubleshooting.md).

## 3. For people changing this repository

This is not how a product team starts Studio. Use it to change Curbpack, or on Linux, where no packaged file is built. Studio's Python dependency is `cryptography`, listed in `requirements.txt`.

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

`make start` runs `python3 -m app`. `make stop` stops the process listening on port 8770. A source checkout uses `data/workspace` inside the repository. Open the URL printed at startup.

For a disposable workspace:

```sh
python3 -m app --workspace /absolute/path/to/disposable-workspace
```

On a source checkout, the command is `scripts/bin/curbcheck`, with the same arguments as the packaged file. `make package`, run on macOS ARM64 or Windows x64, builds the two files in the table above for that computer only.

The cover's **Developer** section is the same audience: Claim editor, Scaffold, a sample requirement editor, and **Prepare sample workspace**. Prepare builds a small demo workspace. It does not become the Pack Check uses unless you select it.

To check this repository itself:

```sh
make test
make ci-tests
```

`make test` runs the Studio functional tests. It does not run curbcheck's product clone. `make test-curbcheck` is that run; see [Development](../development/README.md) and [Testing curbcheck](../testing/README.md). `make ci-tests` runs the mandatory CI checks. `ONLY=tests` selects the Studio suite. Today the only registered check name is `tests`.

These commands do not certify a product repository. The longer product-repository procedure is the [developer guide](developers.md).
