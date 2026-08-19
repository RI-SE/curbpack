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

## Protected main policy

For both repos (`afelin/curbpack`, `RI-SE/curbpack`):

- Require pull request before merging to `main`.
- Require status checks to pass before merge.
- Require branch to be up to date before merge.
- Dismiss stale approvals on new commits.
- Restrict direct pushes to `main`.
- Allow merge queue only if your team actively uses it.

## Merge strategy policy

To reduce history ambiguity:

- Prefer merge commits (default in this repo).
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
