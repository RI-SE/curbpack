#!/usr/bin/env bash
# Resolve curbpack binary for the composite Action (checksum-verified pin).
# Invoked from action.yml with inputs passed only via environment variables.
#
# Env:
#   CURBPACK_ACTION_VERSION — optional release tag; empty/latest → v0.5.2
#   CURBPACK_ACTION_ALLOW_SOURCE_BUILD — "1" enables dogfood source build ONLY when
#     GITHUB_REPOSITORY is RI-SE/curbpack (never for consumer go.mod match alone)
#   GITHUB_ACTION_PATH — Action checkout path (set by GitHub)
#   GITHUB_OUTPUT — step outputs file (set by GitHub)
#   GITHUB_REPOSITORY — owner/repo (set by GitHub)
set -euo pipefail

OS=$(uname -s | tr '[:upper:]' '[:lower:]')
# Action runners = Linux/macOS only. Local Windows CLI is separate (install.ps1).
case "$OS" in
  mingw*|msys*|cygwin*|windows*)
    echo "::error::Curbpack Action supports Linux/macOS runners only. On Windows use the local CLI (install.ps1), not this Action."
    echo "Curbpack Action supports Linux/macOS runners only. On Windows use the local CLI (install.ps1), not this Action." >&2
    exit 1
    ;;
esac
ARCH=$(uname -m)
case "$ARCH" in
  x86_64|amd64) ARCH=amd64 ;;
  aarch64|arm64) ARCH=arm64 ;;
esac
ASSET="curbpack_${OS}_${ARCH}"

ACTION_PATH="${GITHUB_ACTION_PATH:?GITHUB_ACTION_PATH required}"
DEST="${CURBPACK_ACTION_DEST:-$ACTION_PATH/curbpack}"
VER="${CURBPACK_ACTION_VERSION:-}"
REPO="${GITHUB_REPOSITORY:-}"

# Never prefer consumer ./bin/curbpack — that skips checksum verification and
# lets a PR ship a fake-green binary. Consumer Action path always downloads a
# pinned release and verifies sha256 against checksums.txt (fail-closed).
# Dogfood source build is explicit RI-SE workflow only (env + repository).
allow_source=0
if [ "${CURBPACK_ACTION_ALLOW_SOURCE_BUILD:-}" = "1" ] && [ "$REPO" = "RI-SE/curbpack" ]; then
  allow_source=1
fi

if [ "$allow_source" = "1" ] && command -v go >/dev/null 2>&1 && [ -f go.mod ]; then
  go build -o "$DEST" ./cmd/curbpack
  echo "source=built" >> "${GITHUB_OUTPUT:?}"
  echo "path=$DEST" >> "$GITHUB_OUTPUT"
  exit 0
fi

# Empty version → pin v0.5.2 (never silent floating latest).
if [ -z "$VER" ] || [ "$VER" = "latest" ]; then
  if [ "$VER" = "latest" ]; then
    echo "inputs.version=latest is deprecated; downloading v0.5.2 instead" >&2
  fi
  VER="v0.5.2"
fi

# Fail closed on hostile/traversal version strings before URL construction.
# Grammar matches scripts/verify-release-ref.sh (Action has no "latest" after pin).
if ! printf '%s' "$VER" | grep -Eq '^v[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$'; then
  echo "invalid Action version: ${VER}" >&2
  echo "Use a release tag such as v0.5.2 (empty defaults to v0.5.2)." >&2
  exit 1
fi

URL="https://github.com/RI-SE/curbpack/releases/download/${VER}/${ASSET}"
CHECKSUMS_URL="https://github.com/RI-SE/curbpack/releases/download/${VER}/checksums.txt"

# Network install: retry once (max 2 attempts) — never retry gate logic.
set +e
curl -fsSL -o "$DEST" "$URL"
code=$?
if [ "$code" -ne 0 ]; then
  sleep 2
  curl -fsSL -o "$DEST" "$URL"
  code=$?
fi
set -e
if [ "$code" -ne 0 ]; then
  echo "download failed for ${ASSET}" >&2
  exit 1
fi

# Fail-closed sha256 verify (parity with scripts/install.sh)
curl -fsSL -o "${DEST}.checksums.txt" "$CHECKSUMS_URL"
expected=$(grep -E "[ /]${ASSET}\$" "${DEST}.checksums.txt" | head -n 1 | awk '{print $1}')
if [ -z "${expected:-}" ]; then
  echo "no checksum entry for ${ASSET} in checksums.txt — refusing install" >&2
  exit 1
fi
if command -v sha256sum >/dev/null 2>&1; then
  actual=$(sha256sum "$DEST" | awk '{print $1}')
elif command -v shasum >/dev/null 2>&1; then
  actual=$(shasum -a 256 "$DEST" | awk '{print $1}')
else
  echo "neither sha256sum nor shasum found — refusing install" >&2
  exit 1
fi
if [ "$actual" != "$expected" ]; then
  echo "checksum mismatch for ${ASSET}" >&2
  echo "  expected: ${expected}" >&2
  echo "  actual:   ${actual}" >&2
  exit 1
fi
echo "Checksum OK (${actual})"
chmod +x "$DEST"
rm -f "${DEST}.checksums.txt"
echo "source=release" >> "${GITHUB_OUTPUT:?}"
echo "path=$DEST" >> "$GITHUB_OUTPUT"
