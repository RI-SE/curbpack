// Command curbpack-sock is the optional Unix IPC server for Coreward integrators.
// Not part of the main curbpack binary — see examples/mcp/README.md.
package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/afelin/curbpack/examples/mcp/internal/sock"
	"github.com/afelin/curbpack/internal/gitutil"
)

func main() {
	path := flag.String("path", "", "Unix socket path (default: CURBPACK_SOCK or private runtime path)")
	repo := flag.String("repo", "", "Repository root (default: git root or cwd)")
	flag.Parse()
	if flag.NArg() > 0 {
		fmt.Fprintf(os.Stderr, "curbpack-sock: unknown argument %q\n", flag.Arg(0))
		os.Exit(2)
	}
	root := *repo
	if root == "" {
		var err error
		root, err = gitutil.RepoRoot("")
		if err != nil {
			root, _ = os.Getwd()
		}
	}
	if err := sock.Serve(*path, root); err != nil {
		fmt.Fprintf(os.Stderr, "curbpack-sock: %v\n", err)
		os.Exit(1)
	}
}
