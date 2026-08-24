package cli_test

import (
	"os"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/cli"
)

func TestRun_LadderHelpExitZero(t *testing.T) {
	commands := []string{"scan", "check", "share", "drift", "init", "attest"}
	for _, cmd := range commands {
		t.Run(cmd+" --help", func(t *testing.T) {
			stdout, stderr := capture(t, func() {
				if err := cli.Run([]string{cmd, "--help"}); err != nil {
					t.Fatalf("Run(%q --help): %v", cmd, err)
				}
			})
			combined := stdout + stderr
			if !strings.Contains(combined, "Usage:") {
				t.Fatalf("%s --help missing Usage line: %q", cmd, combined)
			}
		})
	}
}

func TestRun_ScanHelpOutsideRepo(t *testing.T) {
	dir := t.TempDir()
	old, _ := os.Getwd()
	_ = os.Chdir(dir)
	defer func() { _ = os.Chdir(old) }()

	_, stderr := capture(t, func() {
		if err := cli.Run([]string{"scan", "--help"}); err != nil {
			t.Fatal(err)
		}
	})
	if !strings.Contains(stderr, "Usage:") {
		t.Fatalf("scan --help outside repo: %q", stderr)
	}
}
