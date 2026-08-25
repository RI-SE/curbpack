package cli

import (
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestExpandBatchPaths_parentChildren(t *testing.T) {
	parent := t.TempDir()
	writeMinimalPack(t, filepath.Join(parent, "pack-a"))
	writeMinimalPack(t, filepath.Join(parent, "pack-b"))
	junk := filepath.Join(parent, "junk")
	if err := os.MkdirAll(junk, 0o755); err != nil {
		t.Fatal(err)
	}
	_ = os.WriteFile(filepath.Join(junk, "readme.txt"), []byte("nope\n"), 0o644)

	got := expandBatchPaths([]string{parent})
	if len(got) != 2 {
		t.Fatalf("want 2 pack children, got %d: %v", len(got), got)
	}
	bases := map[string]bool{}
	for _, p := range got {
		bases[filepath.Base(p)] = true
	}
	if !bases["pack-a"] || !bases["pack-b"] {
		t.Fatalf("want pack-a and pack-b, got %v", got)
	}
	if bases["junk"] {
		t.Fatal("junk dir must be ignored")
	}
}

func TestExpandBatchPaths_singlePack(t *testing.T) {
	dir := t.TempDir()
	pack := filepath.Join(dir, "one")
	writeMinimalPack(t, pack)
	got := expandBatchPaths([]string{pack})
	if len(got) != 1 || got[0] != filepath.Clean(pack) {
		t.Fatalf("pack dir must be single child, got %v", got)
	}
}

func TestCmdReviewBatch(t *testing.T) {
	parent := t.TempDir()
	writeMinimalPack(t, filepath.Join(parent, "alpha"))
	writeMinimalPack(t, filepath.Join(parent, "beta"))
	_ = os.MkdirAll(filepath.Join(parent, "noise"), 0o755)

	stdout, _ := captureReview(t, func() {
		err := Run([]string{"review", "--batch", parent})
		// Producer-unconfirmed optional layers are fine; contradictions exit gates.
		if err != nil && ExitCode(err) != ExitOK && ExitCode(err) != ExitGates {
			t.Fatalf("unexpected exit: %v code=%d", err, ExitCode(err))
		}
	})
	if !strings.Contains(stdout, "alpha") || !strings.Contains(stdout, "beta") {
		t.Fatalf("batch ranks must name both packs: %q", stdout)
	}
	if strings.Contains(stdout, "noise") {
		t.Fatalf("junk child must not appear: %q", stdout)
	}

	err := Run([]string{"review", "--batch", parent, "--full"})
	if ExitCode(err) != ExitUsage {
		t.Fatalf("--batch --full must usage-exit, got %d (%v)", ExitCode(err), err)
	}
	if err == nil || !strings.Contains(err.Error(), "batch prints rank lines only") {
		t.Fatalf("--batch --full message missing: %v", err)
	}
}

func writeMinimalPack(t *testing.T, dir string) {
	t.Helper()
	if err := os.MkdirAll(dir, 0o755); err != nil {
		t.Fatal(err)
	}
	payload := `{"schema_version":"1","pack_id":"house-policy","readiness_score":80}` + "\n"
	_ = os.WriteFile(filepath.Join(dir, "01-gate-failures.json"), []byte(payload), 0o644)
	_ = os.WriteFile(filepath.Join(dir, "02-action-report.md"), []byte("ok\n"), 0o644)
	_ = os.WriteFile(filepath.Join(dir, "03-executive-summary.md"), []byte("ok\n"), 0o644)
	_ = os.WriteFile(filepath.Join(dir, "buyer-onepager.html"), []byte(
		`<!-- curbpack-onepager-fp:aaaaaaaaaaaaaaaa --><dl class="prov"><dt>Rule packs</dt><dd>house-policy</dd></dl>`,
	), 0o644)
}

func captureReview(t *testing.T, fn func()) (stdout, stderr string) {
	t.Helper()
	oldOut, oldErr := os.Stdout, os.Stderr
	rOut, wOut, err := os.Pipe()
	if err != nil {
		t.Fatal(err)
	}
	rErr, wErr, err := os.Pipe()
	if err != nil {
		t.Fatal(err)
	}
	os.Stdout, os.Stderr = wOut, wErr
	defer func() {
		os.Stdout, os.Stderr = oldOut, oldErr
	}()
	doneOut := make(chan string)
	doneErr := make(chan string)
	go func() {
		b, _ := io.ReadAll(rOut)
		doneOut <- string(b)
	}()
	go func() {
		b, _ := io.ReadAll(rErr)
		doneErr <- string(b)
	}()
	fn()
	_ = wOut.Close()
	_ = wErr.Close()
	stdout = <-doneOut
	stderr = <-doneErr
	_ = rOut.Close()
	_ = rErr.Close()
	return stdout, stderr
}
