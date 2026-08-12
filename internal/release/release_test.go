package release_test

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/afelin/curbpack/internal/release"
)

func initGitRepo(t *testing.T, dir string) {
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
	run("git", "config", "user.email", "release@curbpack.local")
	run("git", "config", "user.name", "Release")
}

func TestPrepareReleaseWritesPack(t *testing.T) {
	dir := t.TempDir()
	initGitRepo(t, dir)
	mustWrite(t, filepath.Join(dir, "README.md"), "# x\n")
	run := exec.Command("git", "add", "README.md")
	run.Dir = dir
	run.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
	_ = run.Run()
	run2 := exec.Command("git", "commit", "-m", "readme", "-q")
	run2.Dir = dir
	run2.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
	_ = run2.Run()

	out := filepath.Join(dir, "review-pack")
	err := release.Prepare(release.Options{RepoRoot: dir, PackIDs: []string{"cra-baseline"}, OutDir: out})
	if err == nil {
		t.Fatal("prepare-release must fail when gates are red (without --allow-failing-gates)")
	}
	for _, name := range []string{
		"01-gate-failures.json",
		"02-action-report.md",
		"03-executive-summary.md",
		"buyer-onepager.html",
	} {
		if _, err := os.Stat(filepath.Join(out, name)); err != nil {
			t.Fatalf("missing %s: %v", name, err)
		}
	}
	html, _ := os.ReadFile(filepath.Join(out, "buyer-onepager.html"))
	if !strings.Contains(string(html), "Curbpack") {
		t.Fatal("buyer html missing brand")
	}
	if !strings.Contains(string(html), "not a certificate") {
		t.Fatal("buyer html must disclaim certification")
	}
	if !strings.Contains(string(html), "Structural evidence for human review") {
		t.Fatal("buyer html must stamp structural evidence honesty")
	}
	if !strings.Contains(string(html), "Back — provenance") {
		t.Fatal("buyer html must include provenance back")
	}
	if !strings.Contains(string(html), "Human sign-off") {
		t.Fatal("buyer html must include human sign-off row")
	}
	if !strings.Contains(string(html), "cra-baseline") {
		t.Fatal("buyer html must show chosen pack id")
	}
	if !strings.Contains(string(html), "Hand this one-pager") {
		t.Fatal("buyer html must say hand to buyer or auditor")
	}
	if err := release.Prepare(release.Options{
		RepoRoot: dir, PackIDs: []string{"cra-baseline"}, OutDir: out, AllowFailingGates: true,
	}); err != nil {
		t.Fatal(err)
	}
}

func TestPrepareSkipsUnchangedOnePager(t *testing.T) {
	dir := t.TempDir()
	initGitRepo(t, dir)
	mustWrite(t, filepath.Join(dir, "README.md"), "# x\n")
	run := exec.Command("git", "add", "README.md")
	run.Dir = dir
	run.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
	_ = run.Run()
	run2 := exec.Command("git", "commit", "-m", "readme", "-q")
	run2.Dir = dir
	run2.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
	_ = run2.Run()
	out := filepath.Join(dir, "review-pack")
	if err := release.Prepare(release.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}, OutDir: out, AllowFailingGates: true}); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(out, "buyer-onepager.html")
	info1, err := os.Stat(path)
	if err != nil {
		t.Fatal(err)
	}
	time.Sleep(10 * time.Millisecond)
	if err := release.Prepare(release.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}, OutDir: out, AllowFailingGates: true}); err != nil {
		t.Fatal(err)
	}
	info2, err := os.Stat(path)
	if err != nil {
		t.Fatal(err)
	}
	if !info1.ModTime().Equal(info2.ModTime()) {
		t.Fatal("unchanged one-pager should not be rewritten (mtime should match)")
	}
}

func mustWrite(t *testing.T, path, body string) {
	t.Helper()
	_ = os.MkdirAll(filepath.Dir(path), 0o755)
	if err := os.WriteFile(path, []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
}
