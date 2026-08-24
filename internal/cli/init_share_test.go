package cli_test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/cli"
)

func TestRun_InitDryRun(t *testing.T) {
	dir := t.TempDir()
	initScanGit(t, dir)

	stdout, _ := capture(t, func() {
		old, _ := os.Getwd()
		_ = os.Chdir(dir)
		defer func() { _ = os.Chdir(old) }()
		if err := cli.Run([]string{"init", "--dry-run"}); err != nil {
			t.Fatal(err)
		}
	})
	if !strings.Contains(stdout, "Profile: house-policy") {
		t.Fatalf("default init must print house-policy profile: %q", stdout)
	}
	if !strings.Contains(stdout, "house-policy default; --profile cra to match scan") {
		t.Fatalf("default init must explain profile why: %q", stdout)
	}
	if !strings.Contains(stdout, "Will write:") {
		t.Fatalf("init must print write list: %q", stdout)
	}
	for _, want := range []string{".env", "secret-path decoy", ".git/hooks/pre-commit", "(hook)", "SKILL.md", "(skill)", ".vscode/tasks.json"} {
		if !strings.Contains(stdout, want) {
			t.Fatalf("dry-run write list missing %q: %q", want, stdout)
		}
	}
	if !strings.Contains(stdout, "Dry-run — nothing written.") {
		t.Fatalf("dry-run must say nothing written: %q", stdout)
	}
	for _, path := range []string{
		filepath.Join(dir, ".curbpack.json"),
		filepath.Join(dir, ".vscode"),
		filepath.Join(dir, ".cursor"),
		filepath.Join(dir, ".env"),
		filepath.Join(dir, "proof"),
	} {
		if _, err := os.Stat(path); !os.IsNotExist(err) {
			t.Fatalf("dry-run must not write %s (err=%v)", path, err)
		}
	}
}

func TestRun_InitProfileCraDryRun(t *testing.T) {
	dir := t.TempDir()
	initScanGit(t, dir)

	stdout, _ := capture(t, func() {
		old, _ := os.Getwd()
		_ = os.Chdir(dir)
		defer func() { _ = os.Chdir(old) }()
		if err := cli.Run([]string{"init", "--profile", "cra", "--dry-run"}); err != nil {
			t.Fatal(err)
		}
	})
	if !strings.Contains(stdout, "Profile: cra-baseline") {
		t.Fatalf("want cra-baseline profile: %q", stdout)
	}
	if !strings.Contains(stdout, "--profile cra to match scan") {
		t.Fatalf("want --profile cra why: %q", stdout)
	}
}

func TestRun_InitBareDryRunOmitsHookSkillIDE(t *testing.T) {
	dir := t.TempDir()
	initScanGit(t, dir)

	stdout, _ := capture(t, func() {
		old, _ := os.Getwd()
		_ = os.Chdir(dir)
		defer func() { _ = os.Chdir(old) }()
		if err := cli.Run([]string{"init", "--bare", "--dry-run"}); err != nil {
			t.Fatal(err)
		}
	})
	for _, bad := range []string{".git/hooks/pre-commit", "(hook)", "SKILL.md", "(skill)", ".vscode/tasks.json"} {
		if strings.Contains(stdout, bad) {
			t.Fatalf("--bare dry-run must omit %q: %q", bad, stdout)
		}
	}
	if !strings.Contains(stdout, "secret-path decoy") {
		t.Fatalf("--bare still scaffolds secret-path decoys: %q", stdout)
	}
}

func TestRun_ShareAttachReviewPack(t *testing.T) {
	dir := t.TempDir()
	initScanGit(t, dir)
	mustWriteScan(t, filepath.Join(dir, ".curbpack.json"), `{"packs":["house-policy"]}`+"\n")
	mustWriteScan(t, filepath.Join(dir, "SECURITY.md"), "# Security\n\n"+strings.Repeat("word ", 80)+"\n")
	mustWriteScan(t, filepath.Join(dir, ".well-known", "security.txt"), "Contact: mailto:a@b.c\nExpires: 2027-01-01T00:00:00.000Z\nPreferred-Languages: en\n")

	stdout, _ := capture(t, func() {
		old, _ := os.Getwd()
		_ = os.Chdir(dir)
		defer func() { _ = os.Chdir(old) }()
		err := cli.Run([]string{"share", "--skip-prepare-release"})
		if err != nil && cli.ExitCode(err) != cli.ExitGates {
			t.Fatalf("share: %v", err)
		}
	})

	cacheCP := filepath.Join(dir, ".github", "curbpack", "cache", "context-pack.json")
	cacheBQ := filepath.Join(dir, ".github", "curbpack", "cache", "buyer-questions.md")
	reviewCP := filepath.Join(dir, "review-pack", "context-pack.json")
	reviewBQ := filepath.Join(dir, "review-pack", "buyer-questions.md")
	for _, path := range []string{cacheCP, cacheBQ, reviewCP, reviewBQ} {
		if _, err := os.Stat(path); err != nil {
			t.Fatalf("expected %s: %v\nstdout=%q", path, err, stdout)
		}
	}
	if !strings.Contains(stdout, "Attach:") {
		t.Fatalf("share must print Attach lines: %q", stdout)
	}
	attachReview := 0
	for _, line := range strings.Split(stdout, "\n") {
		if strings.HasPrefix(line, "Attach:") && strings.Contains(line, "review-pack") {
			attachReview++
		}
	}
	if attachReview < 2 {
		t.Fatalf("want Attach lines under review-pack/ for context-pack + buyer-questions, got %d in %q", attachReview, stdout)
	}
}
