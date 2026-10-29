# Install and start Curbpack Studio

The first way to start is the program built for your computer. Download it and run it. A source checkout is for people changing this repository, and for Linux, which has no packaged file. That start is [Changing this repository](developers.md#10-changing-this-repository).

## 1. Download and start

The [latest release](https://github.com/RI-SE/curbpack/releases) has the commands. `curl` downloads the file so you can run it. The hash command checks the download. Each file prints OK.

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

To check the hash. Paste the block. Each file prints OK. The release page has this block with the hash for that release.

```sh
shasum -a 256 -c <<'EOF'
<64 hex digits>  curbpack-studio-macos-arm64
<64 hex digits>  curbcheck-macos-arm64
EOF
```

Windows. `curl.exe` is curl. `curl` in PowerShell is a different command. To download and run:

```powershell
curl.exe -fsSL -O https://github.com/RI-SE/curbpack/releases/download/<tag>/curbpack-studio-windows-x64.exe
curl.exe -fsSL -O https://github.com/RI-SE/curbpack/releases/download/<tag>/curbcheck-windows-x64.exe
.\curbpack-studio-windows-x64.exe
```

To check the hash. Paste the block. Each file prints OK. The release page has this block with the hash for that release.

```powershell
@(
  '<64 hex digits>  curbpack-studio-windows-x64.exe',
  '<64 hex digits>  curbcheck-windows-x64.exe'
) | ForEach-Object {
  $digest, $name = $_ -split '  ', 2
  $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $name).Hash.ToLowerInvariant()
  if ($actual -eq $digest) { "${name}: OK" } else { "${name}: FAILED" }
}
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
