package cli

import (
	"bytes"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/instrument"
)

func TestAccumulationDeltaLineNoPrior(t *testing.T) {
	if got := accumulationDeltaLine(priorCacheSnapshot{}, "house-policy", 0, strings.Repeat("a", 64)); got != "" {
		t.Fatalf("want empty without prior, got %q", got)
	}
}

func TestAccumulationDeltaLineFailedChange(t *testing.T) {
	got := accumulationDeltaLine(priorCacheSnapshot{
		OK: true, PackID: "house-policy", SchemaVersion: "curbpack-evaluation:2", ComparisonKey: strings.Repeat("a", 64), Failed: 2, FailureCount: 2,
	}, "house-policy", 0, strings.Repeat("a", 64))
	if !strings.Contains(got, "Δ failed 2→0") {
		t.Fatalf("want failed delta, got %q", got)
	}
	if strings.Count(got, "\n") != 0 {
		t.Fatalf("must be exactly one line, got %q", got)
	}
}

func TestInstrumentWhisperLinesCapsAndFirstRunQuiet(t *testing.T) {
	priorCache := priorCacheSnapshot{
		OK: true, PackID: "house-policy", SchemaVersion: "curbpack-evaluation:2", ComparisonKey: strings.Repeat("a", 64), Failed: 1, FailureCount: 1,
	}
	now := instrument.Snapshot{DepsFP: "bbb", SecretHits: 2, Deps: []instrument.Dep{{Name: "a", Eco: "npm"}}}
	// First run: no prior instrument → failed tally only.
	lines := instrumentWhisperLines(priorCache, instrument.Snapshot{}, false, "house-policy", 0, now, strings.Repeat("a", 64))
	if len(lines) != 1 || !strings.Contains(lines[0], "Δ failed") {
		t.Fatalf("first run want failed tally only, got %#v", lines)
	}
	prior := instrument.Snapshot{DepsFP: "aaa", SecretHits: 0, Deps: nil}
	lines = instrumentWhisperLines(priorCache, prior, true, "house-policy", 0, now, strings.Repeat("a", 64))
	if len(lines) < 2 || len(lines) > 3 {
		t.Fatalf("want 2–3 lines, got %#v", lines)
	}
	joined := strings.Join(lines, "\n")
	if !strings.Contains(joined, "Δ deps") || !strings.Contains(joined, "Δ secret-hits") {
		t.Fatalf("missing deps/secret whispers:\n%s", joined)
	}
}

func TestAccumulationDeltaLineRepeatGreen(t *testing.T) {
	got := accumulationDeltaLine(priorCacheSnapshot{
		OK: true, PackID: "house-policy", SchemaVersion: "curbpack-evaluation:2", ComparisonKey: strings.Repeat("a", 64), Failed: 0, FailureCount: 0,
	}, "house-policy", 0, strings.Repeat("a", 64))
	if got != "gates tally unchanged · evidence cache updated" {
		t.Fatalf("got %q", got)
	}
}

func TestLoadPriorCacheAndGreenCheckWhisper(t *testing.T) {
	dir := t.TempDir()
	mustGit(t, dir)
	writeGreenHouse(t, dir)

	cache := filepath.Join(dir, ".github", "curbpack", "cache")
	if err := os.MkdirAll(cache, 0o755); err != nil {
		t.Fatal(err)
	}
	prior := `{
  "schema_version": "1",
  "failures": [{"gate_id":"HOUSE-SECURITY-MD"},{"gate_id":"HOUSE-SECURITY-TXT"}],
  "pack_id": "house-policy",
  "readiness_score": 60,
  "failed_rules": 2
}`
	if err := os.WriteFile(filepath.Join(cache, "latest_result.json"), []byte(prior), 0o644); err != nil {
		t.Fatal(err)
	}

	snap := loadPriorCache(dir)
	if snap.OK || snap.Failed != 2 || snap.FailureCount != 2 {
		t.Fatalf("prior snapshot=%+v", snap)
	}

	oldWD, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	if err := os.Chdir(dir); err != nil {
		t.Fatal(err)
	}
	defer func() { _ = os.Chdir(oldWD) }()

	out := captureCLIStdout(t, func() {
		if err := cmdCheck(nil); err != nil {
			t.Fatalf("check: %v", err)
		}
	})
	deltaLines := 0
	for _, line := range strings.Split(out, "\n") {
		trim := strings.TrimSpace(line)
		if strings.Contains(trim, "Δ ") || strings.Contains(trim, "evidence cache updated") {
			deltaLines++
		}
	}
	if deltaLines != 0 {
		t.Fatalf("unbound historical cache must not produce a trend, got %d\n%s", deltaLines, out)
	}
	if strings.Contains(out, "Δ failed") {
		t.Fatalf("unverified alias produced a trend:\n%s", out)
	}
}

func TestGreenCheckNoDeltaWithoutPrior(t *testing.T) {
	dir := t.TempDir()
	mustGit(t, dir)
	writeGreenHouse(t, dir)

	oldWD, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	if err := os.Chdir(dir); err != nil {
		t.Fatal(err)
	}
	defer func() { _ = os.Chdir(oldWD) }()

	out := captureCLIStdout(t, func() {
		if err := cmdCheck(nil); err != nil {
			t.Fatalf("check: %v", err)
		}
	})
	if strings.Contains(out, "Δ ") || strings.Contains(out, "evidence cache updated") {
		t.Fatalf("must not whisper without prior cache:\n%s", out)
	}
}

func writeGreenHouse(t *testing.T, dir string) {
	t.Helper()
	mustWriteFile(t, filepath.Join(dir, "README.md"), "# Product\n")
	mustWriteFile(t, filepath.Join(dir, ".well-known/security.txt"), "Contact: mailto:a@b.c\nExpires: 2027-01-01T00:00:00.000Z\nPreferred-Languages: en\n")
	mustWriteFile(t, filepath.Join(dir, "SECURITY.md"), `# Security Policy

## Reporting

Report vulnerabilities to security@example.com with reproduction steps.

## Supported Versions

We support the latest major release with security patches for twelve months.

## Disclosure

Coordinated disclosure within 90 days after fix availability.
`+strings.Repeat("word ", 40)+"\n")
	mustWriteFile(t, filepath.Join(dir, "package.json"), `{"name":"product","version":"1.0.0","dependencies":{}}`+"\n")
	mustWriteFile(t, filepath.Join(dir, ".curbpack.json"), `{"packs":["house-policy"],"claim":"Prepares evidence for human review — not a conformity assessment."}`+"\n")
}

func captureCLIStdout(t *testing.T, fn func()) string {
	t.Helper()
	r, w, err := os.Pipe()
	if err != nil {
		t.Fatal(err)
	}
	old := os.Stdout
	os.Stdout = w
	defer func() { os.Stdout = old }()
	done := make(chan string, 1)
	go func() {
		var buf bytes.Buffer
		_, _ = io.Copy(&buf, r)
		done <- buf.String()
	}()
	fn()
	_ = w.Close()
	return <-done
}

func mustGit(t *testing.T, dir string) {
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
	run("git", "config", "user.email", "accum@curbpack.local")
	run("git", "config", "user.name", "Accum")
	run("git", "commit", "--allow-empty", "-m", "init", "-q")
}

func mustWriteFile(t *testing.T, path, body string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
}
