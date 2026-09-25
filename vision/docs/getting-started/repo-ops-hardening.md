# Repo ops hardening

Operator runbook for [RI-SE/curbpack](https://github.com/RI-SE/curbpack).

## Source of truth

- **Repository:** `RI-SE/curbpack` — PR-only merge to `main`, protected checks.
- **Public site:** https://ri-se.github.io/curbpack/
- **Force-push:** never on `main`.

## Remotes (local clone)

| Remote | Repo | Use |
|--------|------|-----|
| `corp-origin` | RI-SE/curbpack | **Source of truth** — open product PRs here |
| `origin` | afelin/curbpack | Optional dev fork — downstream catch-up only |

Product work: branch → PR → merge on **RI-SE** only. After merge, optional afelin catch-up: `git fetch corp-origin && git merge corp-origin/main`.

Full policy: [fork policy](../internal/fork-policy.md).

## Daily loop

1. Feature branch → PR → CI green → merge on **RI-SE/curbpack**.
2. Confirm Pages deploy if site content changed.

## Deprecated

`./scripts/curb-sync.sh` and `mirror-drift` removed when RI-SE became canonical. Do not maintain a parallel afelin fork for public releases.

RISE is a **funder / applied-research supporter**, not a product certifier — [promotion firewall](../promotion-firewall.md).
