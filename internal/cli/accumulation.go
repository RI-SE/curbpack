package cli

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/afelin/curbpack/internal/instrument"
	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/redact"
	"github.com/afelin/curbpack/internal/validate"
)

// instrumentPanelCovenant is always printed after the check tally (green and red).
const instrumentPanelCovenant = "instrument panel · not a security program · not conformity assessment"

// priorCacheSnapshot is the quiet accumulation whisper source (pre-overwrite).
type priorCacheSnapshot struct {
	ComparisonKey  string
	OK             bool
	PackID         string
	SchemaVersion  string
	Failed         int
	Evaluated      int
	Skipped        int
	ReadinessScore int // historical only
	FailureCount   int
}

func loadPriorCache(root string) priorCacheSnapshot {
	if e, _, err := validate.LoadLatest(root); err == nil && e.SchemaVersion == ir.EvaluationSchemaVersion {
		return priorCacheSnapshot{OK: true, ComparisonKey: e.ComparisonKey, PackID: e.PackID, SchemaVersion: e.SchemaVersion, Failed: e.FailedRules, Evaluated: e.EvaluatedRules, Skipped: e.SkippedRules, FailureCount: len(e.Failures), ReadinessScore: e.ReadinessScore}
	}
	path := filepath.Join(root, ".github", "curbpack", "cache", "latest_result.json")
	b, err := os.ReadFile(path)
	if err != nil {
		path = filepath.Join(root, ".github", "curbpack", "cache", "latest_failure.json")
		b, err = os.ReadFile(path)
		if err != nil {
			return priorCacheSnapshot{}
		}
	}
	var raw struct {
		SchemaVersion  string            `json:"schema_version"`
		PackID         string            `json:"pack_id"`
		ReadinessScore int               `json:"readiness_score"`
		FailedRules    int               `json:"failed_rules"`
		EvaluatedRules int               `json:"evaluated_rules"`
		SkippedRules   int               `json:"skipped_rules"`
		Failures       []json.RawMessage `json:"failures"`
	}
	if err := json.Unmarshal(b, &raw); err != nil {
		return priorCacheSnapshot{}
	}
	n := 0
	if raw.Failures != nil {
		n = len(raw.Failures)
	}
	failed := raw.FailedRules
	if failed == 0 {
		failed = n
	}
	return priorCacheSnapshot{
		OK:             false, // historical aliases lack bound method/input identity
		PackID:         raw.PackID,
		SchemaVersion:  raw.SchemaVersion,
		Failed:         failed,
		Evaluated:      raw.EvaluatedRules,
		Skipped:        raw.SkippedRules,
		ReadinessScore: raw.ReadinessScore,
		FailureCount:   n,
	}
}

// accumulationDeltaLine returns at most one quiet line when prior cache exists
// and pack/schema are compatible. Trends use failed counts, not percent grades.
func accumulationDeltaLine(prior priorCacheSnapshot, nowPack string, nowFailed int, keys ...string) string {
	if len(keys) != 1 {
		return ""
	}
	return redact.TrendLine(prior.OK, prior.PackID, nowPack, prior.SchemaVersion, ir.EvaluationSchemaVersion, prior.Failed, nowFailed, prior.ComparisonKey, keys[0])
}

// instrumentWhisperLines returns at most 3 dim instrument lines.
func instrumentWhisperLines(priorCache priorCacheSnapshot, priorInst instrument.Snapshot, priorOK bool, nowPack string, nowFailed int, nowInst instrument.Snapshot, keys ...string) []string {
	var lines []string
	if line := accumulationDeltaLine(priorCache, nowPack, nowFailed, keys...); line != "" {
		lines = append(lines, line)
	}
	if !priorOK {
		return lines
	}
	if priorInst.DepsFP != nowInst.DepsFP {
		add, rem := instrument.DepDelta(priorInst, nowInst)
		lines = append(lines, fmt.Sprintf("Δ deps +%d/−%d", add, rem))
	}
	if priorInst.SecretHits != nowInst.SecretHits {
		lines = append(lines, fmt.Sprintf("Δ secret-hits %d→%d", priorInst.SecretHits, nowInst.SecretHits))
	}
	if len(lines) > 3 {
		lines = lines[:3]
	}
	return lines
}
