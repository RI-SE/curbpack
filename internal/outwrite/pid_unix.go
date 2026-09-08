//go:build !windows

package outwrite

import (
	"errors"
	"os"
	"syscall"
)

func pidAlive(pid int) bool {
	if pid <= 0 {
		return false
	}
	p, err := os.FindProcess(pid)
	if err != nil {
		return true
	}
	defer p.Release()
	// On Unix, FindProcess always succeeds; Signal(0) probes liveness.
	err = p.Signal(syscall.Signal(0))
	return !errors.Is(err, syscall.ESRCH) && !errors.Is(err, os.ErrProcessDone)
}
