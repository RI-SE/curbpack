package cli_test

import (
	"bytes"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

type healPayload struct {
	ReadinessScore int `json:"readiness_score"`
	Failures       []struct {
		GateID string `json:"gate_id"`
	} `json:"failures"`
}

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

func TestCheckJSONHealMatchesImmediatePlainCheck(t *testing.T) {
	dir := t.TempDir()
	initGit(t, dir)
	bin := buildCLI(t)
	config := []byte("{\"packs\":[\"house-policy\"],\"version\":\"0.4.3\",\"hooks\":false}\n")
	if err := os.WriteFile(filepath.Join(dir, ".curbpack.json"), config, 0o644); err != nil {
		t.Fatal(err)
	}

	healCmd := exec.Command(bin, "check", "--json", "--heal")
	healCmd.Dir = dir
	healOut, healErr := healCmd.CombinedOutput()
	if exitCode(healErr) != 1 {
		t.Fatalf("check --json --heal exit = %d, want 1\n%s", exitCode(healErr), healOut)
	}
	heal := decodeHealPayload(t, healOut)
	assertGeneratedStubFailures(t, heal)

	for _, name := range []string{"latest_failure.json", "latest_result.json"} {
		body, err := os.ReadFile(filepath.Join(dir, ".github", "curbpack", "cache", name))
		if err != nil {
			t.Fatalf("read %s: %v", name, err)
		}
		cached := decodeHealPayload(t, body)
		assertGeneratedStubFailures(t, cached)
	}

	exportCmd := exec.Command(bin, "export", "--context-pack")
	exportCmd.Dir = dir
	if out, err := exportCmd.CombinedOutput(); err != nil {
		t.Fatalf("export context pack: %v\n%s", err, out)
	}
	contextBody, err := os.ReadFile(filepath.Join(dir, ".github", "curbpack", "cache", "context-pack.json"))
	if err != nil {
		t.Fatalf("read context pack: %v", err)
	}
	contextPayload := decodeHealPayload(t, contextBody)
	assertGeneratedStubFailures(t, contextPayload)

	plainCmd := exec.Command(bin, "check", "--json")
	plainCmd.Dir = dir
	plainOut, plainErr := plainCmd.CombinedOutput()
	if exitCode(plainErr) != 1 {
		t.Fatalf("immediate plain check exit = %d, want 1\n%s", exitCode(plainErr), plainOut)
	}
	if !bytes.Equal(healOut, plainOut) {
		t.Fatalf("heal and immediate plain JSON differ\nheal:\n%s\nplain:\n%s", healOut, plainOut)
	}
}

func decodeHealPayload(t *testing.T, body []byte) healPayload {
	t.Helper()
	var payload healPayload
	if err := json.Unmarshal(body, &payload); err != nil {
		t.Fatalf("decode payload: %v\n%s", err, body)
	}
	return payload
}

func assertGeneratedStubFailures(t *testing.T, payload healPayload) {
	t.Helper()
	if payload.ReadinessScore != 60 {
		t.Fatalf("readiness_score = %d, want 60", payload.ReadinessScore)
	}
	if len(payload.Failures) != 2 {
		t.Fatalf("failures = %d, want 2: %#v", len(payload.Failures), payload.Failures)
	}
	for _, failure := range payload.Failures {
		if failure.GateID != "HOUSE-ANTI-PLACEHOLDER" {
			t.Fatalf("gate_id = %q, want HOUSE-ANTI-PLACEHOLDER", failure.GateID)
		}
	}
}

func exitCode(err error) int {
	if err == nil {
		return 0
	}
	if exitErr, ok := err.(*exec.ExitError); ok {
		return exitErr.ExitCode()
	}
	return -1
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
