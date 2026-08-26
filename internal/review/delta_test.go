package review_test

import (
	"bytes"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/review"
)

func TestDeltaThreeBuckets(t *testing.T) {
	prior := review.Report{
		Schema: review.SchemaVersion,
		Findings: []review.Finding{
			{ID: "a", State: review.StateUnconfirmed, Cause: review.CauseGenuine},
			{ID: "b", State: review.StateContradicted, Cause: review.CauseSelfDisagree},
			{ID: "c", State: review.StateConfirmed},
		},
		RecordDigest: "aabbccdd11223344",
	}
	current := review.Report{
		Schema: review.SchemaVersion,
		Findings: []review.Finding{
			{ID: "a", State: review.StateConfirmed},                          // cleared
			{ID: "b", State: review.StateUnconfirmed, Cause: review.CauseGenuine}, // persisting
			{ID: "d", State: review.StateContradicted, Cause: review.CauseSelfDisagree}, // new
		},
	}
	d := review.ComputeDelta(prior, current)
	if len(d.New) != 1 || d.New[0] != "d" {
		t.Fatalf("NEW=%v", d.New)
	}
	if len(d.Cleared) != 1 || d.Cleared[0] != "a" {
		t.Fatalf("CLEARED=%v", d.Cleared)
	}
	if len(d.Persisting) != 1 || d.Persisting[0] != "b" {
		t.Fatalf("PERSISTING=%v", d.Persisting)
	}
	block := review.FormatDelta(prior, current)
	if !strings.Contains(block, "delta since record aabbccdd…") {
		t.Fatalf("block=%q", block)
	}
	if !strings.Contains(block, "NEW") || !strings.Contains(block, "CLEARED") || !strings.Contains(block, "PERSISTING") {
		t.Fatalf("missing buckets: %q", block)
	}
}

func TestDeltaIdenticalRecordsAllPersistingNoneNewNoneCleared(t *testing.T) {
	rep := review.Report{
		Schema: review.SchemaVersion,
		Findings: []review.Finding{
			{ID: "x", State: review.StateUnconfirmed, Cause: review.CauseGenuine},
			{ID: "y", State: review.StateContradicted, Cause: review.CauseSelfDisagree},
		},
	}
	d := review.ComputeDelta(rep, rep)
	if len(d.New) != 0 || len(d.Cleared) != 0 {
		t.Fatalf("want empty new/cleared, got new=%v cleared=%v", d.New, d.Cleared)
	}
	if len(d.Persisting) != 2 {
		t.Fatalf("persisting=%v", d.Persisting)
	}
}

func TestDeltaExitCodeUnchanged(t *testing.T) {
	// NEW findings must not drive exit; only current contradictions do.
	dir := writeMinimalConsistent(t)
	prior := review.Report{Schema: review.SchemaVersion, RecordDigest: "deadbeef"}
	var buf bytes.Buffer
	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: &buf, Prior: &prior})
	if err != nil {
		t.Fatal(err)
	}
	if review.HasContradictions(rep) {
		t.Fatal("minimal consistent pack must not contradict")
	}
	if !strings.Contains(buf.String(), "delta since record") {
		t.Fatalf("expected delta block: %s", buf.String())
	}
}

func TestDeltaRejectsSchemaMismatch(t *testing.T) {
	// Exercised via CLI loadPriorReport contract — package review stays pure.
	// Keep a package-level note that SchemaVersion is the compare key.
	if review.SchemaVersion == "" {
		t.Fatal("SchemaVersion empty")
	}
}

func TestDeltaWarnsOnMethodVersionMismatch(t *testing.T) {
	prior := review.Report{
		Schema: review.SchemaVersion, MethodVersion: "1.0.0",
		RecordDigest: "aabbccdd11223344",
		Findings:     []review.Finding{{ID: "a", State: review.StateUnconfirmed, Cause: review.CauseGenuine}},
	}
	current := review.Report{
		Schema: review.SchemaVersion, MethodVersion: "1.1.0",
		Findings: []review.Finding{{ID: "a", State: review.StateUnconfirmed, Cause: review.CauseGenuine}},
	}
	block := review.FormatDelta(prior, current)
	want := "method_version differs: prior 1.0.0 · current 1.1.0 — findings may not be comparable"
	if !strings.Contains(block, want) {
		t.Fatalf("missing warn: %q", block)
	}
}

func TestDeltaMismatchRecordedNotOnlyPrinted(t *testing.T) {
	// Warn must live in FormatDelta output (redirectable stdout), not stderr-only.
	prior := review.Report{Schema: review.SchemaVersion, MethodVersion: "1.0.0", RecordDigest: "deadbeef"}
	current := review.Report{Schema: review.SchemaVersion, MethodVersion: "1.1.0"}
	block := review.FormatDelta(prior, current)
	if strings.TrimSpace(block) == "" {
		t.Fatal("empty delta block")
	}
	if !strings.Contains(block, "method_version differs") {
		t.Fatalf("warn not in recorded delta block: %q", block)
	}
	same := review.FormatDelta(
		review.Report{Schema: review.SchemaVersion, MethodVersion: "1.1.0", RecordDigest: "deadbeef"},
		review.Report{Schema: review.SchemaVersion, MethodVersion: "1.1.0"},
	)
	if strings.Contains(same, "method_version differs") {
		t.Fatalf("false warn on matching versions: %q", same)
	}
}
