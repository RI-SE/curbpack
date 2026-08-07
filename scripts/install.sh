#!/bin/sh
# CyberReady+ one-click install — downloads a GitHub Release binary (no Go required).
# Usage: curl -fsSL https://raw.githubusercontent.com/afelin/cyberready/main/scripts/install.sh | sh
# Env: CYBERREADY_VERSION (default: latest), CYBERREADY_INSTALL_DIR (default: ~/.local/bin), GITHUB_TOKEN (optional)
set -eu

REPO="${CYBERREADY_REPO:-afelin/cyberready}"
VERSION="${CYBERREADY_VERSION:-latest}"
INSTALL_DIR="${CYBERREADY_INSTALL_DIR:-${HOME}/.local/bin}"

claim='Prepares evidence for human review — not a conformity assessment.'
echo "CyberReady+ installer"
echo "  ${claim}"
echo

os=$(uname -s | tr '[:upper:]' '[:lower:]')
arch=$(uname -m)
case "$os" in
  darwin|linux) ;;
  *)
    echo "unsupported OS: $os (need darwin or linux)" >&2
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

asset="cyberready_${os}_${arch}"
api="https://api.github.com/repos/${REPO}/releases"
auth_hdr=""
if [ -n "${GITHUB_TOKEN:-}" ]; then
  auth_hdr="Authorization: Bearer ${GITHUB_TOKEN}"
fi

if [ "$VERSION" = "latest" ]; then
  url=$(
    if [ -n "$auth_hdr" ]; then
      curl -fsSL -H "$auth_hdr" -H "Accept: application/vnd.github+json" "${api}/latest"
    else
      curl -fsSL -H "Accept: application/vnd.github+json" "${api}/latest"
    fi | sed -n "s/.*\"browser_download_url\": \"\\([^\"]*${asset}[^\"]*\\)\".*/\\1/p" | head -n 1
  )
  tag=$(
    if [ -n "$auth_hdr" ]; then
      curl -fsSL -H "$auth_hdr" -H "Accept: application/vnd.github+json" "${api}/latest"
    else
      curl -fsSL -H "Accept: application/vnd.github+json" "${api}/latest"
    fi | sed -n 's/.*"tag_name": "\([^"]*\)".*/\1/p' | head -n 1
  )
else
  tag="$VERSION"
  url="https://github.com/${REPO}/releases/download/${tag}/${asset}"
fi

if [ -z "${url:-}" ]; then
  echo "could not resolve download URL for ${asset} (tag=${tag:-unknown})" >&2
  echo "Build from source: go install github.com/afelin/cyberready/cmd/cyberready@latest" >&2
  exit 1
fi

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
echo "Downloading ${tag:-latest} → ${asset}"
curl -fsSL -o "${tmpdir}/cyberready" "$url"
chmod +x "${tmpdir}/cyberready"

mkdir -p "$INSTALL_DIR"
mv "${tmpdir}/cyberready" "${INSTALL_DIR}/cyberready"
echo "Installed: ${INSTALL_DIR}/cyberready"

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
echo "  cyberready doctor"
echo "  cyberready demo"
echo
echo "${claim}"
