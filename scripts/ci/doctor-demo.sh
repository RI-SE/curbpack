#!/usr/bin/env bash
# CI smoke: doctor + demo sandbox
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BIN="${CURBPACK_BIN:-$ROOT/bin/curbpack}"
"$BIN" doctor
DEMO=$(mktemp -d)
"$BIN" demo --out "$DEMO" --keep
test -f "$DEMO/review-pack/buyer-onepager.html"
test -f "$DEMO/.curbpack.json"
