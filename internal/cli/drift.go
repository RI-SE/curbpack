package cli

import (
	"github.com/afelin/curbpack/internal/drift"
	"github.com/afelin/curbpack/internal/gitutil"
)

func cmdDrift(args []string) error {
	f, err := parseDriftFlags(args)
	if helpRequested(err) {
		return nil
	}
	if err != nil {
		return err
	}
	root, err := gitutil.RepoRoot("")
	if err != nil {
		return usageErr("must run inside a git repository")
	}
	return drift.Run(drift.Options{RepoRoot: root, JSONOut: f.jsonOut})
}
