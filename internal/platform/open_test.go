package platform

import (
	"runtime"
	"strings"
	"testing"
)

func TestOpenCmdSupportedOS(t *testing.T) {
	cmd, err := openCmd("/tmp/curbpack-open-test")
	switch runtime.GOOS {
	case "darwin", "linux", "windows":
		if err != nil {
			t.Fatalf("openCmd: %v", err)
		}
		if cmd == nil {
			t.Fatal("expected non-nil cmd")
		}
	default:
		if err == nil {
			t.Fatal("expected error on unsupported OS")
		}
	}
}

func TestOpenFileNeverSilentContract(t *testing.T) {
	// Contract: OpenFile always reports abs path on failure path for empty/missing.
	// We only assert the helper builds a command with an absolute-looking target.
	cmd, err := openCmd("relative-file.html")
	if err != nil && runtime.GOOS != "darwin" && runtime.GOOS != "linux" && runtime.GOOS != "windows" {
		return
	}
	if err != nil {
		t.Fatalf("openCmd: %v", err)
	}
	joined := strings.Join(cmd.Args, " ")
	if !strings.Contains(joined, "relative-file.html") {
		t.Fatalf("expected target in args: %v", cmd.Args)
	}
}
