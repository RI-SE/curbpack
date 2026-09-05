#!/bin/sh
# Fail-closed release smoke: isolated PATH install → version assert → scan honesty + porcelain.
# Usage:
#   CURBPACK_VERSION=v0.5.4 ./scripts/release-smoke-install-scan.sh   # before main bump
#   ./scripts/release-smoke-install-scan.sh                            # after main advertises
# Env:
#   CURBPACK_VERSION   optional pin (e.g. v0.5.4) while main still defaults older
#   CURBPACK_REPO      default RI-SE/curbpack
#   INSTALL_SCRIPT_URL override installer URL (default: main scripts/install.sh)
set -eu

REPO="${CURBPACK_REPO:-RI-SE/curbpack}"
SCRIPT_URL="${INSTALL_SCRIPT_URL:-https://raw.githubusercontent.com/${REPO}/main/scripts/install.sh}"
EXPECT_VERSION="${EXPECT_VERSION:-}"
if [ -n "${CURBPACK_VERSION:-}" ]; then
  # strip leading v for binary version string
  EXPECT_VERSION="${EXPECT_VERSION:-${CURBPACK_VERSION#v}}"
fi
EXPECT_VERSION="${EXPECT_VERSION:-0.5.4}"

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT
INSTALL_DIR="${WORKDIR}/bin"
mkdir -p "$INSTALL_DIR"
export CURBPACK_INSTALL_DIR="$INSTALL_DIR"
# Prefer isolated bin; do not inherit workspace curbpack
export PATH="${INSTALL_DIR}:/usr/bin:/bin:/usr/sbin:/sbin"

echo "== release-smoke-install-scan =="
echo "REPO=${REPO}"
echo "SCRIPT_URL=${SCRIPT_URL}"
echo "CURBPACK_VERSION=${CURBPACK_VERSION:-<manifest default>}"
echo "EXPECT_VERSION=${EXPECT_VERSION}"
echo "INSTALL_DIR=${INSTALL_DIR}"
echo

curl -fsSL "$SCRIPT_URL" | sh

BIN="${INSTALL_DIR}/curbpack"
if [ ! -x "$BIN" ]; then
  echo "FAIL: binary missing at ${BIN}" >&2
  exit 1
fi

GOT=$("$BIN" version 2>&1)
echo "curbpack version → ${GOT}"
if [ "$GOT" != "curbpack ${EXPECT_VERSION}" ]; then
  echo "FAIL: want exact version curbpack ${EXPECT_VERSION}, got: ${GOT}" >&2
  exit 1
fi

REPO_DIR="${WORKDIR}/scan-repo"
mkdir -p "$REPO_DIR"
git -C "$REPO_DIR" init -q
git -C "$REPO_DIR" config user.email "smoke@curbpack.local"
git -C "$REPO_DIR" config user.name "smoke"
echo "# smoke" >"${REPO_DIR}/README.md"
git -C "$REPO_DIR" add README.md
git -C "$REPO_DIR" commit -qm "smoke"

SCAN_OUT="${WORKDIR}/scan.out"
set +e
(cd "$REPO_DIR" && "$BIN" scan >"$SCAN_OUT" 2>&1)
SCAN_EC=$?
set -e
echo "---- scan stdout (exit ${SCAN_EC}) ----"
cat "$SCAN_OUT"
echo "---- end scan ----"

if [ "$SCAN_EC" -ne 0 ]; then
  echo "FAIL: scan exit ${SCAN_EC} (want 0)" >&2
  exit 1
fi

need() {
  if ! grep -F -q "$1" "$SCAN_OUT"; then
    echo "FAIL: scan missing: $1" >&2
    exit 1
  fi
}

need "Exit 0 means diagnosis finished"
need "Exit 0: diagnosis finished"
need "Scan complete — repository unchanged."

# Next (optional): only when findings remain — smoke repo almost always has findings
if grep -F -q "No open gate findings" "$SCAN_OUT"; then
  if grep -E -q 'Next \(optional\):|^Next:' "$SCAN_OUT"; then
    echo "FAIL: Next line present on all-green scan" >&2
    exit 1
  fi
else
  need "Next (optional):"
fi

PORC=$(git -C "$REPO_DIR" status --porcelain)
if [ -n "$PORC" ]; then
  echo "FAIL: porcelain not empty after scan:" >&2
  echo "$PORC" >&2
  exit 1
fi

echo
echo "PASS: version=${EXPECT_VERSION} scan honesty + porcelain empty"
echo "Windows install.ps1: best-effort / not run on this host (record if unavailable)."
