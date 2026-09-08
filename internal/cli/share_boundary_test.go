package cli

import (
	"os"
	"path/filepath"
	"testing"
)

func TestShareCopyRefusesDefaultDirectoryEscape(t *testing.T) {
	root := t.TempDir()
	outside := t.TempDir()
	src := filepath.Join(root, "context-pack.json")
	if err := os.WriteFile(src, []byte("new"), 0600); err != nil {
		t.Fatal(err)
	}
	target := filepath.Join(outside, "context-pack.json")
	if err := os.WriteFile(target, []byte("preserve"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(outside, filepath.Join(root, "review-pack")); err != nil {
		t.Skip(err)
	}
	if _, err := copyFileIntoReviewPack(root, src); err == nil {
		t.Fatal("share followed escaped directory")
	}
	got, err := os.ReadFile(target)
	if err != nil || string(got) != "preserve" {
		t.Fatalf("outside overwritten: %s %v", got, err)
	}
}
