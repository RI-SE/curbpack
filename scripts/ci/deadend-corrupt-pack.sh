#!/usr/bin/env bash
# CI: corrupt pack env must fail closed
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BIN="${CURBPACK_BIN:-$ROOT/bin/curbpack}"
BAD=$(mktemp -d)
mkdir -p "$BAD/broken"
echo '{not json' > "$BAD/broken/pack.json"
FIX=$(mktemp -d)
cd "$FIX"
git init -q
git config user.email "ci@curbpack.local"
git config user.name "CI"
git commit --allow-empty -m init -q
set +e
CURBPACK_PACKS_DIR="$BAD" "$BIN" init --packs broken --yes
code=$?
set -e
test "$code" -ne 0
