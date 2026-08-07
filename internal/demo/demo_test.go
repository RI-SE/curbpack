package demo

import (
	"os"
	"path/filepath"
	"testing"
)

func TestCopyEmbedded(t *testing.T) {
	dir := t.TempDir()
	if err := copyEmbedded(dir); err != nil {
		t.Fatal(err)
	}
	for _, rel := range []string{"SECURITY.md", ".well-known/security.txt", "README.md"} {
		if _, err := os.Stat(filepath.Join(dir, rel)); err != nil {
			t.Fatalf("missing %s: %v", rel, err)
		}
	}
}

func TestRunSandbox(t *testing.T) {
	dir := t.TempDir()
	if err := Run(Options{OutDir: dir, KeepDir: true, Version: "test"}); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(dir, "review-pack", "buyer-onepager.html")); err != nil {
		t.Fatalf("onepager: %v", err)
	}
	if _, err := os.Stat(filepath.Join(dir, ".cyberready.json")); err != nil {
		t.Fatalf("config: %v", err)
	}
}
