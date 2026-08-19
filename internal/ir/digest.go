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
	writeLenPrefixed(h, strings.TrimSpace(p.PackID))
	writeLenPrefixed(h, fmt.Sprintf("%d", p.ReadinessScore))
	failures := append([]Failure(nil), p.Failures...)
	sort.Slice(failures, func(i, j int) bool {
		if failures[i].GateID != failures[j].GateID {
			return failures[i].GateID < failures[j].GateID
		}
		return failures[i].Severity < failures[j].Severity
	})
	for _, f := range failures {
		writeLenPrefixed(h, f.GateID)
		writeLenPrefixed(h, f.Severity)
		writeLenPrefixed(h, f.Type)
		writeLenPrefixed(h, f.ASTCoordinates.TargetFile)
	}
	return fmt.Sprintf("%x", h.Sum(nil))
}

func writeLenPrefixed(h hash.Hash, s string) {
	_, _ = fmt.Fprintf(h, "%d:", len(s))
	_, _ = io.WriteString(h, s)
}
