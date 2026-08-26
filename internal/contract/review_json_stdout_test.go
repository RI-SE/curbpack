package contract_test

import (
	"encoding/json"
	"os/exec"
	"path/filepath"
	"testing"
)

// TestReviewJSONStdoutParses locks W1: review --json must emit parseable JSON on
// stdout alone (no tty.PrintHeader pollution). Combined-output goldens cannot catch this.
func TestReviewJSONStdoutParses(t *testing.T) {
	root := shipRepoRoot(t)
	bin := filepath.Join(t.TempDir(), "curbpack")
	cmd := exec.Command("go", "build", "-o", bin, "./cmd/curbpack")
	cmd.Dir = root
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("go build: %v\n%s", err, out)
	}

	pack := filepath.Join(root, "testdata", "sample-review-pack")
	run := exec.Command(bin, "review", pack, "--json")
	stdout, err := run.Output()
	if err != nil {
		// Contradictions exit 1 but still emit JSON on stdout — only fail on empty/corrupt stdout.
		if ee, ok := err.(*exec.ExitError); ok {
			if len(stdout) == 0 {
				t.Fatalf("review --json: exit %d with empty stdout\nstderr=%s", ee.ExitCode(), ee.Stderr)
			}
		} else {
			t.Fatal(err)
		}
	}
	var m map[string]any
	if err := json.Unmarshal(stdout, &m); err != nil {
		t.Fatalf("stdout must be pure JSON: %v\nfirst 200 bytes: %q", err, truncateBytes(stdout, 200))
	}
	if m["schema"] == nil {
		t.Fatalf("expected schema field in report: %v", m)
	}
}

func truncateBytes(b []byte, n int) []byte {
	if len(b) <= n {
		return b
	}
	return b[:n]
}
