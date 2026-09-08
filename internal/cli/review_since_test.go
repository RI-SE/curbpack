package cli

import (
	"encoding/json"
	"fmt"
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

func TestReviewSinceRejectsDamagedDigest(t *testing.T) {
	for _, repoMode := range []bool{false, true} {
		for _, damage := range []string{"contents", "missing", "fabricated"} {
			t.Run(fmt.Sprintf("repo=%t/%s", repoMode, damage), func(t *testing.T) {
				pack := filepath.Join(t.TempDir(), "pack")
				writeMinimalPack(t, pack)
				prior, err := review.Run(review.Options{BundleRoot: pack, JSONOut: true})
				if err != nil {
					t.Fatal(err)
				}
				switch damage {
				case "contents":
					prior.ConfirmedCount++
				case "missing":
					prior.RecordDigest = ""
				case "fabricated":
					prior.RecordDigest = strings.Repeat("a", 64)
				}
				priorPath := filepath.Join(t.TempDir(), "prior.json")
				writeChainReport(t, priorPath, prior)
				args := []string{"review", pack, "--since", priorPath, "--json"}
				if repoMode {
					args = []string{"review", "--repo", pack, "--since", priorPath, "--json"}
				}
				stdout, _ := captureReview(t, func() { err = Run(args) })
				if ExitCode(err) != ExitUsage || !strings.Contains(err.Error(), "prior report record_digest") {
					t.Fatalf("damaged prior must exit 2 with digest diagnostic; got %d (%v)", ExitCode(err), err)
				}
				if stdout != "" {
					t.Fatalf("damaged prior emitted a report: %s", stdout)
				}
			})
		}
	}
}
