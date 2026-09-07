package outwrite_test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/outwrite"
)

func TestDirDestDefaultRefusesSymlinkEscape(t *testing.T) {
	repo := t.TempDir()
	outside := t.TempDir()
	if err := os.Symlink(outside, filepath.Join(repo, "review-pack")); err != nil {
		t.Skip(err)
	}
	_, _, err := outwrite.DirDest(repo, "", "review-pack")
	if err == nil {
		t.Fatal("expected refuse")
	}
}

func TestDirDestExplicitIsOwnRoot(t *testing.T) {
	repo := t.TempDir()
	out := t.TempDir()
	permitted, dest, err := outwrite.DirDest(repo, out, "review-pack")
	if err != nil {
		t.Fatal(err)
	}
	if permitted != dest {
		t.Fatalf("explicit out should be its own root: permitted=%s dest=%s", permitted, dest)
	}
	if err := outwrite.WriteFile(permitted, filepath.Join(dest, "a.json"), []byte("{}\n"), 0o644); err != nil {
		t.Fatal(err)
	}
}

func TestWriteFileRefusesGitDest(t *testing.T) {
	repo := t.TempDir()
	if err := os.MkdirAll(filepath.Join(repo, ".git"), 0o755); err != nil {
		t.Fatal(err)
	}
	err := outwrite.WriteFile(repo, filepath.Join(repo, ".git", "config"), []byte("x"), 0o644)
	if err == nil || !strings.Contains(err.Error(), ".git") {
		t.Fatalf("expected .git refuse, got %v", err)
	}
}

func TestStageThenPublishLeavesNoTmp(t *testing.T) {
	dir := t.TempDir()
	dest := filepath.Join(dir, "out.json")
	if err := outwrite.WriteFile(dir, dest, []byte(`{"ok":true}`+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatal(err)
	}
	for _, e := range entries {
		if strings.Contains(e.Name(), ".tmp") {
			t.Fatalf("leftover temp: %s", e.Name())
		}
	}
}
