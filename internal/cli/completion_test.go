package cli_test

import (
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/cli"
)

func TestRun_CompletionBash(t *testing.T) {
	stdout, _ := capture(t, func() {
		if err := cli.Run([]string{"completion", "bash"}); err != nil {
			t.Fatal(err)
		}
	})
	if !strings.Contains(stdout, "complete -F _curbpack curbpack") {
		t.Fatalf("bash completion missing complete line: %q", stdout)
	}
	if !strings.Contains(stdout, "--context-pack") {
		t.Fatal("expected --context-pack in export completions")
	}
	if !strings.Contains(stdout, "share") {
		t.Fatal("expected share command")
	}
	if !strings.Contains(stdout, "drift") {
		t.Fatal("expected drift command")
	}
	if !strings.Contains(stdout, "--repair") {
		t.Fatal("expected doctor --repair")
	}
	if !strings.Contains(stdout, "--bundle") {
		t.Fatal("expected share --bundle")
	}
	if !strings.Contains(stdout, "--reveal") {
		t.Fatal("expected share --reveal")
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
