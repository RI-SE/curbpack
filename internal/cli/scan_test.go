package cli_test

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/cli"
	"github.com/afelin/curbpack/internal/packs"
)

func TestRun_ScanReadOnly(t *testing.T) {
	dir := t.TempDir()
	initScanGit(t, dir)
	mustWriteScan(t, filepath.Join(dir, "package.json"), `{"name":"scan-widget","version":"1.0.0"}`+"\n")
	mustWriteScan(t, filepath.Join(dir, "README.md"), "# Scan Widget\n")

	stdout, _ := capture(t, func() {
		old, _ := os.Getwd()
		_ = os.Chdir(dir)
		defer func() { _ = os.Chdir(old) }()
		if err := cli.Run([]string{"scan"}); err != nil {
			t.Fatal(err)
		}
	})
	if !strings.Contains(stdout, "Read-only") {
		t.Fatalf("missing read-only banner: %q", stdout)
	}
	if !strings.Contains(stdout, "scan-widget") {
		t.Fatalf("missing product hint: %q", stdout)
	}
	if !strings.Contains(stdout, "Art 14 reporting clock") {
		t.Fatalf("missing Art 14 clock: %q", stdout)
	}
	if strings.Contains(stdout, "Readiness Score") {
		t.Fatal("scan must not show readiness thermometer")
	}
	cache := filepath.Join(dir, ".github", "curbpack", "cache", "latest_failure.json")
	if _, err := os.Stat(cache); err == nil {
		t.Fatal("scan must not write cache")
	}
}

func TestRun_FixArt14Yes(t *testing.T) {
	dir := t.TempDir()
	initScanGit(t, dir)
	mustWriteScan(t, filepath.Join(dir, "package.json"), `{"name":"fixco","version":"1.0.0"}`+"\n")

	stdout, _ := capture(t, func() {
		old, _ := os.Getwd()
		_ = os.Chdir(dir)
		defer func() { _ = os.Chdir(old) }()
		if err := cli.Run([]string{"fix", "--art14", "--yes"}); err != nil {
			t.Fatal(err)
		}
	})
	if !strings.Contains(stdout, "docs/incident/art14-path.md") {
		t.Fatalf("expected target path in output: %q", stdout)
	}
	path := filepath.Join(dir, "docs/incident", "art14-path.md")
	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(b), "fixco") {
		t.Fatalf("Art 14 body must include product name: %q", b)
	}
	if string(b) == packs.DefaultScaffoldBody(packs.Art14RelPath()) {
		t.Fatal("fix --art14 must write Art14PathBody not DefaultScaffoldBody")
	}
}

func TestRun_AskMySuppliers(t *testing.T) {
	dir := t.TempDir()
	initScanGit(t, dir)
	mustWriteScan(t, filepath.Join(dir, "README.md"), "# Demo\n")
	mustWriteScan(t, filepath.Join(dir, "SECURITY.md"), "# Security\n\n"+strings.Repeat("word ", 80)+"\n")
	mustWriteScan(t, filepath.Join(dir, ".well-known", "security.txt"), "Contact: mailto:a@b.c\nExpires: 2027-01-01T00:00:00.000Z\nPreferred-Languages: en\n")
	cfg := filepath.Join(dir, ".curbpack.json")
	mustWriteScan(t, cfg, `{"packs":["house-policy"]}`+"\n")

	stdout, _ := capture(t, func() {
		old, _ := os.Getwd()
		_ = os.Chdir(dir)
		defer func() { _ = os.Chdir(old) }()
		if err := cli.Run([]string{"ask-my-suppliers"}); err != nil {
			t.Fatal(err)
		}
	})
	if !strings.Contains(stdout, "buyer-questions") {
		t.Fatalf("expected buyer-questions status: %q", stdout)
	}
}

func initScanGit(t *testing.T, dir string) {
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
	run("git", "config", "user.email", "t@example.com")
	run("git", "config", "user.name", "t")
	mustWriteScan(t, filepath.Join(dir, ".gitkeep"), "")
	run("git", "add", ".")
	run("git", "commit", "-m", "init", "-q")
}

func mustWriteScan(t *testing.T, path, body string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
}
