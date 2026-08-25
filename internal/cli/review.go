package cli

import (
	"fmt"
	"os"
	"strings"

	"github.com/afelin/curbpack/internal/review"
	"github.com/afelin/curbpack/internal/tty"
)

func cmdReview(args []string) error {
	jsonOut := false
	var path string
	for i := 0; i < len(args); i++ {
		a := args[i]
		switch {
		case a == "-h" || a == "--help":
			return helpShownErr("review")
		case a == "--json":
			jsonOut = true
		case strings.HasPrefix(a, "-"):
			return usageErr("unknown flag for review: " + a)
		default:
			if path != "" {
				return usageErr("review accepts a single pack directory path")
			}
			path = a
		}
	}
	if path == "" {
		commandUsage("review")
		return usageErr("review requires a path to a received review-pack directory")
	}

	tty.PrintHeader("curbpack review")
	fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Dim, "Offline document triage — not a product verdict."))

	rep, err := review.Run(review.Options{
		BundleRoot: path,
		Writer:     os.Stdout,
		JSONOut:    jsonOut,
	})
	if err != nil {
		return usageErr(err.Error())
	}
	if review.HasContradictions(rep) {
		fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Yellow, "Contradicted findings present — see triage note above."))
		return gatesErr()
	}
	return nil
}
