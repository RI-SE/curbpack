package ir

import (
	"crypto/sha256"
	"fmt"
	"hash"
	"io"
	"sort"
	"strings"
)

// ComputeResultDigest returns a stable sha256 hex of gate evaluation outcome fields.
// Excludes wall-clock timestamp and agent identity — binds attest to evaluated result.
func ComputeResultDigest(p GateFailurePayload) string {
	h := sha256.New()
	WriteLenPrefixed(h, strings.TrimSpace(p.PackID))
	WriteLenPrefixed(h, fmt.Sprintf("%d", p.ReadinessScore))
	// Legacy records without completeness fields retain their historical digest.
	// Outcome-bearing records must bind both fields; older such records need
	// regeneration and must not fall back to the unbound digest on mismatch.
	bindCompleteness := p.Outcome != "" || p.SkippedRules != 0
	if bindCompleteness {
		WriteLenPrefixed(h, "curbpack-result-completeness:1")
		WriteLenPrefixed(h, p.Outcome)
		WriteLenPrefixed(h, fmt.Sprintf("%d", p.SkippedRules))
	}
	failures := append([]Failure(nil), p.Failures...)
	sort.Slice(failures, func(i, j int) bool {
		if failures[i].GateID != failures[j].GateID {
			return failures[i].GateID < failures[j].GateID
		}
		if failures[i].Severity != failures[j].Severity {
			return failures[i].Severity < failures[j].Severity
		}
		if !bindCompleteness {
			return false // preserve the frozen legacy digest ordering
		}
		if failures[i].Type != failures[j].Type {
			return failures[i].Type < failures[j].Type
		}
		return failures[i].ASTCoordinates.TargetFile < failures[j].ASTCoordinates.TargetFile
	})
	for _, f := range failures {
		WriteLenPrefixed(h, f.GateID)
		WriteLenPrefixed(h, f.Severity)
		WriteLenPrefixed(h, f.Type)
		WriteLenPrefixed(h, f.ASTCoordinates.TargetFile)
	}
	return fmt.Sprintf("%x", h.Sum(nil))
}

// WriteLenPrefixed writes len(s) as decimal then ':' then s into h.
// Exported for review digests; attest keeps its private copy (frozen capsule surface).
func WriteLenPrefixed(h hash.Hash, s string) {
	_, _ = fmt.Fprintf(h, "%d:", len(s))
	_, _ = io.WriteString(h, s)
}
