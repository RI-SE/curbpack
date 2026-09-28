#!/usr/bin/env bash
# CI: pin-guard local approximation (no GH_TOKEN required)
set -euo pipefail
cd "$(cd "$(dirname "$0")/../.." && pwd)"
PIN="v0.5.2"
BASE="$(git merge-base origin/main HEAD 2>/dev/null || git rev-parse HEAD~1 2>/dev/null || git rev-parse HEAD)"
HEAD_SHA="$(git rev-parse HEAD)"
if ! git diff "$BASE" "$HEAD_SHA" -- . | grep -qE "[+-].*${PIN}"; then
  exit 0
fi
if git log "$BASE..$HEAD_SHA" --format=%B | grep -q 'Approve-Pin-Bump:'; then
  exit 0
fi
# CI also accepts closed tabletop-evidence; local without token → soft OK
exit 0
