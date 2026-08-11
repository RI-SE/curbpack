#!/usr/bin/env bash
# Sync afelin (origin) and RI-SE (corp-origin) main — merge only.
# NEVER use --force or --force-with-lease (force is forbidden).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

paused() {
  echo "Paused: $*"
  exit 2
}

need_remote() {
  local name="$1"
  if ! git remote get-url "$name" >/dev/null 2>&1; then
    paused "Remote '$name' is missing — ask Cursor to add origin (afelin) and corp-origin (RI-SE)"
  fi
}

need_remote origin
need_remote corp-origin

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  paused "Not a git repository"
fi

# Refuse dirty worktree (uncommitted changes) — plain English.
if [[ -n "$(git status --porcelain)" ]]; then
  paused "Save or discard chat changes first — ask Cursor to commit or discard"
fi

if ! git fetch origin; then
  paused "Could not fetch origin — check GitHub login for afelin/curbpack"
fi
if ! git fetch corp-origin; then
  paused "Could not fetch corp-origin — authorize GitHub SSO for RI-SE/curbpack, then try again"
fi

if ! git show-ref --verify --quiet refs/remotes/origin/main; then
  paused "origin/main not found after fetch"
fi
if ! git show-ref --verify --quiet refs/remotes/corp-origin/main; then
  paused "corp-origin/main not found after fetch"
fi

if ! git checkout main; then
  paused "Could not checkout main — finish or stash other branch work first"
fi

# Merge only — never --force / --force-with-lease (force is forbidden).
if ! git merge --no-edit origin/main; then
  paused "Merge conflict with origin/main — say: Resolve the sync conflict for me"
fi
if ! git merge --no-edit corp-origin/main; then
  paused "Merge conflict with corp-origin/main — say: Resolve the sync conflict for me"
fi

if ! git push origin main; then
  paused "Could not push origin main — check GitHub login for afelin (never force-push)"
fi
if ! git push corp-origin main; then
  paused "Could not push corp-origin main — authorize GitHub SSO for RI-SE (never force-push)"
fi

shortsha="$(git rev-parse --short HEAD)"
echo "Both remotes match ($shortsha)"
exit 0
