package cli

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/review"
)

func TestReviewSinceRejectsUnreadablePrior(t *testing.T) {
	err := Run([]string{"review", t.TempDir(), "--since", filepath.Join(t.TempDir(), "missing.json")})
	if ExitCode(err) != ExitUsage {
		t.Fatalf("want exit 2, got %d (%v)", ExitCode(err), err)
	}
	if err == nil || !strings.Contains(err.Error(), "--since") {
		t.Fatalf("message: %v", err)
	}
}

func TestReviewSinceRejectsSchemaMismatch(t *testing.T) {
	dir := t.TempDir()
	priorPath := filepath.Join(dir, "prior.json")
	bad := review.Report{Schema: "curbpack-review-report:1", Findings: nil}
	b, _ := json.Marshal(bad)
	if err := os.WriteFile(priorPath, b, 0o644); err != nil {
		t.Fatal(err)
	}
	pack := filepath.Join(dir, "pack")
	writeMinimalPack(t, pack)
	err := Run([]string{"review", pack, "--since", priorPath})
	if ExitCode(err) != ExitUsage {
		t.Fatalf("want exit 2, got %d (%v)", ExitCode(err), err)
	}
	if err == nil || !strings.Contains(err.Error(), "schema mismatch") {
		t.Fatalf("message: %v", err)
	}
}

func TestReviewSinceRefusesBatch(t *testing.T) {
	err := Run([]string{"review", "--batch", t.TempDir(), "--since", "x.json"})
	if ExitCode(err) != ExitUsage {
		t.Fatalf("want exit 2, got %d (%v)", ExitCode(err), err)
	}
	if err == nil || !strings.Contains(err.Error(), "--since") {
		t.Fatalf("message: %v", err)
	}
}
