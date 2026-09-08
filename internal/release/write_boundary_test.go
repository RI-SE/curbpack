package release_test

import (
	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/validate"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/release"
)

func TestPrepareRefusesVEXEscapeWithoutChangingOutsideFile(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "1704067200")
	root := t.TempDir()
	initPassingHouse(t, root)
	outside := filepath.Join(t.TempDir(), "sentinel.json")
	if err := os.WriteFile(outside, []byte("preserve me"), 0600); err != nil {
		t.Fatal(err)
	}
	evidence := filepath.Join(root, ".github", "curbpack", "evidence")
	if err := os.MkdirAll(evidence, 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(outside, filepath.Join(evidence, "vex-pending.json")); err != nil {
		t.Skip(err)
	}
	err := release.Prepare(release.Options{RepoRoot: root, PackIDs: []string{"house-policy"}, AllowFailingGates: true})
	b, readErr := os.ReadFile(outside)
	if readErr != nil || string(b) != "preserve me" {
		t.Fatalf("outside file changed: %q (%v)", b, readErr)
	}
	if err == nil {
		t.Fatal("unsafe VEX destination accepted")
	}
}

func TestPrepareReportsSkippedEvaluationWithoutPassClaim(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "1704067200")
	root := t.TempDir()
	initPassingHouse(t, root)
	result := validate.Result{SkippedRules: 2, Payload: ir.GateFailurePayload{SchemaVersion: "1", Outcome: ir.OutcomeIncomplete, SkippedRules: 2}}
	if err := release.Prepare(release.Options{RepoRoot: root, Result: &result, AllowFailingGates: true}); err != nil {
		t.Fatal(err)
	}
	b, err := os.ReadFile(filepath.Join(root, "review-pack", "02-action-report.md"))
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(b), "Evaluation incomplete") || !strings.Contains(string(b), "0 / 0 / 2") || strings.Contains(string(b), "ALL GATES PASSED") {
		t.Fatalf("skips were misrepresented: %s", b)
	}
}
