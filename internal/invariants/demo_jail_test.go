package invariants_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/afelin/cyberready/internal/demo"
)

func TestDemoRefusesProductCwd(t *testing.T) {
	cwd, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	err = demo.Run(demo.Options{OutDir: cwd, KeepDir: true, Version: "test"})
	if err == nil {
		t.Fatal("demo must refuse --out equal to product cwd")
	}
}

func TestDemoRefusesPathUnderCwd(t *testing.T) {
	sub := filepath.Join(t.TempDir(), "nested") // may not be under cwd
	// Create a dir under the real cwd.
	jail := filepath.Join(".", ".cyberready-demo-jail-test")
	_ = os.RemoveAll(jail)
	if err := os.MkdirAll(jail, 0o755); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = os.RemoveAll(jail) })
	err := demo.Run(demo.Options{OutDir: jail, KeepDir: true, Version: "test"})
	if err == nil {
		t.Fatal("demo must refuse --out under product cwd")
	}
	_ = sub
}

func TestDemoSandboxDoesNotTouchCwdMarker(t *testing.T) {
	cwd, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	marker := filepath.Join(cwd, ".cyberready-invariants-marker")
	if err := os.WriteFile(marker, []byte("keep\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = os.Remove(marker) })

	out := t.TempDir()
	if err := demo.Run(demo.Options{OutDir: out, KeepDir: true, Version: "test"}); err != nil {
		t.Fatal(err)
	}
	b, err := os.ReadFile(marker)
	if err != nil || string(b) != "keep\n" {
		t.Fatalf("product cwd marker mutated: %v %q", err, b)
	}
	if _, err := os.Stat(filepath.Join(out, ".cyberready.json")); err != nil {
		t.Fatal(err)
	}
}
