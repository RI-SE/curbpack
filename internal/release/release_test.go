package release_test

import (
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/release"
)

func TestPrepareAggregatesPartialWriteFailures(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "1704067200")
	dir := t.TempDir()
	initPassingHouse(t, dir)

	out := filepath.Join(dir, "review-pack")
	if err := os.MkdirAll(out, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.Chmod(out, 0o555); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = os.Chmod(out, 0o755) })

	err := release.Prepare(release.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}, OutDir: out})
	if err == nil {
		t.Fatal("expected aggregated write errors")
	}
	var joined interface{ Unwrap() []error }
	if !errors.As(err, &joined) {
		t.Fatalf("expected errors.Join aggregate, got %T: %v", err, err)
	}
	if len(joined.Unwrap()) < 2 {
		t.Fatalf("expected multiple partial failures, got %d: %v", len(joined.Unwrap()), err)
	}
}

func initPassingHouse(t *testing.T, dir string) {
	t.Helper()
	write := func(rel, body string) {
		t.Helper()
		p := filepath.Join(dir, rel)
		if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(p, []byte(body), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	write("README.md", "# Project\n")
	write(".well-known/security.txt", "Contact: mailto:a@b.c\nExpires: 2027-01-01T00:00:00.000Z\nPreferred-Languages: en\n")
	write("SECURITY.md", "# Security Policy\n\n## Reporting\n\nReport vulnerabilities to security@example.com.\n\n## Supported Versions\n\nLatest release.\n\n## Disclosure\n\nCoordinated disclosure.\n\n"+strings.Repeat("word ", 40))
	runGit(t, dir, "init", "-q")
	runGit(t, dir, "config", "user.email", "release@curbpack.local")
	runGit(t, dir, "config", "user.name", "Release")
	runGit(t, dir, "add", ".")
	runGit(t, dir, "commit", "-m", "init", "-q")
}

func runGit(t *testing.T, dir string, args ...string) {
	t.Helper()
	cmd := exec.Command("git", args...)
	cmd.Dir = dir
	cmd.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("git %v: %v\n%s", args, err, out)
	}
}
