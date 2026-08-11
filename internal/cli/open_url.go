package cli

import (
	"fmt"
	"os"
	"os/exec"
	"runtime"

	"github.com/afelin/curbpack/internal/research"
)

func openAllowlistedURL(raw string) error {
	if err := research.ValidateSourceURL(raw); err != nil {
		return err
	}
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "darwin":
		cmd = exec.Command("open", raw)
	case "windows":
		cmd = exec.Command("rundll32", "url.dll,FileProtocolHandler", raw)
	default:
		cmd = exec.Command("xdg-open", raw)
	}
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Start(); err != nil {
		return fmt.Errorf("open %s: %w", raw, err)
	}
	return nil
}
