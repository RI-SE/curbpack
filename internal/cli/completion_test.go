package cli_test

import (
	"strings"
	"testing"

	"github.com/afelin/cyberready/internal/cli"
)

func TestRun_CompletionBash(t *testing.T) {
	stdout, _ := capture(t, func() {
		if err := cli.Run([]string{"completion", "bash"}); err != nil {
			t.Fatal(err)
		}
	})
	if !strings.Contains(stdout, "complete -F _cyberready cyberready") {
		t.Fatalf("bash completion missing complete line: %q", stdout)
	}
	if !strings.Contains(stdout, "--context-pack") {
		t.Fatal("expected --context-pack in export completions")
	}
	if !strings.Contains(stdout, "share") {
		t.Fatal("expected share command")
	}
}

func TestRun_CompletionUnknownShell(t *testing.T) {
	_, _ = capture(t, func() {
		err := cli.Run([]string{"completion", "tcsh"})
		if cli.ExitCode(err) != cli.ExitUsage {
			t.Fatalf("want exit 2, got %d (%v)", cli.ExitCode(err), err)
		}
	})
}
