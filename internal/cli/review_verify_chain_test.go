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

func consistentChainPair(t *testing.T) (parent, child review.Report) {
	t.Helper()
	parent = review.Report{
		Schema:         review.SchemaVersion,
		MethodVersion:  review.MethodVersion,
		ConfirmedCount: 1,
	}
	parent.RecordDigest = review.ComputeRecordDigest(parent)
	child = review.Report{
		Schema:             review.SchemaVersion,
		MethodVersion:      review.MethodVersion,
		ConfirmedCount:     2,
		ParentRecordDigest: parent.RecordDigest,
	}
	child.RecordDigest = review.ComputeRecordDigest(child)
	return parent, child
}

func TestReviewVerifyChainHappy(t *testing.T) {
	dir := t.TempDir()
	parentPath := filepath.Join(dir, "parent.json")
	childPath := filepath.Join(dir, "child.json")
	parent, child := consistentChainPair(t)
	writeChainReport(t, parentPath, parent)
	writeChainReport(t, childPath, child)
	if err := Run([]string{"review", "--verify-chain", parentPath, childPath}); err != nil {
		t.Fatalf("want exit 0, got %v (code %d)", err, ExitCode(err))
	}
}

// FG-07: forged reports that copy a parent-supplied digest string must not pass.
func TestReviewVerifyChainRejectsFabricatedDigests(t *testing.T) {
	dir := t.TempDir()
	parentPath := filepath.Join(dir, "parent.json")
	childPath := filepath.Join(dir, "child.json")
	forged := "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
	writeChainReport(t, parentPath, review.Report{
		Schema:         review.SchemaVersion,
		MethodVersion:  review.MethodVersion,
		ConfirmedCount: 1,
		RecordDigest:   forged,
	})
	writeChainReport(t, childPath, review.Report{
		Schema:             review.SchemaVersion,
		MethodVersion:      review.MethodVersion,
		ConfirmedCount:     2,
		RecordDigest:       forged,
		ParentRecordDigest: forged,
	})
	err := Run([]string{"review", "--verify-chain", parentPath, childPath})
	if ExitCode(err) != ExitGates {
		t.Fatalf("FG-07: fabricated digest chain must exit 1, got %d (%v)", ExitCode(err), err)
	}
}

func TestReviewVerifyChainTamper(t *testing.T) {
	dir := t.TempDir()
	parentPath := filepath.Join(dir, "parent.json")
	childPath := filepath.Join(dir, "child.json")
	parent, child := consistentChainPair(t)
	child.ParentRecordDigest = "tampered"
	child.RecordDigest = review.ComputeRecordDigest(child)
	writeChainReport(t, parentPath, parent)
	writeChainReport(t, childPath, child)
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
