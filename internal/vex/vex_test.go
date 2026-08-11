package vex_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/vex"
)

func TestPendingOpenVEX(t *testing.T) {
	payload := ir.GateFailurePayload{
		Failures: []ir.Failure{{
			GateID:               "HOUSE-DEP-AXIOS-PIN",
			SanitizedDescription: "banned pin",
			Remediation:          ir.Remediation{ActionRequired: "upgrade"},
		}},
	}
	doc := vex.FromGateFailures("demo", payload)
	if doc.Status != "draft_pending_attest" {
		t.Fatalf("status=%s", doc.Status)
	}
	if len(doc.Statements) != 1 {
		t.Fatal("expected one statement")
	}
	if doc.Digest == "" || doc.GateDigest == "" {
		t.Fatal("missing digests")
	}
	dir := t.TempDir()
	path, err := vex.Write(dir, doc, "")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(path); err != nil {
		t.Fatal(err)
	}
	if filepath.Base(path) != "vex-pending.json" {
		t.Fatalf("path=%s", path)
	}
}
