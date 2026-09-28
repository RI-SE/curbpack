#!/usr/bin/env bash
# CI smoke: scan read-only on uninitialized repo
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BIN="${CURBPACK_BIN:-$ROOT/bin/curbpack}"
SCAN=$(mktemp -d)
cd "$SCAN"
git init -q
git config user.email "ci@curbpack.local"
git config user.name "CI"
git commit --allow-empty -m init -q
OUT=$("$BIN" scan 2>&1)
printf '%s\n' "$OUT" | grep -q 'Art 14 reporting clock'
printf '%s\n' "$OUT" | grep -q 'Packs: cra-baseline'
printf '%s\n' "$OUT" | grep -q 'Read-only'
test -z "$(git status --porcelain)"
