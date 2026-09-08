package vex_test

import (
	"github.com/afelin/curbpack/internal/vex"
	"os"
	"path/filepath"
	"testing"
)

func TestDefaultEvidenceRefusesOutsideSymlink(t *testing.T) {
	root := t.TempDir()

	outside := filepath.Join(t.TempDir(), "sentinel")
	if err := os.WriteFile(outside, []byte("preserve"), 0600); err != nil {
		t.Fatal(err)
	}
	evidence := filepath.Join(root, ".github", "curbpack", "evidence")
	if err := os.MkdirAll(evidence, 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(outside, filepath.Join(evidence, "vex-pending.json")); err != nil {
		t.Skip(err)
	}
	_, err := vex.Write(root, vex.Document{}, "")
	if err == nil {
		t.Fatal("outside destination accepted")
	}
	b, err := os.ReadFile(outside)
	if err != nil || string(b) != "preserve" {
		t.Fatalf("outside file changed: %q (%v)", b, err)
	}
}
