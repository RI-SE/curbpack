package cli

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func TestInstalledPreCommitHookInvokesCheckWithoutHeal(t *testing.T) {
	root := t.TempDir()
	runHookTestCommand(t, root, "git", "init", "-q")

	if err := installPreCommitHook(root); err != nil {
		t.Fatalf("install hook: %v", err)
	}
	hook := filepath.Join(root, ".git", "hooks", "pre-commit")
	body, err := os.ReadFile(hook)
	if err != nil {
		t.Fatalf("read hook: %v", err)
	}
	if strings.Contains(string(body), "--heal") {
		t.Fatalf("commit hook must not heal tracked files:\n%s", body)
	}
	if !strings.Contains(string(body), "exec curbpack check\n") {
		t.Fatalf("commit hook must run curbpack check:\n%s", body)
	}

	binDir := t.TempDir()
	argsFile := filepath.Join(t.TempDir(), "args")
	fake := filepath.Join(binDir, "curbpack")
	fakeBody := "#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$CURBPACK_ARGS_FILE\"\n"
	if err := os.WriteFile(fake, []byte(fakeBody), 0o755); err != nil {
		t.Fatalf("write fake curbpack: %v", err)
	}

	cmd := exec.Command(hook)
	cmd.Dir = root
	cmd.Env = append(
		os.Environ(),
		"PATH="+binDir+string(os.PathListSeparator)+os.Getenv("PATH"),
		"CURBPACK_ARGS_FILE="+argsFile,
	)
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("run hook: %v\n%s", err, out)
	}
	args, err := os.ReadFile(argsFile)
	if err != nil {
		t.Fatalf("read hook arguments: %v", err)
	}
	if got := string(args); got != "check\n" {
		t.Fatalf("hook arguments = %q, want check only", got)
	}
	if status := runHookTestCommand(t, root, "git", "status", "--porcelain"); status != "" {
		t.Fatalf("hook changed tracked workspace state: %s", status)
	}
}

func runHookTestCommand(t *testing.T, dir string, name string, args ...string) string {
	t.Helper()
	cmd := exec.Command(name, args...)
	cmd.Dir = dir
	out, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("%s %v: %v\n%s", name, args, err, out)
	}
	return strings.TrimSpace(string(out))
}
