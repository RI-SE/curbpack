#!/usr/bin/env bash
# Build-time only. Pages serves the checked-in result without npm or runtime JS.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
MODE=${1:-build}
case "$MODE" in build|--check) ;; *) echo 'usage: build-homepage-css.sh [--check]' >&2; exit 2 ;; esac
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
# Isolate npm cache from host-owned ~/.npm and never create package files in repo.
export npm_config_cache="${CURBPACK_CSS_NPM_CACHE:-$TMP/npm-cache}"
cd "$ROOT"
npx --yes --package=tailwindcss@3.4.17 tailwindcss \
  --config site/tailwind.config.cjs --input site/assets/homepage.input.css \
  --output "$TMP/homepage.css" --minify
if [ "$MODE" = '--check' ]; then
  cmp "$TMP/homepage.css" site/assets/homepage.css || {
    echo 'Homepage CSS is stale; run scripts/build-homepage-css.sh and review the result.' >&2
    exit 1
  }
else
  cp "$TMP/homepage.css" site/assets/homepage.css
fi
