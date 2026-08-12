package gitutil_test

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/gitutil"
)

func initGitRepo(t *testing.T, dir string) {
	t.Helper()
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
	run("git", "config", "user.email", "test@curbpack.local")
	run("git", "config", "user.name", "Test")
}

func TestHeadSHA_AuditMatrix(t *testing.T) {
	t.Run("empty_repo_returns_error_not_zeros", func(t *testing.T) {
		dir := t.TempDir()
		initGitRepo(t, dir)
		sha, err := gitutil.HeadSHA(dir)
		if err == nil {
			t.Fatalf("want error on empty repo, got sha=%q", sha)
		}
		if sha != "" {
			t.Fatalf("want empty sha on error, got %q", sha)
		}
		if strings.HasPrefix(sha, "0000000") {
			t.Fatal("must never return zero SHA with nil error")
		}
	})

	t.Run("committed_repo_returns_head", func(t *testing.T) {
		dir := t.TempDir()
		initGitRepo(t, dir)
		cmd := exec.Command("git", "commit", "--allow-empty", "-m", "init", "-q")
		cmd.Dir = dir
		cmd.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
		if out, err := cmd.CombinedOutput(); err != nil {
			t.Fatalf("%v: %s", err, out)
		}
		sha, err := gitutil.HeadSHA(dir)
		if err != nil {
			t.Fatal(err)
		}
		if len(sha) != 40 {
			t.Fatalf("want 40-char sha, got %q", sha)
		}
	})

	t.Run("non_git_dir_returns_error", func(t *testing.T) {
		dir := t.TempDir()
		sha, err := gitutil.HeadSHA(dir)
		if err == nil {
			t.Fatalf("want error, got %q", sha)
		}
		if sha != "" {
			t.Fatalf("want empty sha, got %q", sha)
		}
	})
}

func TestParentNoteHash_JSON(t *testing.T) {
	dir := t.TempDir()
	initGitRepo(t, dir)
	run := exec.Command("git", "commit", "--allow-empty", "-m", "c1", "-q")
	run.Dir = dir
	run.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
	_ = run.Run()
	head, _ := gitutil.HeadSHA(dir)
	note := `{"schema_version":"v3.33-OCC","state_hash":"abc123deadbeef","commit_sha":"` + head + `"}`
	if err := gitutil.NotesAdd(dir, head, note); err != nil {
		t.Fatal(err)
	}
	run2 := exec.Command("git", "commit", "--allow-empty", "-m", "c2", "-q")
	run2.Dir = dir
	run2.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
	_ = run2.Run()
	head2, _ := gitutil.HeadSHA(dir)
	got := gitutil.ParentNoteHash(dir, head2)
	if got != "abc123deadbeef" {
		t.Fatalf("ParentNoteHash = %q want abc123deadbeef", got)
	}
	_ = filepath.Join(dir) // keep import
}
