# Troubleshooting

Shared stuck? page for Windows, macOS, and Linux. Install SoR: [install.md](install.md).

Not conformity assessment — a green `check` is local structural evidence for human review.

## Decision tree (start here)

1. **`curbpack: command not found`** → new shell → confirm install dir on PATH → `doctor --repair` → full reinstall ([install](install.md) Ladder 1–3).
2. **Install / checksum fail** → re-fetch from pinned **`v0.5.5`** release URL (not `main`) → verify `checksums.txt` → refuse on mismatch.
3. **`doctor` / `demo` / `check` fail for missing `git`** → install Git, reopen shell.
4. **macOS Gatekeeper / Windows SmartScreen** → verify sha256 first → Allow / Unblock → then quarantine/`Unblock-File` only after checksum OK.
5. **Hooks / CRLF / WSL+NTFS weirdness** → convert to LF; `init --hooks` only replaces exact known Curbpack bodies (see Hooks section). Prefer native Windows exe on NTFS vs Linux binary on Linux FS.
6. **Still stuck** → [first-move stuck](../../.github/ISSUE_TEMPLATE/first_move_stuck.yml) with pin + exit code; no certification language.

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

## Hooks / CRLF / legacy heal

`curbpack init --hooks` installs an LF-only non-healing `pre-commit` when missing, or replaces an **exact** known Curbpack body from v0.5.2–v0.5.5 (`check --heal`). It refuses custom or composed hooks and never silently overwrites them.

| Doctor finding | Action |
|----------------|--------|
| `legacy curbpack check --heal (v0.5.2–v0.5.5)` | Safe: `curbpack init --hooks` (exact-match migrate; backup `.curbpack-legacy.bak`) |
| `custom hook still runs check --heal` | Edit the hook by hand to remove `--heal`. Do **not** blind-run `init --hooks` — it will refuse and leave your hook intact. |
| `CRLF detected` | Convert the file to LF. `init --hooks` only rewrites exact known Curbpack bodies. |

```bash
# safe only when doctor reports the exact legacy heal body
curbpack init --hooks
```
---

## `doctor --repair` exit 2

Binary missing. Print install command and reinstall — repair never downloads / never auto-updates.

---

## `curbpack scan` not found / wrong release

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `unknown command "scan"` or `scan` missing from help | Binary from **v0.5.2 or older** (scan ships in **v0.5.3+**) | Reinstall with **`v0.5.5`** (see [install.md](install.md) Ladder 0) |
| `curbpack scan` works in dev checkout but not after install | Stale PATH or old install dir | New shell; `curbpack doctor --repair`; or full reinstall at **v0.5.5** |
| Used wrong install URL / old binary | `scan` missing or wrong version | Re-run Ladder 0 from [install.md](install.md) (`main` installer → smoke-verified binary) |
| npm / `npx` path | npm wrapper **deferred** (PR5) — not the stranger path | Use `install.sh` / `install.ps1` instead |

Pass criteria after fix: `curbpack scan` in any git repo exits 0, prints Art 14 reporting clock + early/late Exit 0 invariant + `Scan complete — repository unchanged.`, and `git status --porcelain` stays empty. `Next (optional):` appears only when open findings remain (v0.5.5+).

---

## `sock` on Windows

Expected failure: optional MCP sidecar Unix IPC lives under [`examples/mcp/`](../../examples/mcp/) — not in the main binary. Golden path does not use it. See [stable-contracts](../stable-contracts.md).

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
3. Open a [first-move stuck](../../.github/ISSUE_TEMPLATE/first_move_stuck.yml) issue with OS, `curbpack version`, and doctor output (no secrets)
