#!/usr/bin/env bash
# Real Git regression: release version must identify exactly the checkout built.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
git init -q
git -c user.name=Test -c user.email=test@example.invalid -c commit.gpgsign=false commit --allow-empty -qm first
git tag v9.8.7
"$ROOT/scripts/verify-release-ref.sh" v9.8.7
for invalid in main v9.8.6 '--help' 'v1.2.3;echo injected'; do
  if "$ROOT/scripts/verify-release-ref.sh" "$invalid"; then
    echo "accepted invalid release ref: $invalid" >&2; exit 1
  fi
done
git -c user.name=Test -c user.email=test@example.invalid -c commit.gpgsign=false commit --allow-empty -qm second
if "$ROOT/scripts/verify-release-ref.sh" v9.8.7; then
  echo 'accepted checkout different from release tag' >&2; exit 1
fi
echo 'release-ref tests passed'
