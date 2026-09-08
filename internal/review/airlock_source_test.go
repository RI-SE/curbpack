package review

import (
	"encoding/json"
	"github.com/afelin/curbpack/internal/redact"
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

func TestReviewExplicitCustomHomeScrubsAllReportStrings(t *testing.T) {
	home := "/opt/custom-reviewer-home"
	rep := Report{SubjectCommit: home + "/claim", TriageSurfaces: []string{home + "/doc.md"}, Findings: []Finding{{ID: "reference:" + home, Detail: home + "/secret", Source: home + "/doc.md"}}, Audit: &PackAudit{Integrity: Assessment{Status: "failed", Detail: home + "/file"}}}
	changed, err := redactReportWithContext(&rep, redact.Context{Mode: redact.Embedded, Home: home})
	if err != nil || !changed {
		t.Fatalf("custom-home scrub: %v %v", changed, err)
	}
	raw, _ := json.Marshal(rep)
	if strings.Contains(string(raw), home) {
		t.Fatalf("custom home remains: %s", raw)
	}
}
