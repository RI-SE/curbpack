#!/usr/bin/env bash
# Chaos dead-ends: clear exit, no panic. Nightly / maintainer smoke.
# Usage: ./scripts/chaos-deadends.sh [path-to-curbpack-binary]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${1:-$ROOT/bin/curbpack}"
if [[ ! -x "$BIN" ]]; then
  (cd "$ROOT" && go build -o bin/curbpack ./cmd/curbpack)
  BIN="$ROOT/bin/curbpack"
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
"$BIN" check --json >/tmp/curbpack-chaos.out 2>/tmp/curbpack-chaos.err
code=$?
set -e
popd >/dev/null
if [[ "$code" -eq 0 ]] || grep -qiE 'panic:|runtime error:' /tmp/curbpack-chaos.out /tmp/curbpack-chaos.err; then
  bad "broken-git-check"
else
  ok "broken-git-check (exit=$code)"
fi

# Readonly cache dir
RO=$(mktemp -d)
pushd "$RO" >/dev/null
git init -q
git config user.email "chaos@curbpack.local"
git config user.name "Chaos"
git commit --allow-empty -m init -q
"$BIN" init --packs house-policy >/dev/null
CACHE="$RO/.github/curbpack/cache"
chmod a-w "$CACHE" || true
set +e
"$BIN" check >/tmp/curbpack-chaos.out 2>/tmp/curbpack-chaos.err
code=$?
set -e
chmod u+w "$CACHE" 2>/dev/null || true
popd >/dev/null
if grep -qiE 'panic:|runtime error:' /tmp/curbpack-chaos.out /tmp/curbpack-chaos.err; then
  bad "readonly-cache (panic)"
else
  ok "readonly-cache (exit=$code, no panic)"
fi

# Concurrent attest (two processes) — must not panic
FIX=$(mktemp -d)
pushd "$FIX" >/dev/null
git init -q
git config user.email "chaos@curbpack.local"
git config user.name "Chaos"
git commit --allow-empty -m init -q
"$BIN" init --packs house-policy >/dev/null
if [[ -d "$ROOT/testdata/demo-app" ]]; then
  cp -R "$ROOT/testdata/demo-app/." "$FIX/"
fi
git add -A && git -c commit.gpgsign=false commit --no-verify -m "fixture" -q || true
"$BIN" prepare-release >/dev/null 2>&1 || true
set +e
"$BIN" attest --allow-dirty >/tmp/curbpack-chaos-a.out 2>/tmp/curbpack-chaos-a.err &
pid1=$!
"$BIN" attest --allow-dirty >/tmp/curbpack-chaos-b.out 2>/tmp/curbpack-chaos-b.err &
pid2=$!
wait "$pid1" || true
wait "$pid2" || true
set -e
popd >/dev/null
if grep -qiE 'panic:|runtime error:' /tmp/curbpack-chaos-a.err /tmp/curbpack-chaos-b.err /tmp/curbpack-chaos-a.out /tmp/curbpack-chaos-b.out 2>/dev/null; then
  bad "concurrent-attest (panic)"
else
  ok "concurrent-attest (no panic)"
fi

# Kill mid prepare-release
FIX2=$(mktemp -d)
pushd "$FIX2" >/dev/null
git init -q
git config user.email "chaos@curbpack.local"
git config user.name "Chaos"
git commit --allow-empty -m init -q
"$BIN" init --packs house-policy >/dev/null
set +e
"$BIN" prepare-release >/tmp/curbpack-chaos.out 2>/tmp/curbpack-chaos.err &
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
"$BIN" demo --out "$ROOT" >/tmp/curbpack-chaos.out 2>/tmp/curbpack-chaos.err
code=$?
set -e
popd >/dev/null
if [[ "$code" -eq 0 ]] || grep -qiE 'panic:|runtime error:' /tmp/curbpack-chaos.out /tmp/curbpack-chaos.err; then
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
