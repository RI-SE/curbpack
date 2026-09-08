#!/usr/bin/env bash
# Focused behavioral regressions; full release evidence also requires the matrix
# and acceptance work documented in docs/production-hardening-audit.md.
set -euo pipefail
cd "$(dirname "$0")/.."
go test ./internal/outwrite ./internal/pathjail ./internal/validate ./internal/exportx ./internal/release ./internal/review ./internal/ir ./internal/cli -count=1 -run 'TestAudit|TestExplicitRecovery|TestReleasePreservesReplacedLock|TestWindowsPathFormsRefused|TestMultipleFindingsCountOneFailedGate|TestExplainCustomHomeIsRemovedBeforePublication|TestPrepareRefusesVEXEscape|TestEvaluationBinds|TestExplicitAsOf|TestImmutable|TestFreshEmission|TestPreparePreflightsWholePack|TestPreparePublishesEvaluation|TestReviewRejectsChangedManifestArtifact|TestOfflinePackAudit|TestHistoricalReportDigest|TestShareCopyRefuses|TestBuiltCLIAsOf'
bash scripts/action-resolve-test.sh
