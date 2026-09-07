//go:build windows

package outwrite

import "syscall"

func pidAlive(pid int) bool {
	if pid <= 0 {
		return true
	}
	h, err := syscall.OpenProcess(syscall.SYNCHRONIZE, false, uint32(pid))
	if err == syscall.Errno(87) {
		return false
	}
	if err != nil {
		return true
	} // access denied is not proof of exit
	defer syscall.CloseHandle(h)
	status, err := syscall.WaitForSingleObject(h, 0)
	return err != nil || status != syscall.WAIT_OBJECT_0
}
