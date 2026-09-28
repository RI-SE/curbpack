#!/usr/bin/env bash
# Local mirror of .github/workflows/ci.yml — silent steps, one line each.
# Dirty tree OK. Re-run a failed line by copying the printed command.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export GITHUB_WORKSPACE="$ROOT"
export CURBPACK_BIN="$ROOT/bin/curbpack"
exec </dev/null

if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
  G=$'\033[32m' R=$'\033[31m' Z=$'\033[0m'
else
  G= R= Z=
fi

WIDTH=72

# One command string per line. Flags belong in the string (e.g. --yes).
CMDS=(
  "python3 scripts/check-required-contexts.py"
  "env SOURCE_DATE_EPOCH=1704067200 go test ./... -count=1"
  "env SOURCE_DATE_EPOCH= go test ./internal/clock/ ./internal/ir/ ./internal/validate/ -count=1 -run 'TestRejectInvalidSourceDateEpoch|TestCanonicalEvaluationStableWithoutEpoch|TestCanonicalEvaluationStableAcrossHOME|TestValidateRejectsInvalidSourceDateEpoch|TestLegacyEvaluationAdapterRoundTrip|TestMarshalCanonicalStable|TestRFC3339ForEvidenceStableWithoutEpoch'"
  "go test ./internal/validate/ -fuzz=FuzzSafeJoin -fuzztime=5s"
  "go test ./internal/validate/ -fuzz=FuzzTextForbidRegex -fuzztime=5s"
  "go test ./internal/attest/ -fuzz=FuzzParseHPURLFragment -fuzztime=5s"
  "./scripts/ci-build.sh"
  "./scripts/ci/doctor-demo.sh"
  "./scripts/ci/smoke-spaced-path.sh"
  "./scripts/ci/smoke-cra.sh"
  "./scripts/ci/smoke-house-policy.sh"
  "./scripts/ci/smoke-scan.sh"
  "./scripts/ci/pin-guard.sh"
  "./scripts/redteam-pilot.sh"
  "./scripts/claim-safety.sh"
  "python3 scripts/test_public_assets.py"
  "python3 scripts/check-public-assets.py"
  "./scripts/release-ref-test.sh"
  "./scripts/install-version-test.sh"
  "./scripts/ci/manifest-parity.sh"
  "./scripts/gauntlet-ratchet.sh"
  "./scripts/ci/deadend-corrupt-pack.sh"
  "./scripts/chaos-deadends.sh $ROOT/bin/curbpack"
)

# Optional steps (skip quietly if tools/token missing)
if command -v npx >/dev/null 2>&1; then
  CMDS+=("./scripts/build-homepage-css.sh --check")
fi
if [[ -n "${GH_TOKEN:-${GITHUB_TOKEN:-}}" ]]; then
  CMDS+=("env CURBPACK_VERSION=\$(python3 -c 'import json; print(json.load(open(\"scripts/install-manifest.json\"))[\"default_version\"])') GITHUB_TOKEN=\${GITHUB_TOKEN:-\$GH_TOKEN} ./scripts/release-smoke-install-scan.sh")
fi
if [[ "${CURBPACK_CI_BROWSER:-}" == "1" ]]; then
  CMDS+=("env CURBPACK_BROWSER_TESTS=1 python3 scripts/test_public_assets.py HomepageBrowserTests")
fi

for CMD in "${CMDS[@]}"; do
  printf '%s' "$CMD"
  pad=$((WIDTH - ${#CMD}))
  if (( pad > 0 )); then
    printf '%*s' "$pad" '' | tr ' ' '.'
  else
    printf ' '
  fi
  if bash -c "$CMD" >/dev/null 2>&1; then
    printf '%s[PASS]%s\n' "$G" "$Z"
  else
    printf '%s[FAIL]%s\n' "$R" "$Z"
    exit 1
  fi
done
