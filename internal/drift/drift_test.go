package drift_test

import (
	"bytes"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/attest"
	"github.com/afelin/curbpack/internal/drift"
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
	run("git", "config", "user.email", "drift@curbpack.local")
	run("git", "config", "user.name", "Drift")
	run("git", "commit", "--allow-empty", "-m", "init", "-q")
}

func TestDrift_never_boolean_summary(t *testing.T) {
	dir := t.TempDir()
	initRepo(t, dir)
	var buf bytes.Buffer
	if err := drift.Run(drift.Options{RepoRoot: dir, JSONOut: true, Writer: &buf}); err != nil {
		t.Fatal(err)
	}
	var report drift.Report
	if err := json.Unmarshal(buf.Bytes(), &report); err != nil {
		t.Fatal(err)
	}
	if drift.ContainsForbiddenSummary(report) {
		t.Fatal("drift report contains forbidden boolean summary fields")
	}
	for _, f := range drift.ForbiddenSummaryFields {
		if strings.Contains(buf.String(), `"`+f+`"`) {
			t.Fatalf("forbidden field %q in output", f)
		}
	}
}

func TestDrift_attest_commit_behind(t *testing.T) {
	dir := t.TempDir()
	initRepo(t, dir)
	head1, _ := gitutil.HeadSHA(dir)
	cap := attest.Capsule{CommitSHA: head1, StateHash: "h1", Signer: "local-unsigned", UserTouch: "not-verified"}
	body, _ := json.Marshal(cap)
	_ = gitutil.NotesAdd(dir, head1, string(body))
	evidence := filepath.Join(dir, ".github", "curbpack", "evidence")
	_ = os.MkdirAll(evidence, 0o755)
	ptr := map[string]string{"state_hash": "h1", "commit_sha": head1}
	pb, _ := json.Marshal(ptr)
	_ = os.WriteFile(filepath.Join(evidence, "hpurl-pointer.json"), pb, 0o644)

	cmd := exec.Command("git", "commit", "--allow-empty", "-m", "after", "-q")
	cmd.Dir = dir
	cmd.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
	_ = cmd.Run()

	var buf bytes.Buffer
	_ = drift.Run(drift.Options{RepoRoot: dir, JSONOut: true, Writer: &buf})
	var report drift.Report
	_ = json.Unmarshal(buf.Bytes(), &report)
	found := false
	for _, s := range report.Signals {
		if s.ID == "attest_commit_behind" {
			found = true
		}
	}
	if !found {
		t.Fatalf("want attest_commit_behind in %v", report.Signals)
	}
}

func TestDrift_attest_none(t *testing.T) {
	dir := t.TempDir()
	initRepo(t, dir)
	var buf bytes.Buffer
	_ = drift.Run(drift.Options{RepoRoot: dir, JSONOut: true, Writer: &buf})
	if !strings.Contains(buf.String(), "attest_none") {
		t.Fatalf("want attest_none: %s", buf.String())
	}
}
