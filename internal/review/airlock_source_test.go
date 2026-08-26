package review

import (
	"strings"
	"testing"
)

func TestAirlockRedactsSource(t *testing.T) {
	rep := Report{Findings: []Finding{{
		ID:     "reference:path:x",
		Detail: "path cite",
		Source: "/Users/evil/secret-surface.md",
		State:  StateUnconfirmed,
		Cause:  CauseGenuine,
	}}}
	if !redactReportAirlock(&rep) {
		t.Fatal("expected Source redaction")
	}
	if strings.Contains(rep.Findings[0].Source, "/Users/evil") {
		t.Fatalf("Source leaked home path: %q", rep.Findings[0].Source)
	}
	if !strings.Contains(rep.Findings[0].Source, redactedHome) {
		t.Fatalf("Source missing redaction token: %q", rep.Findings[0].Source)
	}
}
