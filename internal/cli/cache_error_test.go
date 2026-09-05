package cli_test

import (
	"bytes"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
)

func TestJSONCacheFailureIsOperationalError(t *testing.T) {
	dir := t.TempDir()
	initGit(t, dir)
	bin := buildCLI(t)
	cache := filepath.Join(dir, ".github", "curbpack", "cache", "latest_result.json")
	if err := os.MkdirAll(cache, 0755); err != nil {
		t.Fatal(err)
	}
	for _, verb := range []string{"check", "validate"} {
		cmd := exec.Command(bin, verb, "--json")
		cmd.Dir = dir
		var stdout, stderr bytes.Buffer
		cmd.Stdout = &stdout
		cmd.Stderr = &stderr
		err := cmd.Run()
		if exitCode(err) != 1 {
			t.Fatalf("%s: exit=%d stderr=%s", verb, exitCode(err), stderr.String())
		}
		var payload struct {
			Outcome string `json:"outcome"`
		}
		if err := json.Unmarshal(stdout.Bytes(), &payload); err != nil {
			t.Fatalf("%s: JSON: %v stdout=%s", verb, err, stdout.String())
		}
		if payload.Outcome != "error" {
			t.Fatalf("%s: outcome=%s", verb, payload.Outcome)
		}
	}
}
