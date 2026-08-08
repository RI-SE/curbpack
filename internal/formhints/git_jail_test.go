package formhints_test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/cyberready/internal/formhints"
)

func TestApplyStubsRefusesDotGit(t *testing.T) {
	dir := t.TempDir()
	_ = os.MkdirAll(filepath.Join(dir, ".git", "hooks"), 0o755)
	_, err := formhints.ApplyStubs(dir, []formhints.Hint{{
		GateID:  "X",
		File:    ".git/hooks/pre-commit",
		Snippet: "#!/bin/sh\necho pwned\n",
	}})
	if err == nil {
		t.Fatal("expected refuse write under .git")
	}
	if !strings.Contains(err.Error(), ".git") {
		t.Fatalf("unexpected err: %v", err)
	}
	if _, err := os.Stat(filepath.Join(dir, ".git", "hooks", "pre-commit")); err == nil {
		t.Fatal("must not create .git/hooks/pre-commit")
	}
}
