package validate_test

import (
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"testing"

	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/validate"
)

// FG-05: --diff that skips rules must not write a complete-looking machine cache
// (high readiness_score / pass-shaped) without skip state and incomplete outcome.
func TestDiffSkipRecordsIncompleteInCache(t *testing.T) {
	dir := t.TempDir()
	mustRealGitValidate(t, dir)
	writeGoodHouse(t, dir)

	run := func(args ...string) {
		t.Helper()
		cmd := exec.Command(args[0], args[1:]...)
		cmd.Dir = dir
		cmd.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
		if out, err := cmd.CombinedOutput(); err != nil {
			t.Fatalf("%v: %s", err, out)
		}
	}
	run("git", "add", "-A")
	run("git", "commit", "-m", "base", "-q")
	// Touch a path outside HOUSE-SECRET-PATHS so text_forbid is skipped under --diff.
	mustWrite(t, filepath.Join(dir, "docs/notes.md"), "# notes\nuntouched-secret-paths skip\n")

	res, err := validate.Run(validate.Options{
		RepoRoot: dir,
		PackIDs:  []string{"house-policy"},
		DiffOnly: true,
		Quiet:    true,
	})
	if err != nil {
		t.Fatal(err)
	}
	if res.SkippedRules < 1 {
		t.Fatalf("expected at least one skipped rule under --diff, got %d failures=%v", res.SkippedRules, res.Payload.Failures)
	}

	cachePath := filepath.Join(dir, ".github", "curbpack", "cache", "latest_result.json")
	raw, err := os.ReadFile(cachePath)
	if err != nil {
		t.Fatalf("read cache: %v", err)
	}
	var cached ir.GateFailurePayload
	if err := json.Unmarshal(raw, &cached); err != nil {
		t.Fatalf("cache json: %v\n%s", err, raw)
	}
	if cached.SkippedRules < 1 {
		t.Fatalf("FG-05: machine cache must record skipped_rules, got %#v\n%s", cached, raw)
	}
	if cached.Outcome != ir.OutcomeIncomplete {
		t.Fatalf("FG-05: machine cache outcome=%q want %q\n%s", cached.Outcome, ir.OutcomeIncomplete, raw)
	}
	if res.Passed {
		t.Fatal("FG-05: skipped rules must not report Passed (incomplete must not be pass)")
	}
	if res.Payload.Outcome != ir.OutcomeIncomplete || res.Payload.SkippedRules < 1 {
		t.Fatalf("payload must carry incomplete + skips: %#v", res.Payload)
	}
}

func mustRealGitValidate(t *testing.T, dir string) {
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
	run("git", "config", "user.email", "validate@curbpack.local")
	run("git", "config", "user.name", "Validate")
	run("git", "commit", "--allow-empty", "-m", "init", "-q")
}
