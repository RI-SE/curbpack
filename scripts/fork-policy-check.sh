#!/usr/bin/env bash
# Fail closed on parity/mirror branches and afelin→RI-SE doc poisoning.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
branch_lc="$(printf '%s' "$branch" | tr '[:upper:]' '[:lower:]')"
msg="$(git log -1 --format=%B 2>/dev/null || echo "")"
msg_lc="$(printf '%s' "$msg" | tr '[:upper:]' '[:lower:]')"

# 1) Forbidden branch name patterns
if [[ "$branch" == sync/* ]] || \
   [[ "$branch_lc" == *parity* ]] || \
   [[ "$branch_lc" == *mirror* ]]; then
  echo "fork-policy: forbidden branch name: $branch" >&2
  exit 1
fi

# Merge-base vs main (CI / local)
base=""
if git rev-parse --verify origin/main >/dev/null 2>&1; then
  base="$(git merge-base origin/main HEAD 2>/dev/null || true)"
elif git rev-parse --verify main >/dev/null 2>&1; then
  base="$(git merge-base main HEAD 2>/dev/null || true)"
fi

if [[ -n "$base" ]]; then
  diff="$(git diff "$base"..HEAD 2>/dev/null || true)"

  # 2) Private-fork launch header swap onto RI-SE
  if printf '%s' "$diff" | grep -q 'Private-fork launch checklist'; then
    echo "fork-policy: diff introduces private-fork launch header (forbidden on RI-SE)" >&2
    exit 1
  fi

  # 3) Bulk + parity/mirror keywords
  file_count="$(git diff --name-only "$base"..HEAD 2>/dev/null | wc -l | tr -d ' ')"
  combined="${branch_lc} ${msg_lc}"
  if [[ "$file_count" -gt 80 ]] && printf '%s' "$combined" | grep -qiE 'parity|mirror|sync both|identical remotes'; then
    echo "fork-policy: bulk change ($file_count files) with parity/mirror keywords" >&2
    exit 1
  fi
fi

exit 0
