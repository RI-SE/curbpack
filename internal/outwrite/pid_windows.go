//go:build windows

package outwrite

import "os"

func pidAlive(pid int) bool {
	if pid <= 0 {
		return false
	}
	// Windows: FindProcess succeeds for existing PIDs; Signal is unsupported.
	// Treat any FindProcess success as potentially alive; rely on StaleLockAge
	// for recovery when the owner has exited without releasing.
	_, err := os.FindProcess(pid)
	return err == nil
}
