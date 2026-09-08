package outwrite_test

import (
	"os"
	"path/filepath"
	"runtime"
	"testing"

	"github.com/afelin/curbpack/internal/outwrite"
)

func TestPublishUnwritableStagePreservesOldSet(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("Windows ACL test belongs to the native matrix")
	}
	root := t.TempDir()
	locked := filepath.Join(root, "unwritable")
	if err := os.Mkdir(locked, 0755); err != nil {
		t.Fatal(err)
	}
	first := filepath.Join(root, "artifact.txt")
	marker := filepath.Join(root, "manifest.json")
	for _, p := range []string{first, marker} {
		if err := os.WriteFile(p, []byte("old"), 0600); err != nil {
			t.Fatal(err)
		}
	}
	if err := os.Chmod(locked, 0500); err != nil {
		t.Fatal(err)
	}
	defer os.Chmod(locked, 0755)
	if f, err := os.CreateTemp(locked, "probe"); err == nil {
		f.Close()
		os.Remove(f.Name())
		t.Skip("runner bypasses directory write permissions")
	}
	err := outwrite.Publish([]outwrite.Artifact{{PermittedRoot: root, Path: first, Data: []byte("new")}, {PermittedRoot: root, Path: filepath.Join(locked, "blocked.txt"), Data: []byte("new")}, {PermittedRoot: root, Path: marker, Data: []byte("new")}})
	if err == nil {
		t.Fatal("unwritable staging accepted")
	}
	for _, p := range []string{first, marker} {
		raw, err := os.ReadFile(p)
		if err != nil || string(raw) != "old" {
			t.Fatalf("previous set changed: %s %v", raw, err)
		}
	}
	tmp, err := filepath.Glob(filepath.Join(root, ".curbpack-out-*.tmp"))
	if err != nil || len(tmp) > 0 {
		t.Fatalf("staged files leaked: %v %v", tmp, err)
	}
}
