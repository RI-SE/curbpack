#!/usr/bin/env bash
# cite-check wrapper — RAGChecker-lite groundedness against research-packet.json.
# Preserves the Go CLI exit code (1 on refuse). Never changes curbpack check pass/fail.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${CURBPACK_BIN:-$ROOT/bin/curbpack}"
if [[ ! -x "$BIN" ]]; then
  (cd "$ROOT" && go build -o "$BIN" ./cmd/curbpack)
fi

if [[ $# -lt 1 ]]; then
  echo "usage: scripts/cite-check.sh <draft.md> [more drafts…]" >&2
  exit 2
fi

fail=0
for f in "$@"; do
  "$BIN" research --cite-check "$f"
  ec=$?
  if [[ $ec -ne 0 ]]; then
    fail=$ec
  fi
done
exit "$fail"
