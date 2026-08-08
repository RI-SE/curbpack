package formhints_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/afelin/cyberready/internal/formhints"
)

// TestDebugGitWrite proves ApplyStubs currently allows writes under .git/ (H5).
func TestDebugGitWrite(t *testing.T) {
	dir := t.TempDir()
	_ = os.MkdirAll(filepath.Join(dir, ".git", "hooks"), 0o755)
	out, err := formhints.ApplyStubs(dir, []formhints.Hint{{
		GateID:  "X",
		File:    ".git/hooks/pre-commit",
		Snippet: "#!/bin/sh\necho pwned\n",
	}})
	if err != nil {
		t.Fatalf("safeRelPath refused .git (unexpected for current bug): %v", err)
	}
	if !out[0].Applied {
		t.Fatal("expected write under .git to be applied (bug present)")
	}
	b, err := os.ReadFile(filepath.Join(dir, ".git", "hooks", "pre-commit"))
	if err != nil {
		t.Fatal(err)
	}
	if string(b) == "" {
		t.Fatal("empty write")
	}
}
