#!/bin/sh
# Shared implementation; package_installers.py adds the fixed program selection.
set -eu

install_programs() {
    case "$(uname -s)/$(uname -m)" in
        Darwin/arm64|Darwin/aarch64) host=macos-arm64 ;;
        Linux/x86_64|Linux/amd64)
            host=linux-x64
            if ! getconf GNU_LIBC_VERSION 2>/dev/null | awk '
                $1 == "glibc" { split($2, version, "."); supported = version[1] > 2 || (version[1] == 2 && version[2] >= 35) }
                END { exit !supported }
            '; then
                echo 'Linux installation requires glibc 2.35 or newer (Ubuntu 22.04 or newer); musl/Alpine is not supported.' >&2
                exit 1
            fi
            ;;
        *) echo 'Use macOS ARM64 or Linux x64; on Windows use the PowerShell installer.' >&2; exit 1 ;;
    esac
    version=${CURBPACK_VERSION:-latest}
    if [ "$version" = latest ]; then
        release_url=$(curl -fsSL https://github.com/RI-SE/curbpack/releases/latest -o /dev/null -w '%{url_effective}')
        case "$release_url" in
            https://github.com/RI-SE/curbpack/releases/tag/*) version=${release_url##*/} ;;
            *) echo 'Could not resolve the latest release.' >&2; exit 1 ;;
        esac
    fi
    case "$version" in
        ''|*[!a-zA-Z0-9._-]*) echo 'Invalid release tag.' >&2; exit 1 ;;
    esac
    install_dir=${CURBPACK_INSTALL_DIR:-"$HOME/.local/bin"}
    base="https://github.com/RI-SE/curbpack/releases/download/$version"
    tmpdir=$(mktemp -d)
    staging=''
    trap 'rm -rf "$tmpdir"; if [ -n "$staging" ]; then rm -rf "$staging"; fi' 0
    trap 'exit 1' 1 2 15
    echo "Installing release $version for $host"
    curl -fsSL "$base/SHA256SUMS" -o "$tmpdir/SHA256SUMS"
    for program in "$@"; do
        asset="$program-$host"
        curl -fsSL "$base/$asset" -o "$tmpdir/$asset"
        awk -v asset="$asset" '$2 == asset { print }' "$tmpdir/SHA256SUMS" > "$tmpdir/$asset.sha256"
        if [ ! -s "$tmpdir/$asset.sha256" ]; then
            echo "Missing checksum for $asset" >&2
            exit 1
        fi
        if command -v sha256sum >/dev/null 2>&1; then
            (cd "$tmpdir" && sha256sum -c "$asset.sha256")
        else
            (cd "$tmpdir" && shasum -a 256 -c "$asset.sha256")
        fi
    done
    # Verify every download before replacing either installed program.
    for program in "$@"; do
        if [ -d "$install_dir/$program" ]; then
            echo "Cannot replace directory $install_dir/$program" >&2
            exit 1
        fi
    done
    mkdir -p "$install_dir"
    staging=$(mktemp -d "$install_dir/.curbpack-install.XXXXXX")
    for program in "$@"; do
        cp "$tmpdir/$program-$host" "$staging/$program"
        chmod +x "$staging/$program"
    done
    for program in "$@"; do
        mv -f "$staging/$program" "$install_dir/$program"
        echo "Installed: $install_dir/$program"
    done
    case ":$PATH:" in
        *":$install_dir:"*) ;;
        *)
            printf 'Add this directory to your shell PATH: %s\n' "$install_dir"
            if [ "$install_dir" = "$HOME/.local/bin" ]; then
                printf '%s\n' 'For this terminal: export PATH="$HOME/.local/bin:$PATH"'
            fi
            ;;
    esac
}
