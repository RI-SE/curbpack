# RISE tryout — product repo

Audience wrapper for RISE colleagues testing Curbpack on a repo they are building. **Commands and install pins live only in** [install.md](install.md) and [troubleshooting.md](troubleshooting.md) — do not copy alternate pins from this page.

Not conformity assessment. Not CE marking. Not a notified-body opinion.

## Path A — smoke (recommended)

1. Follow [install.md](install.md) **Ladder 0** (pinned release install).
2. `cd` into your **product git repository** (confirm the path).
3. Run `curbpack scan`.
4. Confirm write-free:

```bash
before="$(git status --porcelain)"
curbpack scan
after="$(git status --porcelain)"
test "$before" = "$after"
```

**Pass for this tryout:** scan exits 0, Art 14 clock / findings / `Next:` visible, working tree unchanged. Soft-exit diagnosis is not a gate pass — see [install.md](install.md) / README exit notes.

Stuck? [troubleshooting.md](troubleshooting.md). Optional sandbox without a product repo: `curbpack demo` (same install SoR).

## Path B — optional deepen

Only if you are willing to write local curbpack files into the product repo. Follow the product-repo ladder in [60-second-paths.md](60-second-paths.md) / [install.md](install.md) (`init` → `check`).

A red check result is a successful evaluation for this tryout. It identifies work for human review; it is not a successful gate result.

Skip pathway confirms, attest, and `./scripts/pilot-receipt.sh` unless you are in a guided workshop (receipt needs a curbpack checkout).

## Feedback (short)

| Field | Your note |
|-------|-----------|
| OS / arch | |
| Install method | |
| `curbpack version` | |
| Path A scan exit + write-free? | |
| Blocker (paste last lines) | |

## Related

- Recruit / pilot frame: [rise-pilot-offer.md](rise-pilot-offer.md)
- Stranger log (external): [stranger-validation-log.md](stranger-validation-log.md)
