#!/usr/bin/env bash
# The friendly-user entry point: build the right CLI and retain an isolated run.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
if [[ $# -ne 0 ]]; then echo 'Usage: scripts/test-prebeta.sh (no arguments)' >&2; exit 2; fi
cd "$root"
# A full first-run exercise, unaffected by an ambient reproducible-build epoch.
unset SOURCE_DATE_EPOCH
as_of=$(date -u +%F)
runs="${CURBPACK_TEST_RUNS_DIR:-$HOME/curbpack-prebeta-runs}"
mkdir -p "$runs"
run=$(mktemp -d "$runs/run.XXXXXX")
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
4. Record what was unclear; include build.txt, OS and the command in feedback.

The example is a deliberately passing demo. This run does not assess your product.
All command checks completed; scan preserved Git status. An independent human
still needs to decide whether the output is understandable and useful.

Binary used: $cli
Guide: $root/docs/getting-started/prebeta.md
TEXT
trap - ERR
cat "$run/START-HERE.txt"
echo "Results: $run"
echo "On macOS, open: open \"$run/recipient/review-pack/evidence-bundle.html\""
