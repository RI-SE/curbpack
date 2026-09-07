package cli

import (
	"fmt"
	"github.com/afelin/curbpack/internal/outwrite"
)

func cmdRecoverLock(args []string) error {
	if len(args) != 1 || args[0] == "--help" || args[0] == "-h" {
		return usageErr("usage: curbpack recover-lock <permitted-output-root>; removes only a lock whose recorded owner is known to have exited")
	}
	if err := outwrite.RecoverStale(args[0]); err != nil {
		return err
	}
	fmt.Println("Recovered stale writer lock. Rerun the interrupted command and verify its outputs.")
	return nil
}
