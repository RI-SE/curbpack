package sbom_test

import (
	"github.com/afelin/curbpack/internal/sbom"
	"os"
	"path/filepath"
	"testing"
)

func TestDefaultEvidenceRefusesOutsideSymlink(t *testing.T) {
	root := t.TempDir()
	if err := os.WriteFile(filepath.Join(root, "go.mod"), []byte("module fixture\ngo 1.23\n"), 0600); err != nil {
		t.Fatal(err)
	}
	outside := filepath.Join(t.TempDir(), "sentinel")
	if err := os.WriteFile(outside, []byte("preserve"), 0600); err != nil {
		t.Fatal(err)
	}
	evidence := filepath.Join(root, ".github", "curbpack", "evidence")
	if err := os.MkdirAll(evidence, 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(outside, filepath.Join(evidence, "sbom.cdx.json")); err != nil {
		t.Skip(err)
	}
	_, _, err := sbom.WriteCycloneDX(root, "")
	if err == nil {
		t.Fatal("outside destination accepted")
	}
	b, err := os.ReadFile(outside)
	if err != nil || string(b) != "preserve" {
		t.Fatalf("outside file changed: %q (%v)", b, err)
	}
}
