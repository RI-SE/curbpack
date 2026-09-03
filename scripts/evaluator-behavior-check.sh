#!/usr/bin/env bash
# Lean tip-evaluator behavior bar: vacuous-pass / target-absent / anti_placeholder cases.
# Exit non-zero on failure. No new deps. See docs/internal/evaluator-tip-drift.md.
set -euo pipefail

ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT"

echo "evaluator-behavior-check: internal/validate vacuous-pass / target-absent / anti_placeholder"
go test ./internal/validate/ \
  -run 'TestAntiPlaceholderTargetAbsentWhenAllMissing|TestNPMDepBanVacuousPassPresentManifest|TestNPMDepBanTargetAbsentMissingManifest|TestAntiPlaceholderUntouchedStubFails|TestAntiPlaceholderStubPlusProductNameStillFails|TestFreshStubFailsAntiPlaceholderInSameRun|TestFreshStubCannotProduceGreenResult' \
  -count=1
echo "evaluator-behavior-check: ok"
