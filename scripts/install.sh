#!/bin/sh
# Curbpack one-click install — downloads a GitHub Release binary (no Go required).
# Preferred: curl -fsSL https://raw.githubusercontent.com/RI-SE/curbpack/main/scripts/install.sh | sh
# (installs smoke-verified binary from release gate / manifest default)
# Env: CURBPACK_VERSION (default: from install-manifest.json / v0.5.3), CURBPACK_INSTALL_DIR (default: ~/.local/bin), GITHUB_TOKEN (optional)
# Legacy CYBERREADY_* env names are still read if CURBPACK_* is unset.
# Fail-closed: verifies asset against release checksums.txt (sha256).
# Atomic: download → checksum → temp → replace. Writes install-marker.json.
set -eu

# Piped `curl | sh` keeps baked MANIFEST_DEFAULT; only read adjacent manifest when $0 is a real file.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" 2>/dev/null && pwd || true)
MANIFEST_DEFAULT="v0.5.3"
if [ -f "$0" ] && [ -n "${SCRIPT_DIR:-}" ] && [ -f "${SCRIPT_DIR}/install-manifest.json" ]; then
  MANIFEST_DEFAULT=$(sed -n 's/.*"default_version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "${SCRIPT_DIR}/install-manifest.json" | head -n 1)
  [ -n "$MANIFEST_DEFAULT" ] || MANIFEST_DEFAULT="v0.5.3"
fi

# Dual-read: CURBPACK_* preferred; CYBERREADY_* accepted during cutover.
REPO="${CURBPACK_REPO:-${CYBERREADY_REPO:-RI-SE/curbpack}}"
VERSION="${CURBPACK_VERSION:-${CYBERREADY_VERSION:-$MANIFEST_DEFAULT}}"
INSTALL_DIR="${CURBPACK_INSTALL_DIR:-${CYBERREADY_INSTALL_DIR:-${HOME}/.local/bin}}"

claim='Prepares evidence for human review — not a conformity assessment.'
echo "Curbpack installer"
echo "  ${claim}"
echo

if [ "$REPO" != "RI-SE/curbpack" ]; then
  echo "WARNING: CURBPACK_REPO=${REPO} — canonical stranger installs use RI-SE/curbpack only." >&2
  echo "Do not use afelin/curbpack (private fork; release assets often 404)." >&2
  if [ "${CURBPACK_REPO_I_UNDERSTAND:-}" != "1" ]; then
    echo "Refusing non-canonical repo. Unset CURBPACK_REPO, or set CURBPACK_REPO_I_UNDERSTAND=1 to override." >&2
    echo "Prefer: https://github.com/RI-SE/curbpack/releases" >&2
    exit 1
  fi
  echo "Proceeding with override (CURBPACK_REPO_I_UNDERSTAND=1)." >&2
  echo
fi

os=$(uname -s | tr '[:upper:]' '[:lower:]')
arch=$(uname -m)
case "$os" in
  darwin|linux) ;;
  msys*|mingw*|cygwin*)
    echo "Use install.ps1 on Windows (PowerShell):" >&2
    echo "  irm https://raw.githubusercontent.com/RI-SE/curbpack/v0.5.3/scripts/install.ps1 | iex" >&2
    exit 1
    ;;
  *)
    echo "unsupported OS: $os (need darwin or linux; Windows → install.ps1)" >&2
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
  echo "Prefer the binary installer from RI-SE releases:" >&2
  echo "  https://github.com/RI-SE/curbpack/releases" >&2
  echo "  docs: https://github.com/RI-SE/curbpack/blob/main/docs/getting-started/install.md" >&2
  echo "Go module path remains github.com/afelin/curbpack until wave-2 migration;" >&2
  echo "with that development repo private, strangers should use binary installers only." >&2
  echo "(Do not treat go install …/RI-SE/curbpack as a working fallback — module path differs.)" >&2
  echo "Do not point stranger installs at afelin/curbpack (private; assets may 404)." >&2
  exit 1
fi

if [ -z "${checksums_url:-}" ]; then
  echo "checksums.txt URL missing — refusing install (fail closed)" >&2
  echo "Prefer RI-SE releases: https://github.com/RI-SE/curbpack/releases" >&2
  echo "Do not use afelin/curbpack for stranger installs (private fork; assets may 404)." >&2
  exit 1
fi

echo "REPO=${REPO}"
echo "VERSION=${tag:-$VERSION}"
echo "ASSET=${asset}"
echo "URL=${url}"
echo "INSTALL_DIR=${INSTALL_DIR}"
case ":$PATH:" in
  *":${INSTALL_DIR}:"*) echo "PATH: INSTALL_DIR already on PATH" ;;
  *) echo "PATH: INSTALL_DIR not on PATH (export hint after install if needed)" ;;
esac
echo

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
echo "Downloading ${tag:-latest} → ${asset}"
if ! curl -fsSL -o "${tmpdir}/curbpack" "$url"; then
  echo "Download failed (often HTTP 404) for:" >&2
  echo "  ${url}" >&2
  echo "Prefer RI-SE releases: https://github.com/RI-SE/curbpack/releases" >&2
  echo "  docs: https://github.com/RI-SE/curbpack/blob/main/docs/getting-started/install.md" >&2
  echo "Do not use afelin/curbpack for stranger installs (private fork; assets may 404)." >&2
  exit 1
fi
chmod +x "${tmpdir}/curbpack"

echo "Verifying checksums.txt"
if ! curl -fsSL -o "${tmpdir}/checksums.txt" "$checksums_url"; then
  echo "checksums.txt download failed (often HTTP 404) for:" >&2
  echo "  ${checksums_url}" >&2
  echo "Prefer RI-SE releases: https://github.com/RI-SE/curbpack/releases" >&2
  echo "Do not use afelin/curbpack for stranger installs (private fork; assets may 404)." >&2
  exit 1
fi
expected=$(
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
# Atomic replace: write .new then mv; remove leftover .new on failure
dest="${INSTALL_DIR}/curbpack"
tmp_dest="${dest}.new"
cp "${tmpdir}/curbpack" "$tmp_dest"
chmod +x "$tmp_dest"
if ! mv -f "$tmp_dest" "$dest"; then
  rm -f "$tmp_dest"
  echo "failed to replace ${dest}" >&2
  exit 1
fi
ln -sfn curbpack "${INSTALL_DIR}/curb"
echo "Installed: ${dest}"
echo "Alias:     ${INSTALL_DIR}/curb → curbpack"

# Install marker (Unix)
marker_dir="${XDG_DATA_HOME:-${HOME}/.local/share}/curbpack"
mkdir -p "$marker_dir"
marker="${marker_dir}/install-marker.json"
ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u)
cat > "$marker" <<EOF
{
  "schema": "curbpack-install-marker:1",
  "version": "${tag:-$VERSION}",
  "install_dir": "${INSTALL_DIR}",
  "binary": "${dest}",
  "installed_at": "${ts}",
  "goos": "${os}"
}
EOF
echo "Marker:    ${marker}"

case ":$PATH:" in
  *":${INSTALL_DIR}:"*) ;;
  *)
    echo
    echo "Add to PATH — open a new terminal after adding this line to your shell profile, or run now:"
    echo "  export PATH=\"${INSTALL_DIR}:\$PATH\""
    case "$(basename "${SHELL:-}")" in
      zsh) echo "  (zsh: put the export in ~/.zprofile)" ;;
      bash) echo "  (bash: put the export in ~/.bashrc)" ;;
    esac
    ;;
esac

echo
echo "Next:"
echo
echo "  cd /path/to/your/git/repo"
echo "  curbpack scan"
echo
echo "Not ready to use a product repository?"
echo "  curbpack demo"
echo
echo "Optional: curbpack doctor"
echo "After OS update / PATH loss: curbpack doctor --repair"
echo
echo "${claim}"
