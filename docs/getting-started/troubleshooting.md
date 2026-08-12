# Troubleshooting

Shared stuck? page for Windows, macOS, and Linux. Install SoR: [install.md](install.md).

Not conformity assessment — a green `check` is local structural evidence for human review.

---

## PATH / command not found

| Check | Fix |
|-------|-----|
| `curbpack` not found after install | Open a **new** shell; confirm install dir on PATH |
| Still missing | `curbpack doctor --repair` (local PATH/alias only; Windows also `install.ps1 -Repair`) |
| Binary gone | Full reinstall — [install ladders](install.md) |
| Windows session PATH stale | New PowerShell / Terminal window after User PATH update |

Unix permanent hint:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Windows default install dir: `%LOCALAPPDATA%\Programs\Curbpack`.

---

## Git missing

`doctor` / `demo` / `check` / `attest` need `git` on PATH.

- macOS: Xcode CLT or Homebrew `git`
- Linux: distro package (`git`)
- Windows: [Git for Windows](https://git-scm.com/download/win) (or winget outside this train)

---

## macOS Gatekeeper

Installer / binary “can't be opened”:

1. Verify sha256 against release `checksums.txt` ([install.md](install.md) Ladder 3).
2. System Settings → Privacy & Security → Allow.
3. After checksum OK: `xattr -d com.apple.quarantine ~/.local/bin/curbpack`

---

## Windows SmartScreen / ExecutionPolicy / Defender

| Issue | What to try |
|-------|-------------|
| SmartScreen | Unblock in file Properties; or `Unblock-File path\to\curbpack.exe` |
| ExecutionPolicy | Ladder 1 with `-ExecutionPolicy Bypass`; or `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Defender quarantine | Restore from Protection history → **full reinstall** (repair cannot resurrect deleted exe) |
| Running-exe lock / access denied | Close running `curbpack.exe`, retry install; atomic `.new` replace fails closed with a clear message |

---

## WSL ↔ NTFS

Prefer the native Windows exe on NTFS repos opened from PowerShell/cmd, or the Linux binary inside WSL on a Linux filesystem. Mixing WSL+`/mnt/c` can confuse hooks and line endings — hooks are **LF-only**.

---

## Hooks / CRLF

`curbpack init --hooks` writes LF-only `pre-commit`. If doctor reports CRLF, re-run init hooks or convert:

```bash
# from repo root
curbpack init --hooks
```

---

## `doctor --repair` exit 2

Binary missing. Print install command and reinstall — repair never downloads / never auto-updates.

---

## `sock` on Windows

Expected failure: sock is **Unix-only** optional Coreward IPC. Golden path does not use it. See [stable-contracts](../stable-contracts.md).

---

## Spaced paths

Demo/init work under paths with spaces (CI covers this). Quote paths in shells:

```bash
curbpack demo --out "/tmp/curbpack smoke" --keep
```

```powershell
curbpack demo --out "$env:TEMP\curbpack smoke" --keep
```

---

## Still stuck

1. `curbpack doctor`  
2. [install.md](install.md) Ladder 1  
3. Open a GitHub issue with OS, `curbpack version`, and doctor output (no secrets)
