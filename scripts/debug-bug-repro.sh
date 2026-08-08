#!/usr/bin/env bash
# Repro harness for debug session 561228 — writes NDJSON via instrumented binary + shell probes.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export ROOT
export CYBERREADY_DEBUG_RUN="${CYBERREADY_DEBUG_RUN:-pre-fix}"
BIN="$ROOT/bin/cyberready-debug"
LOG="$ROOT/.cursor/debug-561228.log"

cd "$ROOT"
go build -o "$BIN" ./cmd/cyberready

# --- H1: Action prefers workspace bin without checksum ---
# #region agent log
python3 - <<'PY'
import json, time, os
root = os.environ["ROOT"]
path = f"{root}/.cursor/debug-561228.log"
# Simulate action.yml resolve preference
ws_bin = f"{root}/bin/cyberready"
prefers = os.path.isfile(ws_bin) and os.access(ws_bin, os.X_OK)
# Read action.yml snippet evidence
action = open(f"{root}/action.yml").read()
hijack = "if [ -x ./bin/cyberready ]; then" in action and "source=workspace-bin" in action
with open(path, "a") as f:
    f.write(json.dumps({
        "sessionId": "561228", "hypothesisId": "H1", "location": "scripts/debug-bug-repro.sh:H1",
        "message": "action workspace-bin preference", "timestamp": int(time.time()*1000),
        "runId": os.environ.get("CYBERREADY_DEBUG_RUN",""),
        "data": {"workspaceBinExists": prefers, "actionPrefersWorkspaceBin": hijack,
                 "checksumSkippedOnWorkspaceBranch": hijack}
    }) + "\n")
print("H1 logged", "hijack=", hijack)
PY
# #endregion

# --- H2: DiffOnly false-green for missing SECURITY.md ---
DIR=$(mktemp -d)
cd "$DIR"
git init -q
git config user.email "dbg@cyberready.local"
git config user.name "Debug"
git commit --allow-empty -m init -q
printf '# Project\n' > README.md
mkdir -p .well-known
printf 'Contact: mailto:a@b.c\nExpires: 2027-01-01T00:00:00.000Z\nPreferred-Languages: en\n' > .well-known/security.txt
# No SECURITY.md
git add -A && git commit -m base -q
echo 'touch' >> README.md   # only README dirty
set +e
"$BIN" check --packs house-policy --diff >/tmp/h2-diff.out 2>&1
DIFF_EC=$?
"$BIN" check --packs house-policy >/tmp/h2-full.out 2>&1
FULL_EC=$?
set -e
# #region agent log
python3 - <<PY
import json, time, os
path = "${ROOT}/.cursor/debug-561228.log"
with open(path, "a") as f:
    f.write(json.dumps({
        "sessionId": "561228", "hypothesisId": "H2", "location": "scripts/debug-bug-repro.sh:H2",
        "message": "diff vs full exit codes", "timestamp": int(time.time()*1000),
        "runId": os.environ.get("CYBERREADY_DEBUG_RUN",""),
        "data": {"diffExit": ${DIFF_EC}, "fullExit": ${FULL_EC},
                 "falseGreen": ${DIFF_EC} == 0 and ${FULL_EC} != 0}
    }) + "\n")
print("H2 diff=", ${DIFF_EC}, "full=", ${FULL_EC})
PY
# #endregion

# --- H3: heal + diff false-green ---
DIR3=$(mktemp -d)
cd "$DIR3"
git init -q
git config user.email "dbg@cyberready.local"
git config user.name "Debug"
git commit --allow-empty -m init -q
printf '# Project\n' > README.md
mkdir -p .well-known
# short security.txt (fails min) + missing SECURITY.md
printf 'Contact: x\n' > .well-known/security.txt
git add -A && git commit -m base -q
# touch only something so diff is active; heal will create SECURITY.md
echo x >> README.md
set +e
"$BIN" check --packs house-policy --diff --heal >/tmp/h3-heal.out 2>&1
HEAL_EC=$?
"$BIN" check --packs house-policy >/tmp/h3-full.out 2>&1
H3FULL=$?
set -e
# #region agent log
python3 - <<PY
import json, time, os
path = "${ROOT}/.cursor/debug-561228.log"
with open(path, "a") as f:
    f.write(json.dumps({
        "sessionId": "561228", "hypothesisId": "H3", "location": "scripts/debug-bug-repro.sh:H3",
        "message": "heal+diff vs full", "timestamp": int(time.time()*1000),
        "runId": os.environ.get("CYBERREADY_DEBUG_RUN",""),
        "data": {"healDiffExit": ${HEAL_EC}, "fullExit": ${H3FULL},
                 "falseGreen": ${HEAL_EC} == 0 and ${H3FULL} != 0,
                 "securityMdExists": os.path.isfile("SECURITY.md")}
    }) + "\n")
print("H3 heal+diff=", ${HEAL_EC}, "full=", ${H3FULL})
PY
# #endregion

# --- H5: ApplyStubs allows .git path ---
cd "$ROOT"
go test ./internal/formhints/ -run TestDebugGitWrite -count=1 -v 2>&1 | tee /tmp/h5.out || true

# --- H4: ssh-keygen argv (only if agent present) ---
if [ -n "${SSH_AUTH_SOCK:-}" ] && ssh-add -L >/dev/null 2>&1; then
  DIR4=$(mktemp -d)
  cd "$DIR4"
  git init -q
  git config user.email "dbg@cyberready.local"
  git config user.name "Debug"
  git commit --allow-empty -m init -q
  "$BIN" init --packs house-policy >/dev/null 2>&1 || true
  # fill stubs so check can pass-ish; attest still tries sign
  printf '# Security\n\n%s\n' "$(python3 -c 'print("word "*40)')" > SECURITY.md
  mkdir -p .well-known
  printf 'Contact: mailto:a@b.c\nExpires: 2027-01-01T00:00:00.000Z\nPreferred-Languages: en\n' > .well-known/security.txt
  git add -A && git commit -m filled -q || true
  "$BIN" attest --allow-dirty >/tmp/h4.out 2>&1 || true
  echo "H4 attest attempted (see NDJSON for argv)"
else
  python3 - <<PY
import json, time, os
path = "${ROOT}/.cursor/debug-561228.log"
with open(path, "a") as f:
    f.write(json.dumps({
        "sessionId": "561228", "hypothesisId": "H4", "location": "scripts/debug-bug-repro.sh:H4",
        "message": "SSH_AUTH_SOCK absent — argv bug still static-confirmed in code",
        "timestamp": int(time.time()*1000),
        "runId": os.environ.get("CYBERREADY_DEBUG_RUN",""),
        "data": {"agentPresent": False, "codeDashFIsPayload": True}
    }) + "\n")
print("H4 skipped runtime (no agent); code evidence logged")
PY
fi

# --- H6: note CI macOS LC_UUID from gh ---
python3 - <<PY
import json, time, os
path = "${ROOT}/.cursor/debug-561228.log"
with open(path, "a") as f:
    f.write(json.dumps({
        "sessionId": "561228", "hypothesisId": "H6", "location": "scripts/debug-bug-repro.sh:H6",
        "message": "CI macOS dyld LC_UUID abort (from gh run 31228295988)",
        "timestamp": int(time.time()*1000),
        "runId": os.environ.get("CYBERREADY_DEBUG_RUN",""),
        "data": {"packages": ["contract","packscmd","sock"], "error": "missing LC_UUID load command",
                 "goVersionCI": "1.22.x", "runner": "macos-latest"}
    }) + "\n")
print("H6 CI evidence logged")
PY

echo "=== REPRO DONE ==="
echo "Log: $LOG"
wc -l "$LOG" || true
