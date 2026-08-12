package cli

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestEnsureCurbpackGitignore_create(t *testing.T) {
	dir := t.TempDir()
	added, err := ensureCurbpackGitignore(dir)
	if err != nil {
		t.Fatal(err)
	}
	if len(added) != 2 {
		t.Fatalf("want 2 added, got %v", added)
	}
	body, err := os.ReadFile(filepath.Join(dir, ".gitignore"))
	if err != nil {
		t.Fatal(err)
	}
	s := string(body)
	for _, e := range curbpackGitignoreEntries {
		if !strings.Contains(s, e+"\n") && !strings.HasSuffix(s, e) {
			t.Fatalf("missing %q in:\n%s", e, s)
		}
	}
}

func TestEnsureCurbpackGitignore_appendIdempotent(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, ".gitignore")
	if err := os.WriteFile(path, []byte("# keep me\n*.log\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	added, err := ensureCurbpackGitignore(dir)
	if err != nil {
		t.Fatal(err)
	}
	if len(added) != 2 {
		t.Fatalf("first pass want 2 added, got %v", added)
	}
	added2, err := ensureCurbpackGitignore(dir)
	if err != nil {
		t.Fatal(err)
	}
	if len(added2) != 0 {
		t.Fatalf("second pass must be idempotent, got %v", added2)
	}
	body, _ := os.ReadFile(path)
	s := string(body)
	if !strings.Contains(s, "# keep me") || !strings.Contains(s, "*.log") {
		t.Fatalf("clobbered unrelated entries:\n%s", s)
	}
	if strings.Count(s, ".github/curbpack/cache/") != 1 {
		t.Fatalf("cache entry duplicated:\n%s", s)
	}
}

func TestEnsureCurbpackGitignore_alreadyPresent(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, ".gitignore")
	seed := ".github/curbpack/cache/\n.github/curbpack/evidence/\n"
	if err := os.WriteFile(path, []byte(seed), 0o644); err != nil {
		t.Fatal(err)
	}
	added, err := ensureCurbpackGitignore(dir)
	if err != nil {
		t.Fatal(err)
	}
	if len(added) != 0 {
		t.Fatalf("want no adds, got %v", added)
	}
}
