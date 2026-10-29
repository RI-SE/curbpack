#!/usr/bin/env bash
# Download and run the Linux x64 checker for the root GitHub Action.
set -euo pipefail

if [[ "$RUNNER_OS/$RUNNER_ARCH" != "Linux/X64" ]]; then
    echo "curbcheck Action requires a Linux x64 runner (Ubuntu 22.04 or newer)." >&2
    exit 1
fi

if [[ -z "$CURBCHECK_RELEASE" || "$CURBCHECK_RELEASE" == *[!a-zA-Z0-9._-]* ]]; then
    echo "Set release to a published tag containing only letters, digits, dots, underscores and hyphens." >&2
    exit 1
fi

tool_dir="$(mktemp -d "$RUNNER_TEMP/curbcheck.XXXXXX")"
base="https://github.com/RI-SE/curbpack/releases/download/$CURBCHECK_RELEASE"
curl -fsSL "$base/curbcheck-linux-x64" -o "$tool_dir/curbcheck-linux-x64"
curl -fsSL "$base/SHA256SUMS" -o "$tool_dir/SHA256SUMS"
(
    cd "$tool_dir"
    awk '$2 == "curbcheck-linux-x64" { print }' SHA256SUMS > curbcheck.sha256
    test -s curbcheck.sha256
    sha256sum -c curbcheck.sha256
)
chmod +x "$tool_dir/curbcheck-linux-x64"

printf 'result=%s\n' "$tool_dir/run-result.json" >> "$GITHUB_OUTPUT"
"$tool_dir/curbcheck-linux-x64" --repo "$GITHUB_WORKSPACE" --out "$tool_dir/run-result.json"
