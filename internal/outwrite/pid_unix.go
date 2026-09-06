//go:build !windows

package outwrite

import (
	"os"
	"strconv"
	"syscall"
)

func pidAlive(pid int) bool {
	if pid <= 0 {
		return false
	}
	p, err := os.FindProcess(pid)
	if err != nil {
		return false
	}
	// On Unix, FindProcess always succeeds; Signal(0) probes liveness.
	err = p.Signal(syscall.Signal(0))
	return err == nil
}

// parsePID is used by tests.
func parsePID(s string) int {
	n, _ := strconv.Atoi(s)
	return n
}
