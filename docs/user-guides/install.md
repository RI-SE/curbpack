# Install and start Curbpack Studio

The Studio installer installs **both `curbpack-studio` and `curbcheck`**. If you only need the checker, use the separate curbcheck installer. Neither requires Python or a source checkout. Git must be installed for Git-based Checks.

The commands below require a release containing the new installer files. For an older release without installers, use [Manual installation](#manual-installation). Linux also requires a release containing the Linux x64 binaries. Available files are listed under [Curbpack releases](https://github.com/RI-SE/curbpack/releases).

## Install Studio, including curbcheck

### macOS ARM64 or Linux x64

Run in a terminal. These commands use `curl`; install it through your Linux distribution if it is not already available.

```sh
curl -fsSL https://github.com/RI-SE/curbpack/releases/latest/download/install-studio.sh -o install-studio.sh && sh install-studio.sh
```

The installer detects the host, downloads both programs from one release, and verifies both SHA-256 checksums before replacing any installed program. It installs them as `~/.local/bin/curbpack-studio` and `~/.local/bin/curbcheck`, without sudo. Linux requires glibc, as on Ubuntu 22.04 or newer; Linux ARM64 and Alpine/musl are not targets of this installer.

If `~/.local/bin` is not on your `PATH`, the installer prints an instruction. For the current terminal:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

Add that line to your shell's startup file if you want it to apply to new terminals too.

### Windows x64

Run in PowerShell:

```powershell
irm https://github.com/RI-SE/curbpack/releases/latest/download/install-studio.ps1 | iex
```

This installs `curbpack-studio.exe` and `curbcheck.exe` under `%LOCALAPPDATA%\Programs\Curbpack`, verifies both downloads before replacing either program, and adds that directory to your user `PATH`. Administrator access is not required. Open a new terminal if the commands are not yet available.

## Install curbcheck only

This installs only `curbcheck`. An existing Studio installation is left alone.

macOS ARM64 or Linux x64:

```sh
curl -fsSL https://github.com/RI-SE/curbpack/releases/latest/download/install-curbcheck.sh -o install-curbcheck.sh && sh install-curbcheck.sh
```

Windows x64, in PowerShell:

```powershell
irm https://github.com/RI-SE/curbpack/releases/latest/download/install-curbcheck.ps1 | iex
```

The default locations and checksum verification are the same as for the Studio installer.

## Start and check the installation

Start Studio:

```sh
curbpack-studio
```

Open the local URL it prints, usually `http://127.0.0.1:8770`. Studio keeps its workspace in `~/curbpack-studio/workspace`. Use `--port` if 8770 is taken, or `--workspace` to choose another directory. In the browser, confirm **Pack Editor**, **Discovery & Claims**, **Check**, and **Review** open. Continue with [Getting started](getting-started.md).

The checker runs independently:

```sh
curbcheck --help
curbcheck --repo /path/to/product --out run-result.json
```

It reads the product's `curbpack.json`. Pack and Claim locations come from that file. `--packs` selects Pack ids, and `--out` requests a JSON result at the given path. See [curbcheck](../reference/curbcheck-cli.md) for all arguments.

## Choose a release or installation directory

By default, an installer resolves GitHub's latest release once, then uses that specific tag for all downloads. To install a particular release, download the installer from that tag too. Replace `REPLACE_WITH_RELEASE_TAG` with a published tag containing the installer and binaries.

macOS/Linux:

```sh
export CURBPACK_VERSION=REPLACE_WITH_RELEASE_TAG
curl -fsSL "https://github.com/RI-SE/curbpack/releases/download/$CURBPACK_VERSION/install-studio.sh" -o install-studio.sh && sh install-studio.sh
```

Windows PowerShell:

```powershell
$env:CURBPACK_VERSION = 'REPLACE_WITH_RELEASE_TAG'
irm "https://github.com/RI-SE/curbpack/releases/download/$env:CURBPACK_VERSION/install-studio.ps1" | iex
```

`CURBPACK_INSTALL_DIR` optionally selects another installation directory on either platform. Otherwise, no configuration is needed. Re-running an installer updates its selected programs; it does not change Studio workspaces or product data. Updates are not a transaction across both binaries: an installation-directory permission error or a program locked by Windows can still interrupt replacement after verification. Close running programs before updating.

For CI, use a pinned release as described in [CI/CD](ci-cd.md); a persistent local installation is not needed there.

## Manual installation

Use this option if you want to manage the downloaded files, location and command names yourself. The files are standalone programs. Download the matching binaries and `SHA256SUMS` from **the same release**. Replace `REPLACE_WITH_RELEASE_TAG` in the examples with the tag you chose. Verify the hashes before starting either program.

| Computer | Curbpack Studio | curbcheck |
| --- | --- | --- |
| macOS ARM64 | `curbpack-studio-macos-arm64` | `curbcheck-macos-arm64` |
| Linux x64 | `curbpack-studio-linux-x64` | `curbcheck-linux-x64` |
| Windows x64 | `curbpack-studio-windows-x64.exe` | `curbcheck-windows-x64.exe` |

### macOS ARM64

```sh
release=REPLACE_WITH_RELEASE_TAG
curl -fsSL -O https://github.com/RI-SE/curbpack/releases/download/$release/curbpack-studio-macos-arm64
curl -fsSL -O https://github.com/RI-SE/curbpack/releases/download/$release/curbcheck-macos-arm64
curl -fsSL -O https://github.com/RI-SE/curbpack/releases/download/$release/SHA256SUMS
shasum -a 256 curbpack-studio-macos-arm64 curbcheck-macos-arm64
```

Compare both printed hashes with their entries in `SHA256SUMS`. Both must match. Then:

```sh
chmod +x curbpack-studio-macos-arm64 curbcheck-macos-arm64
./curbpack-studio-macos-arm64
```

### Linux x64

```sh
release=REPLACE_WITH_RELEASE_TAG
curl -fsSL -O https://github.com/RI-SE/curbpack/releases/download/$release/curbpack-studio-linux-x64
curl -fsSL -O https://github.com/RI-SE/curbpack/releases/download/$release/curbcheck-linux-x64
curl -fsSL -O https://github.com/RI-SE/curbpack/releases/download/$release/SHA256SUMS
sha256sum curbpack-studio-linux-x64 curbcheck-linux-x64
```

Compare both printed hashes with their entries in `SHA256SUMS`. Both must match. Then:

```sh
chmod +x curbpack-studio-linux-x64 curbcheck-linux-x64
./curbpack-studio-linux-x64
```

### Windows x64

Use `curl.exe` in PowerShell:

```powershell
$release = 'REPLACE_WITH_RELEASE_TAG'
curl.exe -fsSL -O https://github.com/RI-SE/curbpack/releases/download/$release/curbpack-studio-windows-x64.exe
curl.exe -fsSL -O https://github.com/RI-SE/curbpack/releases/download/$release/curbcheck-windows-x64.exe
curl.exe -fsSL -O https://github.com/RI-SE/curbpack/releases/download/$release/SHA256SUMS
Get-FileHash -Algorithm SHA256 -LiteralPath curbpack-studio-windows-x64.exe, curbcheck-windows-x64.exe
```

Compare both printed hashes with their entries in `SHA256SUMS` (hexadecimal letter case does not matter). Both must match. Then:

```powershell
.\curbpack-studio-windows-x64.exe
```

To run the manually downloaded checker, use its filename rather than the installed command, for example `./curbcheck-macos-arm64 --repo /path/to/product` or `.\curbcheck-windows-x64.exe --repo C:\path\to\product`.

For older release binaries, run `--help` to check their supported flags; an older release may differ from the current CLI reference.

A source checkout is for people changing this repository or building for themselves. See [Run from a checkout](../development/README.md#run-from-a-checkout).

## If it does not start

Record the program, platform, command and error. A missing release file or failed checksum stops the installer before replacing any program. Do not delete a workspace or regenerate Packs as a generic fix. If the port is taken, start Studio with `--port` set to a free port. More cases are in [Troubleshooting](troubleshooting.md).
