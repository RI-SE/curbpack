#!/usr/bin/env bash
# Reproduce Action resolve defects, then prove the fix against the real resolver
# (scripts/action-resolve-bin.sh) wired from action.yml — not a stub:
#  1) consumer go.mod matching curbpack module must NOT trigger go build
#  2) inputs / generated values reach shell/JS via env — no ${{ inputs.* }} in run/script
#  3) version / boolean grammar validated as data before use
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
ACTION_YML="$ROOT/action.yml"
RESOLVER="$ROOT/scripts/action-resolve-bin.sh"

fail() { echo "FAIL: $*" >&2; exit 1; }

[[ -f "$ACTION_YML" ]] || fail "missing action.yml"
[[ -f "$RESOLVER" ]] || fail "missing scripts/action-resolve-bin.sh"

# action.yml must delegate resolve to the shared resolver script.
grep -q 'scripts/action-resolve-bin.sh' "$ACTION_YML" || \
  fail "action.yml Resolve step must invoke scripts/action-resolve-bin.sh"

# --- Static: no direct input interpolation into executable shell/JS bodies ---
python3 - "$ACTION_YML" <<'PY' || fail "action.yml still interpolates inputs into run/script bodies"
import re, sys
from pathlib import Path
text = Path(sys.argv[1]).read_text(encoding="utf-8")
lines = text.splitlines()
in_exec = False
exec_indent = None
bad = []
for i, line in enumerate(lines, 1):
    if re.match(r"^(\s+)(run|script):\s*\|?\s*$", line):
        in_exec = True
        exec_indent = len(re.match(r"^(\s+)", line).group(1))
        continue
    if in_exec:
        if line.strip() == "":
            continue
        m = re.match(r"^(\s*)", line)
        ind = len(m.group(1)) if m else 0
        if ind <= exec_indent:
            in_exec = False
            exec_indent = None
        elif re.match(r"^\s+(name|id|shell|working-directory|if|uses|env|with|continue-on-error):", line):
            in_exec = False
            exec_indent = None
        if in_exec and "${{ inputs." in line:
            bad.append(f"L{i}: {line.strip()}")
        if in_exec and re.search(r"\$\{\{\s*steps\.[^}]+\.outputs\.", line):
            bad.append(f"L{i}: {line.strip()}")
if bad:
    print("direct interpolation in run/script bodies:", file=sys.stderr)
    for b in bad:
        print(f"  {b}", file=sys.stderr)
    sys.exit(1)
print("static: no inputs/step-outputs interpolation in run/script bodies")
PY

# Resolver must not select source build from go.mod module path alone.
if grep -q "module github.com/afelin/curbpack" "$RESOLVER"; then
  fail "resolver must not key source build on go.mod module path"
fi
grep -q 'RI-SE/curbpack' "$RESOLVER" || fail "resolver missing RI-SE/curbpack dogfood repository gate"
grep -q 'CURBPACK_ACTION_ALLOW_SOURCE_BUILD' "$RESOLVER" || \
  fail "resolver missing CURBPACK_ACTION_ALLOW_SOURCE_BUILD gate"
grep -q 'checksums.txt' "$RESOLVER" || fail "resolver missing checksums.txt verify"
grep -q 'source=release' "$RESOLVER" || fail "resolver missing source=release"
grep -Eq 'v\[0-9\]\+\\\.\[0-9\]\+\\\.\[0-9\]\+' "$RESOLVER" || \
  fail "resolver missing release-tag grammar validation"
grep -q 'v0.5.2' "$RESOLVER" || fail "default pin v0.5.2 missing from resolver"

# Check / sticky comment env-pass contracts in action.yml
grep -q 'CURBPACK_ACTION_DIFF' "$ACTION_YML" || fail "missing CURBPACK_ACTION_DIFF"
grep -q 'CURBPACK_ACTION_HEAL' "$ACTION_YML" || fail "missing CURBPACK_ACTION_HEAL"
grep -q 'CURBPACK_ACTION_PACKS' "$ACTION_YML" || fail "missing CURBPACK_ACTION_PACKS"
grep -q 'process.env.CURBPACK_ACTION_WORKING_DIRECTORY' "$ACTION_YML" || \
  fail "JS sticky comment must read working directory from process.env"
grep -q 'process.env.CURBPACK_ACTION_SCORE' "$ACTION_YML" || \
  fail "JS sticky comment must read score from process.env"
grep -q 'process.env.CURBPACK_ACTION_PASSED' "$ACTION_YML" || \
  fail "JS sticky comment must read passed from process.env"
grep -q 'invalid inputs.diff' "$ACTION_YML" || fail "diff boolean data validation missing"
grep -q 'invalid inputs.heal' "$ACTION_YML" || fail "heal boolean data validation missing"

FAKE=$(mktemp -d)
trap 'rm -rf "$FAKE"' EXIT
mkdir -p "$FAKE/bin" "$FAKE/action/scripts" "$FAKE/work" "$FAKE/home"
SENTINEL_GO="$FAKE/go-called"
SENTINEL_CURL="$FAKE/curl-called"
OUT="$FAKE/github_output"

# Consumer workspace: matching module path (the defect trigger).
cat >"$FAKE/work/go.mod" <<'EOF'
module github.com/afelin/curbpack

go 1.23
EOF
mkdir -p "$FAKE/work/cmd/curbpack"
cat >"$FAKE/work/cmd/curbpack/main.go" <<'EOF'
package main
func main() {}
EOF

# Wire the real resolver the same way action.yml does.
cp "$RESOLVER" "$FAKE/action/scripts/action-resolve-bin.sh"
chmod +x "$FAKE/action/scripts/action-resolve-bin.sh"

cat >"$FAKE/bin/go" <<EOF
#!/bin/sh
touch "$SENTINEL_GO"
echo "unexpected go invocation: \$*" >&2
exit 99
EOF
cat >"$FAKE/bin/curl" <<EOF
#!/bin/sh
touch "$SENTINEL_CURL"
echo "curl stub: \$*" >&2
exit 22
EOF
cat >"$FAKE/bin/uname" <<'EOF'
#!/bin/sh
[ "$1" = "-s" ] && { echo Linux; exit 0; }
[ "$1" = "-m" ] && { echo x86_64; exit 0; }
echo "unexpected uname: $*" >&2
exit 1
EOF
chmod +x "$FAKE/bin/go" "$FAKE/bin/curl" "$FAKE/bin/uname"

run_resolve() {
  local repo="$1"
  local allow="$2"
  local ver="$3"
  rm -f "$SENTINEL_GO" "$SENTINEL_CURL" "$OUT"
  : >"$OUT"
  (
    cd "$FAKE/work"
    env -i \
      PATH="$FAKE/bin:/usr/bin:/bin:/usr/sbin:/sbin" \
      HOME="$FAKE/home" \
      GITHUB_OUTPUT="$OUT" \
      GITHUB_ACTION_PATH="$FAKE/action" \
      GITHUB_REPOSITORY="$repo" \
      CURBPACK_ACTION_VERSION="$ver" \
      CURBPACK_ACTION_ALLOW_SOURCE_BUILD="$allow" \
      bash "$FAKE/action/scripts/action-resolve-bin.sh"
  )
}

# --- Consumer: matching go.mod must NOT invoke go; must attempt release download ---
set +e
out=$(run_resolve "acme/product" "" "" 2>&1)
code=$?
set -e
[[ ! -f "$SENTINEL_GO" ]] || fail "consumer go.mod match still invoked go build (out=$out)"
[[ -f "$SENTINEL_CURL" ]] || fail "consumer path should download pinned release (curl); out=$out code=$code"
[[ "$code" -ne 0 ]] || fail "expected download failure from curl stub"

# Consumer + allow flag still must NOT source-build (repository gate).
set +e
out=$(run_resolve "acme/product" "1" "" 2>&1)
code=$?
set -e
[[ ! -f "$SENTINEL_GO" ]] || fail "non-RI-SE repo with ALLOW_SOURCE_BUILD still invoked go (out=$out)"
[[ -f "$SENTINEL_CURL" ]] || fail "non-RI-SE allow flag should still download; out=$out"

# Hostile version must refuse before curl.
set +e
out=$(run_resolve "acme/product" "" '../../../evil/malware/releases/download/v9.9.9' 2>&1)
code=$?
set -e
[[ "$code" -ne 0 ]] || fail "hostile version accepted"
[[ ! -f "$SENTINEL_CURL" ]] || fail "hostile version reached curl"
[[ ! -f "$SENTINEL_GO" ]] || fail "hostile version reached go"
printf '%s' "$out" | grep -qiE 'invalid|refusing|version' || \
  fail "hostile version refusal message missing (out=$out)"

# RI-SE dogfood allow path may invoke go (prove gate works positively).
set +e
out=$(run_resolve "RI-SE/curbpack" "1" "" 2>&1)
code=$?
set -e
[[ -f "$SENTINEL_GO" ]] || fail "RI-SE dogfood allow should invoke go build (out=$out code=$code)"
[[ ! -f "$SENTINEL_CURL" ]] || fail "RI-SE dogfood source path must not curl"

echo "action-resolve tests passed"
