#!/usr/bin/env bash
# Recorded tutor dogfood: red → explain-packet → airlock → recheck still red → heal → green.
# Chat/tutor step is MANUAL — this script stops with a clear handoff and never greenlights from the packet.
#
# Usage (from repo root):
#   ./scripts/dogfood-explain-recheck.sh
#   CYBERREADY_BIN=./bin/cyberready ./scripts/dogfood-explain-recheck.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BIN="${CYBERREADY_BIN:-}"
if [[ -z "$BIN" ]]; then
  mkdir -p "$ROOT/bin"
  go build -o "$ROOT/bin/cyberready" ./cmd/cyberready
  BIN="$ROOT/bin/cyberready"
fi
if [[ ! -x "$BIN" ]]; then
  echo "dogfood-explain-recheck: CYBERREADY_BIN not executable: $BIN" >&2
  exit 1
fi

WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/cr-explain-dogfood.XXXXXX")"
cleanup() { rm -rf "$WORKDIR"; }
trap cleanup EXIT

echo "== dogfood-explain-recheck =="
echo "bin=$BIN"
echo "work=$WORKDIR"

# 1) Red fixture (house-policy missing SECURITY.md)
git -C "$WORKDIR" init -q
git -C "$WORKDIR" config user.email "dogfood@example.com"
git -C "$WORKDIR" config user.name "dogfood"
printf '# fixture\n' >"$WORKDIR/README.md"
git -C "$WORKDIR" add README.md
git -C "$WORKDIR" commit -qm "init"
(
  cd "$WORKDIR"
  "$BIN" init --bare --packs house-policy >/dev/null
)
# Force red: house-policy requires SECURITY.md (same shape as contract writeMinimalHouseFail).
rm -f "$WORKDIR/SECURITY.md"

set +e
(
  cd "$WORKDIR"
  "$BIN" check >/dev/null 2>&1
)
CHECK_RED=$?
set -e
if [[ "$CHECK_RED" -eq 0 ]]; then
  echo "FAIL: expected red check on incomplete house-policy fixture" >&2
  (cd "$WORKDIR" && "$BIN" check) || true
  exit 1
fi
echo "PASS  1 check red (exit=$CHECK_RED)"

# 2) Export explain-packet + airlock
(
  cd "$WORKDIR"
  "$BIN" export --explain-packet >/dev/null
)
PKT="$WORKDIR/.github/cyberready/cache/explain-packet.json"
test -f "$PKT"
if ! grep -q '<untrusted_metadata>' "$PKT"; then
  echo "FAIL: missing untrusted_metadata wrapper" >&2
  exit 1
fi
if grep -E '/Users/|/home/' "$PKT" >/dev/null; then
  echo "FAIL: absolute home path leaked into packet" >&2
  exit 1
fi
if grep -E 'BEGIN .*PRIVATE KEY' "$PKT" >/dev/null; then
  echo "FAIL: PEM leaked into packet" >&2
  exit 1
fi
echo "PASS  2 export airlocked packet → $PKT"

# 3) Contract unit gate (refuse PEM/home + must recheck)
(
  cd "$ROOT"
  go test ./internal/contract/ -run 'TestExplainPacketCorewardConsumer|TestCorewardRefusePacket' -count=1
) >/dev/null
echo "PASS  3 contract consumer + refuse PEM/home"

# 4) Sock explain_packet + validate_delta (still red)
SOCK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/cr-sock.XXXXXX")"
SOCK="$SOCK_DIR/cyberready.sock"
"$BIN" sock --path "$SOCK" --repo "$WORKDIR" >/tmp/cr-sock-dogfood.log 2>&1 &
SOCK_PID=$!
sock_cleanup() {
  kill "$SOCK_PID" 2>/dev/null || true
  wait "$SOCK_PID" 2>/dev/null || true
  rm -rf "$SOCK_DIR"
}
trap 'sock_cleanup; cleanup' EXIT

for _ in $(seq 1 50); do
  [[ -S "$SOCK" ]] && break
  sleep 0.05
done
if [[ ! -S "$SOCK" ]]; then
  echo "FAIL: sock did not appear at $SOCK" >&2
  cat /tmp/cr-sock-dogfood.log >&2 || true
  exit 1
fi

python3 - "$SOCK" <<'PY'
import json, socket, sys
path = sys.argv[1]

def roundtrip(op):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(10)
    s.connect(path)
    s.sendall((json.dumps({"op": op}) + "\n").encode())
    data = b""
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        data += chunk
        try:
            return json.loads(data.decode())
        except json.JSONDecodeError:
            continue
    raise SystemExit(f"no json for {op}: {data!r}")

ep = roundtrip("explain_packet")
assert ep.get("ok") is True, ep
pkt = ep.get("explain_packet")
assert isinstance(pkt, dict), pkt
body = pkt.get("untrusted_metadata") or ""
assert "<untrusted_metadata>" in body and "</untrusted_metadata>" in body, body[:200]
assert "/Users/" not in body and "/home/" not in body
vd = roundtrip("validate_delta")
assert vd.get("ok") is not True, vd
print("sock_ok")
PY
echo "PASS  4 sock explain_packet + validate_delta still red"

# 5) MANUAL handoff — chat must not claim fixed
cat <<EOF

--- CHAT HANDOFF (manual) ---
Packet: $PKT
Sock:   $SOCK  (CYBERREADY_SOCK=$SOCK)
Rules:  summarize only; never attest; never claim fixed from the packet.
Next:   apply a fix in the editor, then re-run validate_delta / check.
This script continues with heal → green without generative chat.
-----------------------------

EOF

# 6) Heal → green (match contract writeGoodHouse fixture)
mkdir -p "$WORKDIR/.well-known"
cat >"$WORKDIR/.well-known/security.txt" <<'EOF'
Contact: mailto:a@b.c
Expires: 2027-01-01T00:00:00.000Z
Preferred-Languages: en
EOF
# shellcheck disable=SC2005
printf '%s\n' "$(cat <<'EOF'
# Security Policy

## Reporting

Report vulnerabilities to security@example.com with reproduction steps.

## Supported Versions

We support the latest major release with security patches for twelve months.

## Disclosure

Coordinated disclosure within 90 days after fix availability.
EOF
)$(python3 -c 'print("word "*40)')" >"$WORKDIR/SECURITY.md"
(
  cd "$WORKDIR"
  "$BIN" check --heal >/dev/null 2>&1 || true
)
set +e
(
  cd "$WORKDIR"
  "$BIN" check >/dev/null 2>&1
)
CHECK_GREEN=$?
set -e
if [[ "$CHECK_GREEN" -ne 0 ]]; then
  echo "FAIL: expected green after fixture heal (exit=$CHECK_GREEN)" >&2
  (cd "$WORKDIR" && "$BIN" check) || true
  exit 1
fi
echo "PASS  6 check green after heal/fix (exit=0)"

# 7) Stale packet still must not authorize "fixed"
(
  cd "$ROOT"
  go test ./internal/contract/ -run TestExplainPacketCorewardConsumer -count=1
) >/dev/null
echo "PASS  7 stale packet never greenlights (contract)"

echo
echo "dogfood-explain-recheck: OK (chat step was manual handoff above)"
echo "Artifacts: $PKT (copied under workdir; cleaned on exit — re-run to regenerate)"
echo "Unit shortcut: go test ./internal/contract/ -run TestExplainPacketCorewardConsumer -count=1"
echo "Sock IPC:     go test ./internal/sock/ -run TestExplainPacketIPC -count=1"
