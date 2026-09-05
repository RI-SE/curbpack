package gitutil_test

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/gitutil"
)

func TestRunGit_neutralizesRepoLocalExecutableConfig(t *testing.T) {
	dir := t.TempDir()
	initGitRepo(t, dir)

	marker := filepath.Join(dir, "fsmonitor-fired")
	monitor := filepath.Join(dir, "evil-fsmonitor")
	script := "#!/bin/sh\ntouch \"" + marker + "\"\nexit 0\n"
	if err := os.WriteFile(monitor, []byte(script), 0o755); err != nil {
		t.Fatal(err)
	}
	run := func(args ...string) {
		t.Helper()
		cmd := exec.Command(args[0], args[1:]...)
		cmd.Dir = dir
		cmd.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
		if out, err := cmd.CombinedOutput(); err != nil {
			t.Fatalf("%v: %s", err, out)
		}
	}
	run("git", "commit", "--allow-empty", "-m", "seed", "-q")
	run("git", "config", "core.fsmonitor", monitor)
	_ = os.Remove(marker)

	if _, err := gitutil.ChangedFiles(dir); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(marker); err == nil {
		t.Fatal("repository-local core.fsmonitor must not execute during evaluator gitutil calls (MUST-45)")
	}
}

func TestFileTouchedSinceRef_optionShapedFailsClosed(t *testing.T) {
	dir := t.TempDir()
	initGitRepo(t, dir)
	run := func(args ...string) {
		t.Helper()
		cmd := exec.Command(args[0], args[1:]...)
		cmd.Dir = dir
		cmd.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
		if out, err := cmd.CombinedOutput(); err != nil {
			t.Fatalf("%v: %s", err, out)
		}
	}
	path := filepath.Join(dir, "tracked.md")
	if err := os.WriteFile(path, []byte("v1\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	run("git", "add", "tracked.md")
	run("git", "commit", "-m", "c1", "-q")

	marker := filepath.Join(dir, "option-output")
	ok, err := gitutil.FileTouchedSinceRef(dir, "--output="+marker, "tracked.md")
	if err == nil {
		t.Fatal("option-shaped since_ref must fail closed")
	}
	if ok {
		t.Fatal("option-shaped since_ref must not report touched")
	}
	if !strings.Contains(err.Error(), "option") && !strings.Contains(err.Error(), "ref") {
		t.Fatalf("want ref/option error, got %v", err)
	}
	if _, err := os.Stat(marker); err == nil {
		t.Fatal("option-shaped since_ref must not create git --output file")
	}
	_, err = gitutil.FileTouchedSinceRef(dir, "-n", "tracked.md")
	if err == nil {
		t.Fatal("leading-dash since_ref must fail closed")
	}
}

func TestDiffNameOnly_optionShapedRevsFailClosed(t *testing.T) {
	dir := t.TempDir()
	initGitRepo(t, dir)
	run := func(args ...string) {
		t.Helper()
		cmd := exec.Command(args[0], args[1:]...)
		cmd.Dir = dir
		cmd.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
		if out, err := cmd.CombinedOutput(); err != nil {
			t.Fatalf("%v: %s", err, out)
		}
	}
	if err := os.WriteFile(filepath.Join(dir, "a.md"), []byte("x\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	run("git", "add", "a.md")
	run("git", "commit", "-m", "c1", "-q")
	sha, err := gitutil.HeadSHA(dir)
	if err != nil {
		t.Fatal(err)
	}
	marker := filepath.Join(dir, "diff-output")
	_, err = gitutil.DiffNameOnly(dir, "--output="+marker, sha, []string{"a.md"})
	if err == nil {
		t.Fatal("option-shaped fromRev must fail closed")
	}
	if _, err := os.Stat(marker); err == nil {
		t.Fatal("option-shaped rev must not create git --output file")
	}
}
