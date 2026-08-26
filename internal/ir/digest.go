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
	failures := append([]Failure(nil), p.Failures...)
	sort.Slice(failures, func(i, j int) bool {
		if failures[i].GateID != failures[j].GateID {
			return failures[i].GateID < failures[j].GateID
		}
		return failures[i].Severity < failures[j].Severity
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
