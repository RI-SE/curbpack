#!/bin/sh
# Curbpack one-click install — downloads a GitHub Release binary (no Go required).
# Usage: curl -fsSL https://raw.githubusercontent.com/afelin/curbpack/main/scripts/install.sh | sh
# Env: CURBPACK_VERSION (default: v0.5.0), CURBPACK_INSTALL_DIR (default: ~/.local/bin), GITHUB_TOKEN (optional)
# Legacy CYBERREADY_* env names are still read if CURBPACK_* is unset.
# Fail-closed: verifies asset against release checksums.txt (sha256).
set -eu

# Dual-read: CURBPACK_* preferred; CYBERREADY_* accepted during cutover.
REPO="${CURBPACK_REPO:-${CYBERREADY_REPO:-afelin/curbpack}}"
VERSION="${CURBPACK_VERSION:-${CYBERREADY_VERSION:-v0.5.0}}"
INSTALL_DIR="${CURBPACK_INSTALL_DIR:-${CYBERREADY_INSTALL_DIR:-${HOME}/.local/bin}}"

claim='Prepares evidence for human review — not a conformity assessment.'
echo "Curbpack installer"
echo "  ${claim}"
echo

os=$(uname -s | tr '[:upper:]' '[:lower:]')
arch=$(uname -m)
case "$os" in
  darwin|linux) ;;
  msys*|mingw*|cygwin*|windows*)
    echo "unsupported OS: Windows is not supported (need darwin or linux)" >&2
    echo "See README — Windows = documented unsupported." >&2
    exit 1
    ;;
  *)
    echo "unsupported OS: $os (need darwin or linux; Windows unsupported)" >&2
    exit 1
    ;;
esac
case "$arch" in
  x86_64|amd64) arch=amd64 ;;
  aarch64|arm64) arch=arm64 ;;
  *)
    echo "unsupported arch: $arch (need amd64 or arm64)" >&2
    exit 1
    ;;
esac

asset="curbpack_${os}_${arch}"
api="https://api.github.com/repos/${REPO}/releases"
auth_hdr=""
if [ -n "${GITHUB_TOKEN:-}" ]; then
  auth_hdr="Authorization: Bearer ${GITHUB_TOKEN}"
fi

gh_curl() {
  if [ -n "$auth_hdr" ]; then
    curl -fsSL -H "$auth_hdr" -H "Accept: application/vnd.github+json" "$@"
  else
    curl -fsSL -H "Accept: application/vnd.github+json" "$@"
  fi
}

if [ "$VERSION" = "latest" ]; then
  release_json=$(gh_curl "${api}/latest")
  url=$(printf '%s' "$release_json" | sed -n "s/.*\"browser_download_url\": \"\\([^\"]*${asset}[^\"]*\\)\".*/\\1/p" | head -n 1)
  checksums_url=$(printf '%s' "$release_json" | sed -n 's/.*"browser_download_url": "\([^"]*checksums\.txt\)".*/\1/p' | head -n 1)
  tag=$(printf '%s' "$release_json" | sed -n 's/.*"tag_name": "\([^"]*\)".*/\1/p' | head -n 1)
else
  tag="$VERSION"
  url="https://github.com/${REPO}/releases/download/${tag}/${asset}"
  checksums_url="https://github.com/${REPO}/releases/download/${tag}/checksums.txt"
fi

if [ -z "${url:-}" ]; then
  echo "could not resolve download URL for ${asset} (tag=${tag:-unknown})" >&2
  echo "Build from source: go install github.com/afelin/curbpack/cmd/curbpack@latest" >&2
  exit 1
fi

if [ -z "${checksums_url:-}" ]; then
  echo "checksums.txt URL missing — refusing install (fail closed)" >&2
  exit 1
fi

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
echo "Downloading ${tag:-latest} → ${asset}"
curl -fsSL -o "${tmpdir}/curbpack" "$url"
chmod +x "${tmpdir}/curbpack"

echo "Verifying checksums.txt"
curl -fsSL -o "${tmpdir}/checksums.txt" "$checksums_url"
expected=$(
  # sha256sum format: "<hash>  <filename>" or "<hash> *<filename>"
  grep -E "[ /]${asset}\$" "${tmpdir}/checksums.txt" | head -n 1 | awk '{print $1}'
)
if [ -z "${expected:-}" ]; then
  echo "no checksum entry for ${asset} in checksums.txt — refusing install" >&2
  exit 1
fi

if command -v sha256sum >/dev/null 2>&1; then
  actual=$(sha256sum "${tmpdir}/curbpack" | awk '{print $1}')
elif command -v shasum >/dev/null 2>&1; then
  actual=$(shasum -a 256 "${tmpdir}/curbpack" | awk '{print $1}')
else
  echo "neither sha256sum nor shasum found — refusing install" >&2
  exit 1
fi

if [ "$actual" != "$expected" ]; then
  echo "checksum mismatch for ${asset}" >&2
  echo "  expected: ${expected}" >&2
  echo "  actual:   ${actual}" >&2
  exit 1
fi
echo "Checksum OK (${actual})"

mkdir -p "$INSTALL_DIR"
mv "${tmpdir}/curbpack" "${INSTALL_DIR}/curbpack"
ln -sfn curbpack "${INSTALL_DIR}/curb"
echo "Installed: ${INSTALL_DIR}/curbpack"
echo "Alias:     ${INSTALL_DIR}/curb → curbpack"

case ":$PATH:" in
  *":${INSTALL_DIR}:"*) ;;
  *)
    echo
    echo "Add to PATH:"
    echo "  export PATH=\"${INSTALL_DIR}:\$PATH\""
    ;;
esac

echo
echo "Next (safe sandbox, never touches your product):"
echo "  curb doctor"
echo "  curb demo"
echo
echo "${claim}"
