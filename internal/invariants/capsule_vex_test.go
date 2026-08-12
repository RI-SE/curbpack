package invariants_test

import (
	"os"
	"path/filepath"
	"runtime"
	"testing"

	"github.com/afelin/curbpack/internal/attest"
	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/validate"
	"github.com/afelin/curbpack/internal/vex"
)

func TestCapsuleHashReproducibleNoWallClock(t *testing.T) {
	a := attest.ComputeStateHash("c1", "p1", "sbom", "vex")
	b := attest.ComputeStateHash("c1", "p1", "sbom", "vex")
	if a != b {
		t.Fatal("state_hash must ignore wall clock")
	}
	// Boundary fields must not collide under length-prefixed hashing.
	if attest.ComputeStateHash("a", "b", "c|d", "e") == attest.ComputeStateHash("a|b", "c", "d", "e") {
		t.Fatal("length-prefixed state_hash must reject delimiter ambiguity")
	}
}

func TestHealVEXStaysDraft(t *testing.T) {
	payload := ir.GateFailurePayload{
		Failures: []ir.Failure{{
			GateID:               "HOUSE-SECURITY-MD",
			Severity:             "high",
			Type:                 "MISSING",
			SanitizedDescription: "missing",
		}},
	}
	doc := vex.FromGateFailures("app", payload)
	if doc.Status != "draft_pending_attest" {
		t.Fatalf("status=%q want draft_pending_attest", doc.Status)
	}
	for _, s := range doc.Statements {
		if s.Status != "under_investigation" {
			t.Fatalf("statement status=%q", s.Status)
		}
	}
}

func TestPathTraversalFailClosed(t *testing.T) {
	dir := t.TempDir()
	if err := os.MkdirAll(filepath.Join(dir, ".git"), 0o755); err != nil {
		t.Fatal(err)
	}
	// Adversarial pack path is covered in validate tests; assert SafeJoin export.
	_, _, err := validate.SafeJoin(dir, "../etc/passwd")
	if err == nil {
		t.Fatal("expected traversal refuse")
	}
	// On Windows, "/etc/passwd" is not filepath.IsAbs — use a real abs probe.
	absProbe := "/etc/passwd"
	if runtime.GOOS == "windows" {
		absProbe = `C:\Windows\System32\drivers\etc\hosts`
	}
	_, _, err = validate.SafeJoin(dir, absProbe)
	if err == nil {
		t.Fatal("expected abs refuse")
	}
	full, rel, err := validate.SafeJoin(dir, "docs/a.md")
	if err != nil {
		t.Fatal(err)
	}
	if rel != "docs/a.md" {
		t.Fatalf("rel=%q", rel)
	}
	if filepath.Dir(full) != filepath.Join(dir, "docs") {
		t.Fatalf("full=%q", full)
	}
}
