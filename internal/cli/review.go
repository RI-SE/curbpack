package cli

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/afelin/curbpack/internal/review"
	"github.com/afelin/curbpack/internal/tty"
)

func cmdReview(args []string) error {
	jsonOut := false
	full := false
	batch := false
	var paths []string
	for i := 0; i < len(args); i++ {
		a := args[i]
		switch {
		case a == "-h" || a == "--help":
			return helpShownErr("review")
		case a == "--json":
			jsonOut = true
		case a == "--full":
			full = true
		case a == "--batch":
			batch = true
		case strings.HasPrefix(a, "-"):
			return usageErr("unknown flag for review: " + a)
		default:
			paths = append(paths, a)
		}
	}
	if len(paths) == 0 {
		commandUsage("review")
		return usageErr("review requires a path to a received review-pack directory")
	}
	if batch {
		if jsonOut {
			return usageErr("review --batch does not combine with --json (run per-child with --json)")
		}
		if full {
			return usageErr("batch prints rank lines only; run per-pack with --full")
		}
		return runReviewBatch(paths)
	}
	if len(paths) != 1 {
		return usageErr("review accepts a single pack directory (use --batch for many)")
	}

	tty.PrintHeader("curbpack review")
	fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Dim, "Offline document triage — not a product verdict."))

	rep, err := review.Run(review.Options{
		BundleRoot: paths[0],
		Writer:     os.Stdout,
		JSONOut:    jsonOut,
		Full:       full,
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

type batchRow struct {
	path       string
	base       string
	rep        review.Report
	err        error
	unreadable bool
	contradict bool
	genuine    int
}

func runReviewBatch(paths []string) error {
	tty.PrintHeader("curbpack review --batch")
	fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Dim, "Offline document triage — not a product verdict."))

	children := expandBatchPaths(paths)
	if len(children) == 0 {
		return usageErr("review --batch found no review-pack directories")
	}

	var rows []batchRow
	for _, p := range children {
		row := batchRow{path: p, base: filepath.Base(p)}
		rep, err := review.Run(review.Options{
			BundleRoot: p,
			Writer:     ioDiscard{},
		})
		if err != nil {
			row.err = err
			row.unreadable = true
		} else {
			row.rep = rep
			row.contradict = review.HasContradictions(rep)
			row.genuine = rep.UnconfirmedGenuine
		}
		rows = append(rows, row)
	}

	sort.SliceStable(rows, func(i, j int) bool {
		// (1) unreadable / parse-fail first, (2) contradictions, (3) genuine desc, (4) basename
		if rows[i].unreadable != rows[j].unreadable {
			return rows[i].unreadable
		}
		if rows[i].contradict != rows[j].contradict {
			return rows[i].contradict
		}
		if rows[i].genuine != rows[j].genuine {
			return rows[i].genuine > rows[j].genuine
		}
		return rows[i].base < rows[j].base
	})

	anyBad := false
	for _, r := range rows {
		status := "ok"
		extra := ""
		switch {
		case r.unreadable:
			status = "UNREADABLE"
			extra = r.err.Error()
			anyBad = true
		case r.contradict:
			status = "CONTRADICTED"
			extra = fmt.Sprintf("%d contradicted · %d genuine", r.rep.ContradictedCount, r.rep.UnconfirmedGenuine)
			anyBad = true
		default:
			extra = fmt.Sprintf("%d genuine · %d extractor · confirmed %d",
				r.rep.UnconfirmedGenuine, r.rep.UnconfirmedExtractor, r.rep.ConfirmedCount)
		}
		fmt.Printf("%s\t%s\t%s\n", status, r.base, extra)
	}
	if anyBad {
		return gatesErr()
	}
	return nil
}

// looksLikeReviewPack reports whether dir has the required triage layers.
func looksLikeReviewPack(dir string) bool {
	for _, name := range []string{"01-gate-failures.json", "buyer-onepager.html"} {
		st, err := os.Stat(filepath.Join(dir, name))
		if err != nil || st.IsDir() || st.Size() == 0 {
			return false
		}
	}
	return true
}

// expandBatchPaths expands each arg: a pack dir is used as-is; a non-pack directory
// expands to immediate child dirs that look like review-packs. Junk children are ignored.
func expandBatchPaths(paths []string) []string {
	seen := map[string]struct{}{}
	var out []string
	add := func(p string) {
		p = filepath.Clean(p)
		if _, ok := seen[p]; ok {
			return
		}
		seen[p] = struct{}{}
		out = append(out, p)
	}
	for _, p := range paths {
		p = filepath.Clean(p)
		st, err := os.Stat(p)
		if err != nil || !st.IsDir() {
			// Keep unreadable/non-dir paths so batch can mark UNREADABLE.
			add(p)
			continue
		}
		if looksLikeReviewPack(p) {
			add(p)
			continue
		}
		entries, err := os.ReadDir(p)
		if err != nil {
			add(p)
			continue
		}
		foundChild := false
		for _, e := range entries {
			if !e.IsDir() {
				continue
			}
			child := filepath.Join(p, e.Name())
			if looksLikeReviewPack(child) {
				add(child)
				foundChild = true
			}
		}
		if !foundChild {
			// Parent was not a pack and had no pack children — surface as unreadable child.
			add(p)
		}
	}
	return out
}
