#!/usr/bin/env bash
# Build committed source only, with an unmistakable pre-beta identity.
set -euo pipefail
# Tester files are private by default. Git settings/identity cannot bleed into
# the fixture or select an unrelated repository through inherited GIT_* vars.
umask 077
while IFS= read -r variable; do
  case "$variable" in GIT_*) unset "$variable" ;; esac
done < <(compgen -e)
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_SYSTEM=/dev/null GIT_CONFIG_GLOBAL=/dev/null
root=$(cd "$(dirname "$0")/.." && pwd)
minimum=40d80909db6b19fa3309351e8d9998b0e305c468
command -v go >/dev/null || { echo 'Go 1.23+ is required.' >&2; exit 2; }
command -v git >/dev/null || { echo 'Git is required.' >&2; exit 2; }
git -C "$root" merge-base --is-ancestor "$minimum" HEAD || {
  echo 'This checkout does not include merged PR #58. Fetch and select current main first.' >&2
  exit 2
}
sha=$(git -C "$root" rev-parse HEAD)
label="0.5.5-prebeta+g${sha:0:12}"
output="${1:-$root/bin/curbpack-prebeta}"
if [[ $# -gt 1 ]]; then echo 'Usage: scripts/build-prebeta.sh [output-binary]' >&2; exit 2; fi
mkdir -p "$(dirname "$output")"
output=$(cd "$(dirname "$output")" && pwd)/$(basename "$output")
work=$(mktemp -d "${TMPDIR:-/tmp}/curbpack-prebeta-build.XXXXXX")
trap 'rm -rf "$work"' EXIT
mkdir "$work/source"
git -C "$root" archive "$sha" | tar -x -C "$work/source"
echo "Building committed source $sha ($label)"
echo 'Uncommitted source changes are excluded.'
(cd "$work/source" && CGO_ENABLED=0 GOOS="$(go env GOHOSTOS)" GOARCH="$(go env GOHOSTARCH)" \
  go build -trimpath -ldflags "-X github.com/afelin/curbpack/internal/buildinfo.Version=$label" \
  -o "$work/curbpack" ./cmd/curbpack)
[[ "$("$work/curbpack" version)" == "curbpack $label" ]] || {
  echo 'Built binary identity did not match the selected commit.' >&2; exit 1;
}
# Stage beside the destination so replacement cannot expose a partial binary.
staged=$(mktemp "${output}.XXXXXX")
trap 'rm -rf "$work"; rm -f "${staged:-}"' EXIT
cp "$work/curbpack" "$staged"
chmod 755 "$staged"
mv -f "$staged" "$output"
printf 'source_commit=%s\nversion=%s\n' "$sha" "$label" > "${output}.build.txt"
echo "Binary: $output"
"$output" version
