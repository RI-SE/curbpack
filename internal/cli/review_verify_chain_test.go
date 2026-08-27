package cli

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/review"
)

func writeChainReport(t *testing.T, path string, rep review.Report) {
	t.Helper()
	b, err := json.Marshal(rep)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, b, 0o644); err != nil {
		t.Fatal(err)
	}
}

func TestReviewVerifyChainHappy(t *testing.T) {
	dir := t.TempDir()
	parentPath := filepath.Join(dir, "parent.json")
	childPath := filepath.Join(dir, "child.json")
	writeChainReport(t, parentPath, review.Report{
		Schema:       review.SchemaVersion,
		RecordDigest: "aaa111",
	})
	writeChainReport(t, childPath, review.Report{
		Schema:             review.SchemaVersion,
		RecordDigest:       "bbb222",
		ParentRecordDigest: "aaa111",
	})
	if err := Run([]string{"review", "--verify-chain", parentPath, childPath}); err != nil {
		t.Fatalf("want exit 0, got %v (code %d)", err, ExitCode(err))
	}
}

func TestReviewVerifyChainTamper(t *testing.T) {
	dir := t.TempDir()
	parentPath := filepath.Join(dir, "parent.json")
	childPath := filepath.Join(dir, "child.json")
	writeChainReport(t, parentPath, review.Report{
		Schema:       review.SchemaVersion,
		RecordDigest: "aaa111",
	})
	writeChainReport(t, childPath, review.Report{
		Schema:             review.SchemaVersion,
		RecordDigest:       "bbb222",
		ParentRecordDigest: "tampered",
	})
	err := Run([]string{"review", "--verify-chain", parentPath, childPath})
	if ExitCode(err) != ExitGates {
		t.Fatalf("want exit 1, got %d (%v)", ExitCode(err), err)
	}
}

func TestReviewVerifyChainEmptyParentDigest(t *testing.T) {
	dir := t.TempDir()
	parentPath := filepath.Join(dir, "parent.json")
	childPath := filepath.Join(dir, "child.json")
	writeChainReport(t, parentPath, review.Report{
		Schema: review.SchemaVersion,
	})
	writeChainReport(t, childPath, review.Report{
		Schema:             review.SchemaVersion,
		ParentRecordDigest: "aaa111",
	})
	err := Run([]string{"review", "--verify-chain", parentPath, childPath})
	if ExitCode(err) != ExitGates {
		t.Fatalf("want exit 1, got %d (%v)", ExitCode(err), err)
	}
}

func TestReviewVerifyChainExclusiveFlags(t *testing.T) {
	err := Run([]string{"review", "--verify-chain", "a.json", "b.json", "--json"})
	if ExitCode(err) != ExitUsage {
		t.Fatalf("want exit 2, got %d (%v)", ExitCode(err), err)
	}
	if err == nil || !strings.Contains(err.Error(), "--verify-chain") {
		t.Fatalf("message: %v", err)
	}
}
