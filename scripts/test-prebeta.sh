#!/usr/bin/env bash
# The friendly-user entry point: build the right CLI and retain an isolated run.
set -euo pipefail
# Tester files are private by default. Git settings/identity cannot bleed into
# the fixture or select an unrelated repository through inherited GIT_* vars.
umask 077
while IFS= read -r variable; do
  case "$variable" in GIT_*) unset "$variable" ;; esac
done < <(compgen -e)
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_SYSTEM=/dev/null GIT_CONFIG_GLOBAL=/dev/null
root=$(cd "$(dirname "$0")/.." && pwd)
if [[ $# -ne 0 ]]; then echo 'Usage: scripts/test-prebeta.sh (no arguments)' >&2; exit 2; fi
cd "$root"
# A full first-run exercise, unaffected by an ambient reproducible-build epoch.
unset SOURCE_DATE_EPOCH
as_of=$(date -u +%F)
runs="${CURBPACK_TEST_RUNS_DIR:-$HOME/curbpack-prebeta-runs}"
mkdir -p "$runs"
run=$(mktemp -d "$runs/run.XXXXXX")
mkdir "$run/empty-git-template"
export GIT_TEMPLATE_DIR="$run/empty-git-template"
echo "Run folder: $run"
trap 'echo "Stopped before completion. Inspect logs in: $run" >&2' ERR
cli="$run/curbpack-prebeta"
"$root/scripts/build-prebeta.sh" "$cli"
cp "${cli}.build.txt" "$run/build.txt"
{ "$cli" version; go version; uname -sm; printf 'as_of=%s\n' "$as_of"; } > "$run/environment.txt"
# demo --out creates a fresh example; it does not initialize the caller's repo.
"$cli" doctor > "$run/01-doctor.txt" 2>&1
"$cli" demo --out "$run/example" > "$run/02-demo.txt" 2>&1
(
  cd "$run/example"
  git status --porcelain=v1 --untracked-files=all > "$run/before-scan.txt"
  "$cli" scan --packs house-policy > "$run/03-scan.txt" 2>&1
  git status --porcelain=v1 --untracked-files=all > "$run/after-scan.txt"
  cmp "$run/before-scan.txt" "$run/after-scan.txt"
  "$cli" check --json --as-of "$as_of" > "$run/04-check.json" 2> "$run/04-check.err"
  "$cli" share --bundle --as-of "$as_of" > "$run/05-share.txt" 2>&1
)
mkdir "$run/recipient"
cp -R "$run/example/review-pack" "$run/recipient/review-pack"
(cd "$run/recipient" && "$cli" review "$run/recipient/review-pack" --json) \
  > "$run/06-review.json" 2> "$run/06-review.err"
cat > "$run/START-HERE.txt" <<TEXT
Curbpack friendly pre-beta — local test run

$(cat "$run/build.txt")
Evaluation date: $as_of

1. Open recipient/review-pack/evidence-bundle.html in your browser.
2. Read 03-scan.txt and 04-check.json: diagnosis and gate results differ.
3. Read 06-review.json: pack_audit distinguishes integrity, authenticity,
   completeness and applicability. This unsigned fixture is not certification.
4. Use feedback.txt for a minimal report; keep raw logs private.

The example is a deliberately passing demo. This run does not assess your product.
All command checks completed; scan preserved Git status. An independent human
still needs to decide whether the output is understandable and useful.

Binary used: ./curbpack-prebeta (in this run folder)
Guide: docs/getting-started/prebeta.md in the source checkout
TEXT
cat > "$run/feedback.txt" <<TEXT
Curbpack prepared-example feedback
$(cat "$run/build.txt")
Platform: $(uname -sm)
Completed commands: doctor, demo, scan, check, share --bundle, review
Expected: fixture passes; unsigned pack integrity verifies.
Observation (write here; omit private names, paths, secrets and product content):
TEXT
trap - ERR
cat "$run/START-HERE.txt"
echo "Results: $run"
echo "On macOS, open: open \"$run/recipient/review-pack/evidence-bundle.html\""
