# Troubleshooting

Use this page when Curbpack does not install, start, or behave as expected.

For installation instructions, see [Install Curbpack](install.md).

## `curbpack: command not found`

If your shell cannot find `curbpack`:

1. Open a new terminal window.
2. Check that the Curbpack installation directory is on your `PATH`.
3. If the binary is missing, reinstall Curbpack.

On macOS and Linux, the default installation directory is typically:

```bash
$HOME/.local/bin
```

To add it to the current shell:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Add the corresponding command to your shell configuration if the directory should be available permanently.

On Windows, the default installation directory is:

```text
%LOCALAPPDATA%\Programs\Curbpack\
```

Open a new PowerShell or Terminal window after changing the User `PATH`.

`curbpack doctor --repair` cannot help if the shell cannot find the `curbpack` command in the first place.

## Git Is Missing

`curbpack doctor`, `demo`, `check`, and `attest` require Git to be available on `PATH`.

Install Git using the normal method for your operating system:

- macOS: Xcode Command Line Tools, Homebrew, or another Git installation
- Linux: your distribution's Git package
- Windows: [Git for Windows](https://git-scm.com/download/win)

After installing Git, open a new terminal and try the command again.

## Installation or Checksum Failure

If installation fails while downloading or verifying Curbpack:

1. Download the release again.
2. Use the pinned release rather than an arbitrary development version.
3. Verify the downloaded file against `checksums.txt`.
4. Do not use the binary if the checksum does not match.

See [Install Curbpack](install.md) for the current installation procedure.

## macOS Gatekeeper Blocks Curbpack

If macOS reports that Curbpack cannot be opened:

1. Verify the downloaded binary against the release checksum.
2. Open **System Settings → Privacy & Security** and allow the application if appropriate.
3. After verifying the checksum, the quarantine attribute can be removed with:

```bash
xattr -d com.apple.quarantine ~/.local/bin/curbpack
```

Do not remove quarantine from an unverified download.

## Windows SmartScreen, Execution Policy, or Defender

### SmartScreen

Verify the downloaded binary first.

You can then unblock the file through its Properties dialog or with:

```powershell
Unblock-File path\to\curbpack.exe
```

### PowerShell Execution Policy

If the installation script is blocked by PowerShell execution policy, use the installation instructions in [Install Curbpack](install.md).

A user-level PowerShell policy can also be configured with:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Only change execution policy if that is appropriate for your environment.

### Microsoft Defender Removed the Binary

If Defender quarantined or deleted `curbpack.exe`, restore or review it through **Protection history** and verify the binary before using it.

If the executable has been deleted, reinstall Curbpack. `doctor --repair` does not download or restore a missing binary.

### The Executable Is Locked

If installation fails because `curbpack.exe` is currently in use, close any running Curbpack process and retry the installation.

## `curbpack scan` Is Not Available

If you see:

```text
unknown command "scan"
```

or `scan` is missing from the help output, you may be running an older Curbpack version.

`scan` is available from v0.5.3.

Check the installed version and reinstall the current pinned release if necessary.

If `scan` works from a development checkout but not from your installed command, check which executable your shell is using. An older installation directory may still appear earlier on `PATH`.

After correcting the installation, open a new shell and try again.

## Git Hooks and Line Endings

`curbpack init --hooks` can install the Curbpack pre-commit hook.

Curbpack does not silently overwrite arbitrary custom hooks.

If `doctor` reports an exact legacy Curbpack hook from v0.5.2–v0.5.5 that still runs:

```text
curbpack check --heal
```

it can be migrated with:

```bash
curbpack init --hooks
```

If you have a custom or composed hook, edit it manually instead.

If Curbpack reports CRLF line endings in a hook, convert the hook to LF.

## WSL and Windows Filesystems

Avoid mixing execution environments unnecessarily.

For a repository on NTFS, prefer the native Windows Curbpack executable from PowerShell or Command Prompt.

For a repository inside a Linux filesystem under WSL, prefer the Linux Curbpack binary inside WSL.

Using Linux tools against repositories under `/mnt/c` can cause problems with Git hooks and line endings.

## Paths Containing Spaces

Curbpack supports paths containing spaces, but shell paths must be quoted correctly.

macOS and Linux:

```bash
curbpack demo --out "/tmp/curbpack smoke" --keep
```

PowerShell:

```powershell
curbpack demo --out "$env:TEMP\curbpack smoke" --keep
```

## `sock` on Windows

The optional MCP `sock` example uses Unix IPC and is not part of the main Curbpack executable.

It is not required for normal Curbpack use.

See [`examples/mcp/`](../../examples/mcp/) and [Stable Contracts](../reference/stable-contracts.md) for details.

## `doctor --repair`

`curbpack doctor --repair` is a local repair operation. It does not download or update Curbpack.

If the Curbpack executable itself is missing, reinstall Curbpack instead.

If `doctor --repair` exits with code 2 because the required binary is missing, follow the installation instructions in [Install Curbpack](install.md).

## Still Stuck

Run:

```bash
curbpack doctor
```

If Curbpack still does not work, open a [first-move stuck](../../.github/ISSUE_TEMPLATE/first_move_stuck.yml) issue and include:

- operating system
- `curbpack version`
- relevant command and exit code
- `curbpack doctor` output

Do not include passwords, tokens, credentials, or other secrets.
