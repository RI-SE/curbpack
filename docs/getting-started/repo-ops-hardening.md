# Repo ops hardening (dual-remote)

This runbook keeps `afelin/curbpack` and `RI-SE/curbpack` clean and aligned while preserving a low-cognitive-load workflow.

## Daily operator loop

1. Work only on a feature branch.
2. Open PR and wait for required checks to pass.
3. Merge PR (never direct-push `main`).
4. Run `./scripts/curb-sync.sh`.
5. Confirm both remotes are identical on `main`.

```bash
git rev-parse origin/main
git rev-parse corp-origin/main
```

The two SHAs must match.

## Protected main policy (source + mirror)

Use asymmetric protection to avoid endless SHA drift:

- **Source of truth (`afelin/curbpack`)**
  - Protect `main` with required checks.
  - Require PR-based merge into `main`.
  - Restrict direct pushes to `main`.
- **Mirror (`RI-SE/curbpack`)**
  - Keep `main` in mirror mode for deterministic sync (`./scripts/curb-sync.sh`).
  - Do not require PR-only merge on mirror `main`, or sync will create merge-commit loops.
  - Never force-push; mirror only receives normal sync pushes from source `main`.

## Merge strategy policy

To reduce history ambiguity:

- Prefer merge commits on the source repo (default here).
- Keep branch auto-delete enabled after merge.
- Do not force-push to `main`.

## Branch hygiene

Weekly cleanup:

```bash
git fetch --all --prune
git branch -r
```

Delete remote branches only when they are fully merged into `main`.

## Auth hygiene

- Keep one source of truth for GitHub auth in Cursor (plugin auth).
- Avoid persistent `GITHUB_TOKEN` shell exports.
- Rotate PAT yearly (or immediately if auth behaves unexpectedly).

## CI sanity checks

Before declaring repo healthy:

- `gh pr list --state open` is expected (or empty if all merged).
- Required checks are green on merged PRs.
- `./scripts/curb-sync.sh` exits cleanly.
- `origin/main` equals `corp-origin/main`.

## Incident playbook (if sync pauses)

`curb-sync.sh` pause messages are authoritative:

- auth error -> re-auth GitHub / SSO for RI-SE
- merge conflict -> resolve on branch, re-run sync
- protected branch rejection -> finish PR path and re-run sync

Never use force push to bypass these pauses.
