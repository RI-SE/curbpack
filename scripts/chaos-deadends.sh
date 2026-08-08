#!/usr/bin/env bash
# Chaos dead-ends: clear exit, no panic. Nightly / maintainer smoke.
# Usage: ./scripts/chaos-deadends.sh [path-to-cyberready-binary]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${1:-$ROOT/bin/cyberready}"
if [[ ! -x "$BIN" ]]; then
  (cd "$ROOT" && go build -o bin/cyberready ./cmd/cyberready)
  BIN="$ROOT/bin/cyberready"
fi
if [[ "$BIN" != /* ]]; then
  BIN="$(cd "$(dirname "$BIN")" && pwd)/$(basename "$BIN")"
fi

pass=0
fail=0
ok() { echo "OK   $1"; pass=$((pass + 1)); }
bad() { echo "FAIL $1"; fail=$((fail + 1)); }

echo "== chaos dead-ends =="

# Broken git: empty .git dir
BROKEN=$(mktemp -d)
mkdir -p "$BROKEN/.git"
pushd "$BROKEN" >/dev/null
set +e
"$BIN" check --json >/tmp/cyberready-chaos.out 2>/tmp/cyberready-chaos.err
code=$?
set -e
popd >/dev/null
if [[ "$code" -eq 0 ]] || grep -qiE 'panic:|runtime error:' /tmp/cyberready-chaos.out /tmp/cyberready-chaos.err; then
  bad "broken-git-check"
else
  ok "broken-git-check (exit=$code)"
fi

# Readonly cache dir
RO=$(mktemp -d)
pushd "$RO" >/dev/null
git init -q
git config user.email "chaos@cyberready.local"
git config user.name "Chaos"
git commit --allow-empty -m init -q
"$BIN" init --packs house-policy >/dev/null
CACHE="$RO/.github/cyberready/cache"
chmod a-w "$CACHE" || true
set +e
"$BIN" check >/tmp/cyberready-chaos.out 2>/tmp/cyberready-chaos.err
code=$?
set -e
chmod u+w "$CACHE" 2>/dev/null || true
popd >/dev/null
if grep -qiE 'panic:|runtime error:' /tmp/cyberready-chaos.out /tmp/cyberready-chaos.err; then
  bad "readonly-cache (panic)"
else
  ok "readonly-cache (exit=$code, no panic)"
fi

# Concurrent attest (two processes) — must not panic
FIX=$(mktemp -d)
pushd "$FIX" >/dev/null
git init -q
git config user.email "chaos@cyberready.local"
git config user.name "Chaos"
git commit --allow-empty -m init -q
"$BIN" init --packs house-policy >/dev/null
if [[ -d "$ROOT/testdata/demo-app" ]]; then
  cp -R "$ROOT/testdata/demo-app/." "$FIX/"
fi
git add -A && git -c commit.gpgsign=false commit --no-verify -m "fixture" -q || true
"$BIN" prepare-release >/dev/null 2>&1 || true
set +e
"$BIN" attest --allow-dirty >/tmp/cyberready-chaos-a.out 2>/tmp/cyberready-chaos-a.err &
pid1=$!
"$BIN" attest --allow-dirty >/tmp/cyberready-chaos-b.out 2>/tmp/cyberready-chaos-b.err &
pid2=$!
wait "$pid1" || true
wait "$pid2" || true
set -e
popd >/dev/null
if grep -qiE 'panic:|runtime error:' /tmp/cyberready-chaos-a.err /tmp/cyberready-chaos-b.err /tmp/cyberready-chaos-a.out /tmp/cyberready-chaos-b.out 2>/dev/null; then
  bad "concurrent-attest (panic)"
else
  ok "concurrent-attest (no panic)"
fi

# Kill mid prepare-release
FIX2=$(mktemp -d)
pushd "$FIX2" >/dev/null
git init -q
git config user.email "chaos@cyberready.local"
git config user.name "Chaos"
git commit --allow-empty -m init -q
"$BIN" init --packs house-policy >/dev/null
set +e
"$BIN" prepare-release >/tmp/cyberready-chaos.out 2>/tmp/cyberready-chaos.err &
pid=$!
sleep 0.05
kill -9 "$pid" 2>/dev/null || true
wait "$pid" 2>/dev/null || true
set -e
popd >/dev/null
ok "kill-mid-prepare-release (no hang)"

# Demo refuses product cwd
pushd "$ROOT" >/dev/null
set +e
"$BIN" demo --out "$ROOT" >/tmp/cyberready-chaos.out 2>/tmp/cyberready-chaos.err
code=$?
set -e
popd >/dev/null
if [[ "$code" -eq 0 ]] || grep -qiE 'panic:|runtime error:' /tmp/cyberready-chaos.out /tmp/cyberready-chaos.err; then
  bad "demo-cwd-jail"
else
  ok "demo-cwd-jail (exit=$code)"
fi

echo
echo "chaos summary: pass=$pass fail=$fail"
if [[ "$fail" -gt 0 ]]; then
  exit 1
fi
exit 0
