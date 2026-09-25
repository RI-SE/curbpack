# Fork policy (maintainers)

Operator-facing rules for **RI-SE/curbpack** (public) and **afelin/curbpack** (optional private dev fork).

## Source of truth

| Repo | Role |
|------|------|
| **RI-SE/curbpack** | Public SoR — releases, site, stranger install URLs, kill-test cohort |
| **afelin/curbpack** | Optional dev sandbox — **downstream only** |

## Allowed

- Feature branch → PR → merge on **RI-SE/curbpack**.
- After RI-SE merge: on an afelin clone, one-way catch-up:

  ```bash
  git fetch corp-origin && git merge corp-origin/main
  ```

- `./scripts/curbpack-ship.sh preflight <pr#>` assumes product PRs target **RI-SE/curbpack**.

## Forbidden (agents and humans)

- Full-tree “parity”, “mirror”, or “sync both remotes” PRs (either direction).
- Copying afelin maintainer docs onto RI-SE (e.g. *Private-fork launch checklist* header in `docs/internal/launch-readiness.md`).
- Dual merge trains for the same feature unless a human explicitly wants a **private-only** experiment first.
- Chasing identical commit SHAs across repos.
- Re-enabling dual-remote sync scripts (`curb-sync.sh` stays exit-2 stub).

## Fork-specific files (may differ by design)

Never force-identical wholesale merges for:

| File | afelin | RI-SE |
|------|--------|-------|
| `docs/internal/launch-readiness.md` | Private-fork framing | Public Apache-2.0 framing |

## CI guard

`scripts/fork-policy-check.sh` runs in `redteam-pilot` (case 12). It fails on forbidden branch names, private-fork header swaps, and bulk parity-style copies.

## See also

- [Repo ops hardening](../getting-started/repo-ops-hardening.md)
- [Sync both remotes (deprecated)](../getting-started/sync-both-remotes.md)
