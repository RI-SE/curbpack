package cli

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/attest"
	"github.com/afelin/curbpack/internal/gitutil"
)

func TestShareLadderLines_stale(t *testing.T) {
	dir := t.TempDir()
	_ = os.MkdirAll(filepath.Join(dir, "review-pack"), 0o755)
	_ = os.WriteFile(filepath.Join(dir, "review-pack", "buyer-onepager.html"), []byte("<!-- curbpack-onepager-fp:deadbeef -->"), 0o644)
	cache := filepath.Join(dir, ".github", "curbpack", "cache")
	_ = os.MkdirAll(cache, 0o755)
	_ = os.WriteFile(filepath.Join(cache, "latest_result.json"), []byte(`{"schema_version":"1","pack_id":"house-policy","readiness_score":80}`), 0o644)
	lines := shareLadderLines(dir, 80, true)
	if len(lines) == 0 || !strings.HasPrefix(lines[0], "share_stale:") {
		t.Fatalf("want share_stale first, got %v", lines)
	}
}

func TestShareLadderLines_attestBehind(t *testing.T) {
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
	run("git", "config", "user.email", "share@curbpack.local")
	run("git", "config", "user.name", "Share")
	run("git", "commit", "--allow-empty", "-m", "one", "-q")
	head1, err := gitutil.HeadSHA(dir)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := attest.Run(attest.Options{RepoRoot: dir, AllowDirty: true}); err != nil {
		t.Fatal(err)
	}
	run("git", "commit", "--allow-empty", "-m", "two", "-q")
	lines := shareLadderLines(dir, 80, true)
	found := false
	for _, line := range lines {
		if strings.HasPrefix(line, "attest_commit_behind:") && strings.Contains(line, head1[:8]) {
			found = true
		}
	}
	if !found {
		t.Fatalf("want attest_commit_behind mentioning bind, got %v", lines)
	}
}
