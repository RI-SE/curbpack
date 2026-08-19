package clock_test

import (
	"testing"
	"time"

	"github.com/afelin/curbpack/internal/clock"
)

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
