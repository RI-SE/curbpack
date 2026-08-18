package attest_test

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/attest"
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
}

func TestStateHashFieldBoundaryCollision(t *testing.T) {
	// Pipe (or other delimiter) ambiguity must not collide under length-prefixing.
	pairs := [][2][4]string{
		{
			{"a", "b", "c|d", "e"},
			{"a|b", "c", "d", "e"},
		},
		{
			{"ab", "c", "d", "e"},
			{"a", "bc", "d", "e"},
		},
		{
			{"", "x", "y", "z"},
			{"x", "", "y", "z"},
		},
		{
			{"commit", "parent", "sbom=x", "vex"},
			{"commit", "parent", "sbom", "=xvex"},
		},
	}
	for i, p := range pairs {
		left := attest.ComputeStateHash(p[0][0], p[0][1], p[0][2], p[0][3])
		right := attest.ComputeStateHash(p[1][0], p[1][1], p[1][2], p[1][3])
		if left == right {
			t.Fatalf("pair %d: boundary inputs must not collide: %q vs %q → %s", i, p[0], p[1], left)
		}
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
	run("git", "config", "user.email", "attest@curbpack.local")
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

func TestReviewedByEvidenceNotInStateHash(t *testing.T) {
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
	run("git", "config", "user.email", "attest@curbpack.local")
	run("git", "config", "user.name", "Attest")
	run("git", "commit", "--allow-empty", "-m", "init", "-q")

	cap, err := attest.Run(attest.Options{RepoRoot: dir, AllowDirty: true, ReviewedBy: "Ada Reviewer"})
	if err != nil {
		t.Fatal(err)
	}
	if cap.Evidence["reviewed_by"] != "Ada Reviewer" {
		t.Fatalf("evidence reviewed_by=%q", cap.Evidence["reviewed_by"])
	}
	want := attest.ComputeStateHash(cap.CommitSHA, cap.ParentStateHash, cap.Evidence["sbom_digest"], cap.Evidence["vex_digest"])
	if cap.StateHash != want {
		t.Fatalf("reviewed-by must not enter state_hash: got %s want %s", cap.StateHash, want)
	}
	bind, err := attest.LatestBind(dir)
	if err != nil {
		t.Fatal(err)
	}
	if bind.ReviewedBy != "Ada Reviewer" {
		t.Fatalf("bind ReviewedBy=%q", bind.ReviewedBy)
	}
}

func TestAgentIdentityEnvNotInStateHash(t *testing.T) {
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
	run("git", "config", "user.email", "attest@curbpack.local")
	run("git", "config", "user.name", "Attest")
	run("git", "commit", "--allow-empty", "-m", "init", "-q")

	t.Setenv("CURBPACK_AGENT_ID", "agent-a")
	t.Setenv("CURBPACK_MODEL_HASH", "hash-a")
	t.Setenv("CURBPACK_MANDATE_ID", "mandate-a")
	capA, err := attest.Run(attest.Options{RepoRoot: dir, AllowDirty: true})
	if err != nil {
		t.Fatal(err)
	}
	t.Setenv("CURBPACK_AGENT_ID", "agent-b")
	t.Setenv("CURBPACK_MODEL_HASH", "hash-b")
	t.Setenv("CURBPACK_MANDATE_ID", "mandate-b")
	capB, err := attest.Run(attest.Options{RepoRoot: dir, AllowDirty: true})
	if err != nil {
		t.Fatal(err)
	}
	if capA.StateHash != capB.StateHash {
		t.Fatalf("AgentIdentity env must not enter state_hash: %s vs %s", capA.StateHash, capB.StateHash)
	}
	want := attest.ComputeStateHash(capA.CommitSHA, capA.ParentStateHash, capA.Evidence["sbom_digest"], capA.Evidence["vex_digest"])
	if capA.StateHash != want {
		t.Fatalf("state_hash drifted from frozen field order: got %s want %s", capA.StateHash, want)
	}
}
