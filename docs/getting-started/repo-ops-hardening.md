# Repo ops hardening

Operator runbook for [RI-SE/curbpack](https://github.com/RI-SE/curbpack).

## Source of truth

- **Repository:** `RI-SE/curbpack` — PR-only merge to `main`, protected checks.
- **Public site:** https://ri-se.github.io/curbpack/
- **Force-push:** never on `main`.

## Daily loop

1. Feature branch → PR → CI green → merge.
2. Confirm Pages deploy if site content changed.

## Deprecated

`./scripts/curb-sync.sh` and `mirror-drift` removed when RI-SE became canonical. Do not maintain a parallel afelin fork for public releases.

RISE is a **funder / applied-research supporter**, not a product certifier — [promotion firewall](../promotion-firewall.md).
