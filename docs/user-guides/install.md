# Install Curbpack

Install the Curbpack CLI and verify that it works before continuing with the getting-started guide.

## 1. Install on macOS or Linux

Use the supported installer:

```bash
curl -fsSL https://raw.githubusercontent.com/RI-SE/curbpack/main/scripts/install.sh | sh
```

The installer places the `curbpack` binary in a user-local bin directory.

If that directory is not already on your `PATH`, follow the PATH instruction printed by the installer before continuing.

For example:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then check that Curbpack is available:

```bash
curbpack --help
```

## 2. Install on Windows

Run the supported installer from PowerShell:

```powershell
irm https://raw.githubusercontent.com/RI-SE/curbpack/main/scripts/install.ps1 | iex
```

The installer adds the Curbpack installation directory to your user `PATH`.

If `curbpack` is not available immediately afterwards, open a new PowerShell window and try:

```powershell
curbpack --help
```

## 3. Verify the installation

Run:

```bash
curbpack doctor
```

`doctor` checks the local Curbpack installation and runtime environment.

Then inspect the available commands:

```bash
curbpack --help
```
 

## 4. Repair an existing installation

If Curbpack is already installed and the command itself is available, local installation settings can be repaired with:

```bash
curbpack doctor --repair
```

Repair does not download or update Curbpack.

On Windows, the installer also supports local repair:

```powershell
.\install.ps1 -Repair
```

If the Curbpack binary itself is missing, reinstall instead.

## 5. Next

Continue with [Getting started](getting-started.md) to try Curbpack on the reference product.
