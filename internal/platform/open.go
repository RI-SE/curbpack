// Package platform holds thin OS adapters (open / reveal). Shared CLI logic stays OS-agnostic.
package platform

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
)

// OpenFile opens path with the OS default handler.
// Never silent: always prints Opened / Could not open with an absolute path.
func OpenFile(path string) error {
	abs, err := filepath.Abs(path)
	if err != nil {
		abs = path
	}
	cmd, err := openCmd(abs)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Could not open: %s (%v)\n", abs, err)
		return err
	}
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Start(); err != nil {
		fmt.Fprintf(os.Stderr, "Could not open: %s (%v)\n", abs, err)
		return fmt.Errorf("open %s: %w", abs, err)
	}
	fmt.Fprintf(os.Stderr, "Opened: %s\n", abs)
	return nil
}

// OpenURL opens a URL with the OS default handler (same never-silent contract).
func OpenURL(raw string) error {
	cmd, err := openCmd(raw)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Could not open: %s (%v)\n", raw, err)
		return err
	}
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Start(); err != nil {
		fmt.Fprintf(os.Stderr, "Could not open: %s (%v)\n", raw, err)
		return fmt.Errorf("open %s: %w", raw, err)
	}
	fmt.Fprintf(os.Stderr, "Opened: %s\n", raw)
	return nil
}

// RevealInFileManager opens the parent directory (Finder / Explorer / xdg-open).
func RevealInFileManager(path string) error {
	abs, err := filepath.Abs(path)
	if err != nil {
		abs = path
	}
	dir := filepath.Dir(abs)
	switch runtime.GOOS {
	case "darwin":
		cmd := exec.Command("open", "-R", abs)
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		if err := cmd.Start(); err != nil {
			fmt.Fprintf(os.Stderr, "Could not open: %s (%v)\n", abs, err)
			return err
		}
		fmt.Fprintf(os.Stderr, "Opened: %s\n", abs)
		return nil
	case "windows":
		cmd := exec.Command("explorer", "/select,", abs)
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		if err := cmd.Start(); err != nil {
			// Fall back to opening the directory
			return OpenFile(dir)
		}
		fmt.Fprintf(os.Stderr, "Opened: %s\n", abs)
		return nil
	default:
		return OpenFile(dir)
	}
}

func openCmd(target string) (*exec.Cmd, error) {
	switch runtime.GOOS {
	case "darwin":
		return exec.Command("open", target), nil
	case "windows":
		// cmd start needs an empty title arg when the path may be quoted.
		return exec.Command("cmd", "/c", "start", "", target), nil
	case "linux":
		return exec.Command("xdg-open", target), nil
	default:
		return nil, fmt.Errorf("unsupported OS for open: %s", runtime.GOOS)
	}
}
