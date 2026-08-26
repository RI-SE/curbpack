package cli

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/review"
)

func TestRepoModeRefusesBatch(t *testing.T) {
	err := Run([]string{"review", "--repo", t.TempDir(), "--batch", t.TempDir()})
	if ExitCode(err) != ExitUsage {
		t.Fatalf("want exit 2, got %d (%v)", ExitCode(err), err)
	}
	if err == nil || !strings.Contains(err.Error(), "--batch") {
		t.Fatalf("message: %v", err)
	}
}

func TestRepoModeEmptyProsePathsExitsTwo(t *testing.T) {
	// Invalid pack id forces ProsePaths/compose failure → exit 2 naming the fix.
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, ".curbpack.json"), []byte(`{"packs":["not-a-real-pack-id"]}`+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	err := Run([]string{"review", "--repo", dir})
	if ExitCode(err) != ExitUsage {
		t.Fatalf("want exit 2, got %d (%v)", ExitCode(err), err)
	}
	if err == nil || !strings.Contains(err.Error(), "compose pack surfaces") {
		t.Fatalf("message should name compose fix: %v", err)
	}
}

func TestRepoModeUsesProsePaths(t *testing.T) {
	dir := t.TempDir()
	// Minimal house-policy targets often include SECURITY.md; create it and a note.
	mustWriteCLI(t, filepath.Join(dir, "SECURITY.md"), []byte("# security\n"))
	mustWriteCLI(t, filepath.Join(dir, "docs"), nil) // ensure parent if needed
	// Run against this repo — ResolvePackIDs defaults to house-policy.
	stdout, stderr := captureReview(t, func() {
		err := Run([]string{"review", "--repo", dir, "--json"})
		if err != nil && ExitCode(err) != ExitOK && ExitCode(err) != ExitGates {
			t.Fatalf("unexpected: %v code=%d", err, ExitCode(err))
		}
	})
	_ = stderr
	var rep review.Report
	if err := json.Unmarshal([]byte(stdout), &rep); err != nil {
		t.Fatalf("json: %v\n%s", err, stdout)
	}
	if rep.DigestScope != review.DigestScopeClosure {
		t.Fatalf("digest_scope=%q", rep.DigestScope)
	}
	if rep.MethodVersion != review.MethodVersion {
		t.Fatalf("method=%q", rep.MethodVersion)
	}
}

func TestRepoModeComposesWithSince(t *testing.T) {
	dir := t.TempDir()
	mustWriteCLI(t, filepath.Join(dir, "SECURITY.md"), []byte("# security\n"))
	priorPath := filepath.Join(dir, "prior.json")
	prior := review.Report{
		Schema:        review.SchemaVersion,
		MethodVersion: "1.0.0",
		RecordDigest:  "aabbccdd11223344",
		Findings:      []review.Finding{{ID: "reference:path:SECURITY.md", State: review.StateUnconfirmed, Cause: review.CauseGenuine, Source: "x"}},
	}
	b, _ := json.Marshal(prior)
	if err := os.WriteFile(priorPath, b, 0o644); err != nil {
		t.Fatal(err)
	}
	stdout, _ := captureReview(t, func() {
		err := Run([]string{"review", "--repo", dir, "--since", priorPath})
		if err != nil && ExitCode(err) != ExitOK && ExitCode(err) != ExitGates {
			t.Fatalf("unexpected: %v code=%d", err, ExitCode(err))
		}
	})
	if !strings.Contains(stdout, "delta since record") {
		t.Fatalf("expected delta block: %s", stdout)
	}
	if !strings.Contains(stdout, "method_version differs") {
		t.Fatalf("expected method_version warn: %s", stdout)
	}
}

func mustWriteCLI(t *testing.T, path string, data []byte) {
	t.Helper()
	if data == nil {
		if err := os.MkdirAll(path, 0o755); err != nil {
			t.Fatal(err)
		}
		return
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, data, 0o644); err != nil {
		t.Fatal(err)
	}
}
