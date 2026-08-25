# Stranger validation log (Wave B gate)

**Gate:** 3 external repos × 2 successful `curbpack scan` runs each (exit 0, read-only, Exit 0 invariant + `Scan complete — repository unchanged.` always — `Next (optional):` only when findings remain — `git status --porcelain` empty).

**Parallel recruit:** while logging strangers, offer the one-sentence [RISE Neutral Evidence Profile Pilot](rise-pilot-offer.md) to a named relying party — do not wait for all six scans.

**Install pin:** smoke-verified **`v0.5.4`** ([`scripts/install-manifest.json`](../../scripts/install-manifest.json) + [`scripts/release-gate.json`](../../scripts/release-gate.json)). Action pin stays **`@v0.5.2`**. Send-verbatim uses **`main`** install scripts (do not use `…/v0.5.4/scripts/install.sh` — that tag tree still baked older `MANIFEST_DEFAULT`). Optional pin-in-time: `CURBPACK_VERSION=v0.5.4`.

**Install (send verbatim):**

```bash
curl -fsSL https://raw.githubusercontent.com/RI-SE/curbpack/main/scripts/install.sh | sh
cd /path/to/your/git/repo
curbpack scan
```

Windows (PowerShell):

```powershell
irm https://raw.githubusercontent.com/RI-SE/curbpack/main/scripts/install.ps1 | iex
cd C:\path\to\your\git\repo
curbpack scan
```

Stop at **scan** for stranger validation. Do **not** run receipt, share, attest, pathway, or `./scripts/pilot-receipt.sh` on this path (workshop / deepen tracks only).

Contributor / unreleased installer only (labelled development):

```bash
# DEV: curl -fsSL https://raw.githubusercontent.com/RI-SE/curbpack/main/scripts/install.sh | sh
```

---

## Stranger 1

| Field | Run 1 | Run 2 |
|-------|-------|-------|
| Date | | |
| OS / arch | | |
| Install method | curl \| sh / install.ps1 / other | |
| Repo type (language, size) | | |
| `curbpack scan` exit code | | |
| Art 14 clock shown? | | |
| Exit 0 + `Scan complete` visible? | | |
| `Next:` / `Next (optional):` only if findings? (Y/N + note) | | |
| Blockers | | |
| stdout (paste or link) | | |

## Stranger 2

| Field | Run 1 | Run 2 |
|-------|-------|-------|
| Date | | |
| OS / arch | | |
| Install method | | |
| Repo type | | |
| Exit code | | |
| Art 14 clock? | | |
| Exit 0 + `Scan complete`? | | |
| `Next:` / `Next (optional):` only if findings? | | |
| Blockers | | |
| stdout | | |

## Stranger 3

| Field | Run 1 | Run 2 |
|-------|-------|-------|
| Date | | |
| OS / arch | | |
| Install method | | |
| Repo type | | |
| Exit code | | |
| Art 14 clock? | | |
| Exit 0 + `Scan complete`? | | |
| `Next:` / `Next (optional):` only if findings? | | |
| Blockers | | |
| stdout | | |

---

## Sign-off (human)

- [ ] 3 strangers × 2 runs complete
- [ ] Log linked from first-run feedback issues, Teams note, or ADOPTERS draft PR (Discussions not enabled — do not send testers there)
- [ ] Wave B `verify` spike scheduled per [software-design-document.md](../software-design-document.md)
