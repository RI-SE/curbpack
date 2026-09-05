#!/usr/bin/env bash
# Reproduce: hostile CURBPACK_VERSION can path-traverse release download URLs
# while keeping binary + checksums.txt self-consistent (same attacker path).
# Installers must refuse before any download.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
INSTALL_SH="$ROOT/scripts/install.sh"
INSTALL_PS1="$ROOT/scripts/install.ps1"

fail() { echo "FAIL: $*" >&2; exit 1; }

# Prove the URL construction hazard (why the guard exists).
REPO='RI-SE/curbpack'
ASSET='curbpack_darwin_amd64'
hostile='../../../evil/malware/releases/download/v9.9.9'
url="https://github.com/${REPO}/releases/download/${hostile}/${ASSET}"
case "$url" in
  *'/evil/malware/releases/download/'*) ;;
  *) fail "expected traversal demo URL to escape curbpack release path; got: $url" ;;
esac

FAKEBIN=$(mktemp -d)
trap 'rm -rf "$FAKEBIN"' EXIT
SENTINEL="$FAKEBIN/curl-called"
mkdir -p "$FAKEBIN/home" "$FAKEBIN/install"

cat >"$FAKEBIN/curl" <<EOF
#!/bin/sh
touch "$SENTINEL"
echo "unexpected curl invocation: \$*" >&2
exit 99
EOF
cat >"$FAKEBIN/uname" <<'EOF'
#!/bin/sh
[ "$1" = "-s" ] && { echo Darwin; exit 0; }
[ "$1" = "-m" ] && { echo arm64; exit 0; }
echo "unexpected uname: $*" >&2
exit 1
EOF
chmod +x "$FAKEBIN/curl" "$FAKEBIN/uname"

run_install() {
  rm -f "$SENTINEL"
  env -i \
    PATH="$FAKEBIN:/usr/bin:/bin:/usr/sbin:/sbin" \
    HOME="$FAKEBIN/home" \
    CURBPACK_VERSION="$1" \
    CURBPACK_INSTALL_DIR="$FAKEBIN/install" \
    sh "$INSTALL_SH" 2>&1
}

# Hostile / traversal / injection must refuse before any download.
for bad in \
  '../../../evil/malware/releases/download/v9.9.9' \
  'v0.5.4/../../evil' \
  'v0.5.4;curl evil' \
  '--help' \
  'main' \
  'latest/../v0.5.4' \
  'v0.5.4%2F..%2Fevil'
do
  set +e
  out=$(run_install "$bad")
  code=$?
  set -e
  [[ "$code" -ne 0 ]] || fail "install.sh accepted hostile version: $bad"
  [[ ! -f "$SENTINEL" ]] || fail "install.sh reached curl for hostile version: $bad"
  printf '%s' "$out" | grep -qiE 'invalid|refusing|version' || \
    fail "install.sh hostile refusal message missing for: $bad (out=$out)"
done

# Valid tags and latest must pass the version gate (then attempt download → curl sentinel).
for good in 'latest' 'v0.5.4' 'v1.2.3' 'v0.5.5-rc.1'; do
  set +e
  run_install "$good" >/dev/null
  code=$?
  set -e
  [[ -f "$SENTINEL" ]] || fail "install.sh should accept version gate for $good then call curl (exit=$code)"
done

# PowerShell installer must embed an explicit version/tag validation guard.
grep -qE 'CURBPACK_VERSION|\$Version' "$INSTALL_PS1" || fail "install.ps1 missing version input"
if ! grep -Eq 'invalid (install )?version|refusing.*version|version tag such as' "$INSTALL_PS1"; then
  fail "install.ps1 lacks CURBPACK_VERSION / tag validation guard"
fi
# Same tag grammar as scripts/verify-release-ref.sh (plus literal latest in installers).
if ! grep -Fq 'v[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$' "$INSTALL_SH"; then
  fail "install.sh must use release tag grammar matching verify-release-ref.sh"
fi
if ! grep -Fq 'v[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$' "$INSTALL_PS1"; then
  fail "install.ps1 must use release tag grammar matching verify-release-ref.sh"
fi

echo 'install-version tests passed'
