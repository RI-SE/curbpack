package cli

import (
	"github.com/afelin/curbpack/internal/drift"
	"github.com/afelin/curbpack/internal/gitutil"
)

func cmdDrift(args []string) error {
	root, err := gitutil.RepoRoot("")
	if err != nil {
		return usageErr("must run inside a git repository")
	}
	f, err := parseDriftFlags(args)
	if err != nil {
		return err
	}
	return drift.Run(drift.Options{RepoRoot: root, JSONOut: f.jsonOut})
}
