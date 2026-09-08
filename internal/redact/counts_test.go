package redact_test

import (
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/redact"
)

func TestCountsLineNoPercent(t *testing.T) {
	c := redact.FromRules(2, 1, 10)
	line := c.Line(true)
	if strings.Contains(line, "%") || strings.Contains(line, "readiness") {
		t.Fatalf("must not use percent grade: %q", line)
	}
	if line != "failed=2 evaluated=9 skipped=1 gates=open" {
		t.Fatalf("got %q", line)
	}
}

func TestTrendRequiresCompatiblePack(t *testing.T) {
	if got := redact.TrendLine(true, "house-policy", "cra-baseline", "1", "1", 2, 0); got != "" {
		t.Fatalf("incompatible packs must not trend: %q", got)
	}
	got := redact.TrendLine(true, "house-policy", "house-policy", "1", "1", 2, 0, strings.Repeat("a", 64), strings.Repeat("a", 64))
	if !strings.Contains(got, "Δ failed 2→0") {
		t.Fatalf("got %q", got)
	}
}

func TestTrendRefusesMissingOrChangedIdentity(t *testing.T) {
	for _, keys := range [][]string{nil, {strings.Repeat("a", 64), strings.Repeat("b", 64)}} {
		if got := redact.TrendLine(true, "same", "same", "2", "2", 2, 0, keys...); got != "" {
			t.Fatalf("unbound trend: %s", got)
		}
	}
}
