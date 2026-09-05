package pathjail

import (
	"os"
	"path/filepath"
	"testing"
)

func TestExistingFileUnderSymlinkAncestorRefused(t *testing.T) {
	root := t.TempDir()
	outside := t.TempDir()
	if err := os.WriteFile(filepath.Join(outside, "file.md"), []byte("outside"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(outside, filepath.Join(root, "docs")); err != nil {
		t.Skip(err)
	}
	if _, _, err := Join(root, "docs/file.md"); err == nil {
		t.Fatal("existing file through escaping symlink ancestor accepted")
	}
}

func TestSymlinkAliasIntoGitRefused(t *testing.T) {
	root := t.TempDir()
	if err := os.Mkdir(filepath.Join(root, ".git"), 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(filepath.Join(root, ".git"), filepath.Join(root, "alias")); err != nil {
		t.Skip(err)
	}
	if _, _, err := Join(root, "alias/config"); err == nil {
		t.Fatal("symlink alias into .git accepted")
	}
}
