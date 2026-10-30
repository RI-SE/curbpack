# Troubleshooting

Use this page when Studio does not start or a Check does not do what you expected.

Installation is [Install](install.md).

## The application does not start

After using the installer, run `curbpack-studio`. If you installed manually, run the downloaded `curbpack-studio-<host>` file (`.exe` on Windows). It prints a local URL. Its workspace is `~/curbpack-studio/workspace`.

If the command is not found, check PATH: Unix installers use `~/.local/bin` by default and print a PATH instruction. The Windows installer adds `%LOCALAPPDATA%\Programs\Curbpack` to your user PATH; open a new terminal if needed. See [Install](install.md).

From a source checkout:

```sh
python3 -m pip install -r requirements.txt
python3 -m app --workspace /absolute/path
```

Check the interpreter, that `cryptography` imported, that port 8770 is free, and that the workspace path is writable. Pass `--port` if 8770 is taken. The process prints the URL. A source checkout defaults to `data/workspace` in the Studio repository. A frozen build defaults to `~/curbpack-studio/workspace`.

## Git is missing or the repository cannot be used

Check records `commit` and `worktree` when Git has a HEAD, and omits both when it does not. A missing `git` binary on a path that a Git Check needs is a failure of that Check, not a skipped row. Install Git the usual way for the operating system and open a new shell.

A dirty tree is a real result. Do not present it as a clean commit. Requirements signing works on a directory that is not a Git checkout. Signing never commits.

## Packaging or checksum failure

If a downloaded Studio binary fails the checksum command on its release page, do not run it. Download the file again from the release you intended. The steps and the command are in [Install](install.md). This guide does not list a published checksum, because a published pair of release binaries was not verified from this tree.

An installer download returning HTTP 404 usually means that release does not contain the selected installer or platform binary. Check its asset list. Older releases without installers can still be installed using [Manual installation](install.md#manual-installation). A failed binary download or checksum stops an installer before replacing the installed programs.

`make package` builds for the operating system you run it on. It does not prove that a binary exists for another operating system.

## macOS Gatekeeper

Verify the file against the release checksum before allowing it. If Gatekeeper blocks a verified file from an unidentified developer, use System Settings, Privacy & Security, Open Anyway. Do not bypass a warning that identifies actual malware. Prefer [Run from a checkout](../development/README.md#run-from-a-checkout) when you do not have a release binary you trust.

## Windows SmartScreen, execution policy, Defender

Verify the file against the release checksum before allowing it through SmartScreen. If Defender removed a packaged `exe`, investigate the detection before restoring it, or rebuild with `make package` on that machine. The installer does not change execution policy, disable antivirus or bypass operating-system protections. If your organisation blocks downloaded scripts, use [Manual installation](install.md#manual-installation) and its own approval process.

If a package build fails because the executable is locked, close the running process and retry.

## Git hooks

Studio does not install Git hooks. A Check in CI is `curbcheck`. It does not write stubs. Scaffold, used by a person, writes a new file and refuses to overwrite.

## WSL and Windows filesystems

Keep the process and the repository on the same side of the filesystem boundary. A Linux Python against a repository under `/mnt/c` is a common source of line-ending and Git-status surprises. `worktree: dirty` will then be telling the truth about those differences.

## Paths with spaces

Quote paths.

```sh
python3 -m app --workspace "/tmp/curbpack smoke"
```

```powershell
python -m app --workspace "$env:TEMP\curbpack smoke"
```

## Check ran and nothing failed, but the product has no evidence

A run with no Claim rows exits 1 and the page says it is not a successful verification. A run that only has an `exist` Check on `README.md` will stay green when you delete `SECURITY.md`. Look at `checks[].args` before you conclude the tool missed the file.

The Pack open in Pack Editor is not the Pack Check loaded. Read `curbpack.json`. A file named `.curbpack.json` is ignored.

A Claim that names a Requirement the selected Pack does not contain stops the run with an error. No result file is written.

## Still stuck

Record:

- the Studio commit or the build you ran
- the operating system
- the exact command, including `--workspace` and any `curbcheck` arguments you passed (`--repo`, `--packs`, `--out`, `--skip`)
- the workspace path, with secrets removed
- the Requirement id, Claim id, and Check arguments
- the run result's `commit` and `worktree`
- the failing row or the full test output

Do not attach signing keys or customer evidence.

The process output and the run-result JSON are the transcript.
