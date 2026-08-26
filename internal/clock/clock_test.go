package clock_test

import (
	"os"
	"testing"
	"time"

	"github.com/afelin/curbpack/internal/clock"
)

func TestFormatArt14Countdown(t *testing.T) {
	cases := []struct {
		days int
		want string
	}{
		{23, "Article 14 reporting starts in 23 days (11 September 2026)"},
		{1, "Article 14 reporting starts in 1 day (11 September 2026)"},
		{0, "Article 14 reporting starts today (11 September 2026)"},
		{-1, "Article 14 reporting has applied since 11 September 2026"},
		{-5, "Article 14 reporting has applied since 11 September 2026"},
	}
	for _, c := range cases {
		if got := clock.FormatArt14Countdown(c.days); got != c.want {
			t.Fatalf("FormatArt14Countdown(%d) = %q, want %q", c.days, got, c.want)
		}
	}
}

func TestFormatArt14CountdownPastDeadline(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "1789171200") // 2026-09-12 UTC (day after Art14ReportingStart)
	days := clock.DaysUntilUTC(clock.Art14ReportingStart)
	if days != -1 {
		t.Fatalf("want -1 day after deadline, got %d", days)
	}
	got := clock.FormatArt14Countdown(days)
	want := "Article 14 reporting has applied since 11 September 2026"
	if got != want {
		t.Fatalf("FormatArt14Countdown(%d) = %q, want %q", days, got, want)
	}
}

func TestDaysUntilArt14Reporting(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "1757548800") // 2025-09-11 UTC
	days := clock.DaysUntilUTC(clock.Art14ReportingStart)
	if days != 365 {
		t.Fatalf("want 365 days until 2026-09-11 from 2025-09-11, got %d", days)
	}
	if clock.Art14ReportingStart != time.Date(2026, 9, 11, 0, 0, 0, 0, time.UTC) {
		t.Fatal("Art14ReportingStart date drift")
	}
}

func TestRFC3339ForEvidenceStableWithoutEpoch(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "")
	_ = os.Unsetenv("SOURCE_DATE_EPOCH")
	a := clock.RFC3339ForEvidence()
	b := clock.RFC3339ForEvidence()
	if a != b {
		t.Fatalf("evidence RFC3339 drifted: %q vs %q", a, b)
	}
	if a != clock.EvidenceEpoch {
		t.Fatalf("want fixed EvidenceEpoch %q, got %q", clock.EvidenceEpoch, a)
	}
}

func TestRFC3339ForEvidenceHonorsSourceDateEpoch(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "1704067200") // 2024-01-01 UTC
	got := clock.RFC3339ForEvidence()
	want := "2024-01-01T00:00:00Z"
	if got != want {
		t.Fatalf("RFC3339ForEvidence() = %q, want %q", got, want)
	}
}
