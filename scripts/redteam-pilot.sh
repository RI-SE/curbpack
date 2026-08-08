#!/usr/bin/env bash
# Pilot-prod adversarial scoreboard — the three invariants in docs/security-model.md.
# Exit non-zero if any case fails.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BIN="${CYBERREADY_BIN:-$ROOT/bin/cyberready}"
if [[ ! -x "$BIN" ]]; then
  go build -o "$BIN" ./cmd/cyberready
fi

PASS=0
FAIL=0

ok() { echo "  PASS  $*"; PASS=$((PASS + 1)); }
bad() { echo "  FAIL  $*"; FAIL=$((FAIL + 1)); }

echo "== redteam-pilot (pilot-prod contract) =="

# --- 1) Fake ./bin/cyberready must not be preferred by Action resolve ---
if grep -q 'Never prefer consumer \./bin/cyberready' action.yml && \
   ! grep -E '^\s*if \[ -x (\./)?bin/cyberready' action.yml && \
   grep -q 'source=built\|source=release' action.yml; then
  ok "1 Action resolve does not prefer workspace ./bin/cyberready"
else
  bad "1 Action resolve must not prefer unverified ./bin/cyberready"
fi

# --- 2) Missing SECURITY.md + dirty README — check --diff fails ---
TMP2="$(mktemp -d)"
cleanup() { rm -rf "$TMP2"; }
trap cleanup EXIT
set +e
(
  set -e
  cd "$TMP2"
  git init -q
  git config user.email "redteam@cyberready.local"
  git config user.name "Redteam"
  git commit --allow-empty -m init -q
  "$BIN" init --packs house-policy >/dev/null
  rm -f SECURITY.md
  git add -A && git -c commit.gpgsign=false commit --no-verify -m stubs -q || true
  echo "# dirty" >> README.md
  "$BIN" check --diff >/dev/null 2>&1
)
diff_code=$?
set -e
if [[ "$diff_code" -ne 0 ]]; then
  ok "2 check --diff fails when SECURITY.md missing (dirty README only)"
else
  bad "2 check --diff false-greened missing SECURITY.md"
fi

# --- 3) ApplyStubs .git/hooks/pre-commit refused ---
if go test ./internal/formhints/ -run TestApplyStubsRefusesDotGit -count=1 >/dev/null 2>&1; then
  ok "3 ApplyStubs refuses .git/hooks/pre-commit"
else
  bad "3 ApplyStubs .git jail regression"
fi

# --- 4) Pack path ../outside refused ---
if go test ./internal/packs/ -run 'TestValidatePackRefusesPathEscape|TestValidatePackSchema' -count=1 >/dev/null 2>&1; then
  ok "4 pack path ../outside refused at ValidatePack"
else
  bad "4 pack path escape not refused"
fi

# --- 5) Claim-safety still green ---
if ./scripts/claim-safety.sh >/dev/null 2>&1; then
  ok "5 claim-safety green"
else
  bad "5 claim-safety failed"
fi

echo ""
echo "redteam-pilot: $PASS passed, $FAIL failed"
if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
exit 0
