package review

import (
	"os"
	"path/filepath"
	"testing"
)

func TestDigestPathsSkippedCount(t *testing.T) {
	root := t.TempDir()
	okPath := filepath.Join(root, "ok.txt")
	if err := os.WriteFile(okPath, []byte("a"), 0o644); err != nil {
		t.Fatal(err)
	}
	badPath := filepath.Join(root, "bad.txt")
	if err := os.WriteFile(badPath, []byte("b"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.Chmod(badPath, 0o000); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = os.Chmod(badPath, 0o644) })

	_, _, skipped := digestPaths(root, []string{"ok.txt", "bad.txt"})
	if skipped != 1 {
		t.Fatalf("skipped=%d want 1", skipped)
	}
}
