#!/usr/bin/env bash
# cite-check wrapper — RAGChecker-lite groundedness against research-packet.json.
# Exit non-zero on refuse. Never changes cyberready check pass/fail.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${CYBERREADY_BIN:-$ROOT/bin/cyberready}"
if [[ ! -x "$BIN" ]]; then
  (cd "$ROOT" && go build -o "$BIN" ./cmd/cyberready)
fi

if [[ $# -lt 1 ]]; then
  echo "usage: scripts/cite-check.sh <draft.md> [more drafts…]" >&2
  exit 2
fi

fail=0
for f in "$@"; do
  if ! "$BIN" research --cite-check "$f"; then
    fail=1
  fi
done
exit "$fail"
