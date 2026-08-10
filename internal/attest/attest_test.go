package attest_test

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/cyberready/internal/attest"
)

func TestReproducibleStateHash(t *testing.T) {
	a := attest.ComputeStateHash("abc", "parent", "sbom1", "vex1")
	b := attest.ComputeStateHash("abc", "parent", "sbom1", "vex1")
	if a != b {
		t.Fatal("state hash must be reproducible")
	}
	c := attest.ComputeStateHash("abc", "parent", "sbom2", "vex1")
	if a == c {
		t.Fatal("sbom digest must affect hash")
	}
	seed := attest.StateSeed("abc", "parent", "sbom1", "vex1")
	if seed != "abc|parent|sbom=sbom1|vex=vex1" {
		t.Fatalf("seed=%q", seed)
	}
}

func TestAttestRefusesDirtyWithoutAllowDirty(t *testing.T) {
	dir := t.TempDir()
	run := func(args ...string) {
		t.Helper()
		cmd := exec.Command(args[0], args[1:]...)
		cmd.Dir = dir
		cmd.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
		if out, err := cmd.CombinedOutput(); err != nil {
			t.Fatalf("%v: %s", err, out)
		}
	}
	run("git", "init", "-q")
	run("git", "config", "user.email", "attest@cyberready.local")
	run("git", "config", "user.name", "Attest")
	run("git", "commit", "--allow-empty", "-m", "init", "-q")
	if err := os.WriteFile(filepath.Join(dir, "dirty.txt"), []byte("uncommitted\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	_, err := attest.Run(attest.Options{RepoRoot: dir, AllowDirty: false})
	if err == nil || !strings.Contains(err.Error(), "OCC conflict") {
		t.Fatalf("want OCC conflict without --allow-dirty, got %v", err)
	}
	if _, err := attest.Run(attest.Options{RepoRoot: dir, AllowDirty: true}); err != nil {
		t.Fatalf("--allow-dirty must proceed: %v", err)
	}
}
