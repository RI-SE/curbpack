#!/usr/bin/env bash
# CI smoke: spaced-path demo + house-policy init must stay red
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BIN="${CURBPACK_BIN:-$ROOT/bin/curbpack}"
SPACE=$(mktemp -d "/tmp/curbpack smoke.XXXXXX")
"$BIN" demo --out "$SPACE" --keep
test -f "$SPACE/review-pack/buyer-onepager.html"
FIX=$(mktemp -d "/tmp/curb init.XXXXXX")
cd "$FIX"
git init -q
git config user.email "ci@curbpack.local"
git config user.name "CI"
git commit --allow-empty -m init -q
"$BIN" init --packs house-policy --yes
set +e
CHECK_OUT=$("$BIN" check 2>&1)
CHECK_CODE=$?
set -e
test "$CHECK_CODE" -ne 0
printf '%s\n' "$CHECK_OUT" | grep -q 'HOUSE-ANTI-PLACEHOLDER'
printf '%s\n' "$CHECK_OUT" | grep -q 'scaffold body overlap'
REPAIR_OUT=$("$BIN" doctor --repair 2>&1)
echo "$REPAIR_OUT" | grep -Eqi 'repair:|Repair done|binary missing'
