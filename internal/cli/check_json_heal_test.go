package cli_test

import (
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

func TestCheckJSONHealValidJSON(t *testing.T) {
	dir := t.TempDir()
	initGit(t, dir)
	bin := buildCLI(t)

	initCmd := exec.Command(bin, "init", "--packs", "house-policy")
	initCmd.Dir = dir
	out, err := initCmd.CombinedOutput()
	if err != nil {
		t.Fatalf("init: %v %s", err, out)
	}

	checkCmd := exec.Command(bin, "check", "--json", "--heal")
	checkCmd.Dir = dir
	out, err = checkCmd.CombinedOutput()
	if err == nil {
		// red init stubs expected
	}
	text := string(out)
	if strings.Contains(text, "## Form hints") {
		t.Fatalf("--json --heal must not emit form hints markdown:\n%s", text)
	}
	var payload map[string]any
	if err := json.Unmarshal(out, &payload); err != nil {
		t.Fatalf("stdout must be valid JSON only: %v\n%s", err, text)
	}
}

// Init stubs leave only not-started/scaffold/absent findings — no ✘, no readiness=%, still exit 1.
func TestCheckScoreStubOnlyNoReadiness(t *testing.T) {
	dir := t.TempDir()
	initGit(t, dir)
	bin := buildCLI(t)

	initCmd := exec.Command(bin, "init", "--packs", "house-policy", "--bare")
	initCmd.Dir = dir
	if out, err := initCmd.CombinedOutput(); err != nil {
		t.Fatalf("init: %v %s", err, out)
	}

	checkCmd := exec.Command(bin, "check", "--score")
	checkCmd.Dir = dir
	out, err := checkCmd.CombinedOutput()
	text := string(out)
	if err == nil {
		t.Fatalf("stub-only check must exit non-zero (Passed false), got success:\n%s", text)
	}
	if strings.Contains(text, "✘") {
		t.Fatalf("stub-only overlap must not print ✘: %q", text)
	}
	if strings.Contains(text, "readiness=") {
		t.Fatalf("stub-only findings must omit readiness=%%: %q", text)
	}
	if !strings.Contains(text, "○") {
		t.Fatalf("stub-only findings should print ○ not-started lines: %q", text)
	}
}

func initGit(t *testing.T, dir string) {
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
	run("git", "config", "user.email", "cli@curbpack.local")
	run("git", "config", "user.name", "CLI")
	run("git", "commit", "--allow-empty", "-m", "init", "-q")
}

func buildCLI(t *testing.T) string {
	t.Helper()
	bin := filepath.Join(t.TempDir(), "curbpack")
	if runtime.GOOS == "windows" {
		bin += ".exe"
	}
	wd, _ := os.Getwd()
	root := filepath.Clean(filepath.Join(wd, "../.."))
	out, err := exec.Command("go", "build", "-o", bin, filepath.Join(root, "cmd/curbpack")).CombinedOutput()
	if err != nil {
		t.Fatalf("build: %v %s", err, out)
	}
	_ = root
	return bin
}
