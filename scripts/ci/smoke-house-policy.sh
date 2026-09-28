#!/usr/bin/env bash
# CI smoke: house-policy hooks/skill/ide + attest
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BIN="${CURBPACK_BIN:-$ROOT/bin/curbpack}"
FIX=$(mktemp -d)
cd "$FIX"
git init -q
git config user.email "ci@curbpack.local"
git config user.name "CI"
git commit --allow-empty -m init -q
"$BIN" init --packs house-policy --hooks --skill --ide --yes
test -x .git/hooks/pre-commit
grep -q 'curbpack check' .git/hooks/pre-commit
! grep -q -- '--heal' .git/hooks/pre-commit
grep -aF 'refusing commit' .git/hooks/pre-commit
! grep -q $'\r' .git/hooks/pre-commit
test -f .cursor/skills/curbpack/SKILL.md
test -f .vscode/tasks.json
set +e
CHECK_OUT=$("$BIN" check 2>&1)
CHECK_CODE=$?
set -e
test "$CHECK_CODE" -ne 0
printf '%s\n' "$CHECK_OUT" | grep -q 'HOUSE-ANTI-PLACEHOLDER'
printf '%s\n' "$CHECK_OUT" | grep -q 'scaffold body overlap'
set +e
"$BIN"
BARE_CODE=$?
set -e
test "$BARE_CODE" -ne 0
"$BIN" check --form-hints || true
echo '{"name":"demo","dependencies":{"left-pad":"1.3.0"}}' > package.json
"$BIN" prepare-release --allow-failing-gates
test -f .github/curbpack/evidence/sbom.cdx.json
python3 - <<'PY'
import json
d=json.load(open(".github/curbpack/evidence/sbom.cdx.json"))
assert d["bomFormat"]=="CycloneDX" and d["specVersion"]=="1.5"
v=json.load(open(".github/curbpack/evidence/vex-pending.json"))
assert v["status"]=="draft_pending_attest"
PY
git add -A && git -c commit.gpgsign=false commit --no-verify -m "evidence" -q
"$BIN" attest --allow-dirty
test -f .github/curbpack/evidence/hpurl-pointer.json
python3 - <<'PY'
import json
p=json.load(open(".github/curbpack/evidence/hpurl-pointer.json"))
assert p.get("state_hash") and p["state_hash"] in p.get("hpurl","")
PY
grep -aF 'refusing commit' .git/hooks/pre-commit
H1=$(python3 -c 'import json;print(json.load(open(".github/curbpack/evidence/hpurl-pointer.json"))["state_hash"])')
"$BIN" attest --allow-dirty >/dev/null
H2=$(python3 -c 'import json;print(json.load(open(".github/curbpack/evidence/hpurl-pointer.json"))["state_hash"])')
test "$H1" = "$H2"
