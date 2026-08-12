package attest_test

import (
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"testing"

	"github.com/afelin/curbpack/internal/attest"
	"github.com/afelin/curbpack/internal/gitutil"
)

func initRepo(t *testing.T, dir string) {
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
	run("git", "config", "user.email", "bind@curbpack.local")
	run("git", "config", "user.name", "Bind")
	run("git", "commit", "--allow-empty", "-m", "init", "-q")
}

func TestLatestBind_none(t *testing.T) {
	dir := t.TempDir()
	initRepo(t, dir)
	bind, err := attest.LatestBind(dir)
	if err != nil {
		t.Fatal(err)
	}
	if bind.Found {
		t.Fatal("want Found=false with no attest")
	}
}

func TestLatestBind_hpurl_pointer(t *testing.T) {
	dir := t.TempDir()
	initRepo(t, dir)
	head, _ := gitutil.HeadSHA(dir)
	cap := attest.Capsule{
		SchemaVersion: "v3.33-OCC",
		CommitSHA:     head,
		StateHash:     "state-from-note",
		Signer:        "local-unsigned",
		UserTouch:     "not-verified",
	}
	body, _ := json.Marshal(cap)
	if err := gitutil.NotesAdd(dir, head, string(body)); err != nil {
		t.Fatal(err)
	}
	evidence := filepath.Join(dir, ".github", "curbpack", "evidence")
	_ = os.MkdirAll(evidence, 0o755)
	ptr := map[string]string{
		"state_hash": "state-from-note",
		"commit_sha": head,
	}
	pb, _ := json.MarshalIndent(ptr, "", "  ")
	_ = os.WriteFile(filepath.Join(evidence, "hpurl-pointer.json"), pb, 0o644)

	bind, err := attest.LatestBind(dir)
	if err != nil {
		t.Fatal(err)
	}
	if !bind.Found || bind.Source != "hpurl-pointer" {
		t.Fatalf("want hpurl-pointer bind, got %+v", bind)
	}
	if bind.StateHash != "state-from-note" {
		t.Fatalf("state_hash = %q", bind.StateHash)
	}
}

func TestLatestBind_post_commit_head_empty(t *testing.T) {
	dir := t.TempDir()
	initRepo(t, dir)
	head1, _ := gitutil.HeadSHA(dir)
	cap := attest.Capsule{CommitSHA: head1, StateHash: "bind1", Signer: "local-unsigned", UserTouch: "not-verified"}
	body, _ := json.Marshal(cap)
	_ = gitutil.NotesAdd(dir, head1, string(body))
	evidence := filepath.Join(dir, ".github", "curbpack", "evidence")
	_ = os.MkdirAll(evidence, 0o755)
	ptr := map[string]string{"state_hash": "bind1", "commit_sha": head1}
	pb, _ := json.Marshal(ptr)
	_ = os.WriteFile(filepath.Join(evidence, "hpurl-pointer.json"), pb, 0o644)

	cmd := exec.Command("git", "commit", "--allow-empty", "-m", "after-bind", "-q")
	cmd.Dir = dir
	cmd.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
	_ = cmd.Run()

	bind, err := attest.LatestBind(dir)
	if err != nil {
		t.Fatal(err)
	}
	if !bind.Found {
		t.Fatal("bind must survive new commit on HEAD")
	}
	if bind.CommitSHA != head1 {
		t.Fatalf("bind commit = %q want %q", bind.CommitSHA, head1)
	}
	head2, _ := gitutil.HeadSHA(dir)
	if bind.CommitSHA == head2 {
		t.Fatal("bind should be prior commit, not new HEAD without re-attest")
	}
}

func TestLatestBind_git_notes_fallback(t *testing.T) {
	dir := t.TempDir()
	initRepo(t, dir)
	head, _ := gitutil.HeadSHA(dir)
	cap := attest.Capsule{CommitSHA: head, StateHash: "notes-only", Signer: "local-unsigned", UserTouch: "not-verified"}
	body, _ := json.Marshal(cap)
	if err := gitutil.NotesAdd(dir, head, string(body)); err != nil {
		t.Fatal(err)
	}
	// No hpurl-pointer.json — must fall back to git log notes.
	bind, err := attest.LatestBind(dir)
	if err != nil {
		t.Fatal(err)
	}
	if !bind.Found || bind.Source != "git-notes" {
		t.Fatalf("want git-notes fallback, got %+v", bind)
	}
}
