package clock_test

import (
	"testing"
	"time"

	"github.com/afelin/curbpack/internal/clock"
)

func TestFormatArt14Countdown(t *testing.T) {
	cases := []struct {
		days int
		want string
	}{
		{23, "23 days until 11 September 2026"},
		{1, "1 day until 11 September 2026"},
		{0, "starts today (11 September 2026)"},
		{-1, "started 1 day ago (11 September 2026)"},
		{-5, "started 5 days ago (11 September 2026)"},
	}
	for _, c := range cases {
		if got := clock.FormatArt14Countdown(c.days); got != c.want {
			t.Fatalf("FormatArt14Countdown(%d) = %q, want %q", c.days, got, c.want)
		}
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
