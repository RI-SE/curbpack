package cli_test

import (
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func TestBuiltCLIAsOfIsDataAndInvalidEpochFails(t *testing.T) {
	bin := buildCLI(t)
	root := t.TempDir()
	initGit(t, root)
	run := func(epoch, asOf string) ([]byte, error) {
		cmd := exec.Command(bin, "check", "--json", "--as-of", asOf)
		cmd.Dir = root
		env := []string{}
		for _, v := range os.Environ() {
			if !strings.HasPrefix(v, "SOURCE_DATE_EPOCH=") {
				env = append(env, v)
			}
		}
		if epoch != "unset" {
			env = append(env, "SOURCE_DATE_EPOCH="+epoch)
		}
		cmd.Env = env
		return cmd.CombinedOutput()
	}
	data, err := run("unset", "2024-01-02")
	if exitCode(err) != 1 {
		t.Fatalf("empty fixture should report findings: %v %s", err, data)
	}
	var result struct {
		AsOf   string `json:"as_of"`
		Digest string `json:"evaluation_digest"`
	}
	if err := json.Unmarshal(data, &result); err != nil {
		t.Fatal(err)
	}
	if result.AsOf != "2024-01-02T00:00:00Z" || len(result.Digest) != 64 {
		t.Fatalf("missing explicit identity: %s", data)
	}
	before, err := os.ReadFile(filepath.Join(root, ".github", "curbpack", "cache", "latest.json"))
	if err != nil {
		t.Fatal(err)
	}
	for _, epoch := range []string{"bad", "", "9223372036854775807"} {
		if out, err := run(epoch, "2024-01-02"); err == nil {
			t.Fatalf("invalid epoch %q accepted: %s", epoch, out)
		}
	}
	after, err := os.ReadFile(filepath.Join(root, ".github", "curbpack", "cache", "latest.json"))
	if err != nil || string(after) != string(before) {
		t.Fatal("invalid epoch changed cache pointer")
	}
}
