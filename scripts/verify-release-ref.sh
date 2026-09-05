#!/usr/bin/env bash
# Verify that version, immutable tag, and the checkout being built agree.
set -euo pipefail
TAG=${1:-}
if [[ ! "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$ ]]; then
  echo 'release requires a version tag such as v1.2.3' >&2
  exit 1
fi
TAG_SHA=$(git rev-parse --verify "refs/tags/${TAG}^{commit}")
HEAD_SHA=$(git rev-parse --verify HEAD)
if [[ "$TAG_SHA" != "$HEAD_SHA" ]]; then
  echo 'release checkout does not match requested tag' >&2
  exit 1
fi
if [[ -n "$(git status --porcelain --untracked-files=normal)" ]]; then
  echo 'release checkout must be clean before building' >&2
  exit 1
fi
printf '%s\n' "$TAG_SHA"
