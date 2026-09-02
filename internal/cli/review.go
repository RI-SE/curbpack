package cli

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/afelin/curbpack/internal/attest"
	"github.com/afelin/curbpack/internal/config"
	"github.com/afelin/curbpack/internal/gitutil"
	"github.com/afelin/curbpack/internal/pathway"
	"github.com/afelin/curbpack/internal/review"
	"github.com/afelin/curbpack/internal/tty"
)

func cmdReview(args []string) error {
	jsonOut := false
	full := false
	batch := false
	repoMode := false
	repoPath := "."
	sincePath := ""
	verifyChain := false
	edgesPath := ""
	var packList []string
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
		case a == "--verify-chain":
			verifyChain = true
		case a == "--repo":
			repoMode = true
			if i+1 < len(args) && !strings.HasPrefix(args[i+1], "-") {
				i++
				repoPath = args[i]
			}
		case a == "--packs":
			if i+1 >= len(args) {
				return usageErr("review --packs requires a value")
			}
			i++
			packList = config.ParsePacksFlag(args[i])
			if len(packList) == 0 {
				return usageErr("review --packs requires at least one pack id")
			}
		case strings.HasPrefix(a, "--packs="):
			packList = config.ParsePacksFlag(strings.TrimPrefix(a, "--packs="))
			if len(packList) == 0 {
				return usageErr("review --packs requires at least one pack id")
			}
		case a == "--since":
			if i+1 >= len(args) {
				return usageErr("review --since requires a path to a prior report JSON")
			}
			i++
			sincePath = args[i]
		case a == "--edges":
			if i+1 >= len(args) {
				return usageErr("review --edges requires a path to an edges JSON file")
			}
			i++
			edgesPath = args[i]
		case strings.HasPrefix(a, "-"):
			return usageErr("unknown flag for review: " + a)
		default:
			paths = append(paths, a)
		}
	}
	if verifyChain {
		if repoMode || batch || sincePath != "" || edgesPath != "" || len(packList) > 0 || jsonOut || full {
			return usageErr("review --verify-chain is exclusive (no --repo/--batch/--since/--packs/--json/--full)")
		}
		if len(paths) != 2 {
			return usageErr("review --verify-chain requires <parent.json> <child.json>")
		}
		return runVerifyChain(paths[0], paths[1])
	}
	if edgesPath != "" {
		if !repoMode {
			return usageErr("review --edges only applies with --repo")
		}
		if !jsonOut {
			return usageErr("review --edges requires --json")
		}
		if batch {
			return usageErr("review --edges does not combine with --batch")
		}
		if verifyChain {
			return usageErr("review --edges does not combine with --verify-chain")
		}
	}
	if repoMode && batch {
		return usageErr("review --repo does not combine with --batch")
	}
	if len(packList) > 0 && !repoMode {
		return usageErr("review --packs only applies with --repo")
	}
	if repoMode {
		if len(paths) != 0 {
			return usageErr("review --repo does not take a pack path argument (got " + strings.Join(paths, ", ") + ")")
		}
		return runReviewRepo(repoPath, packList, jsonOut, full, sincePath, edgesPath)
	}
	if len(paths) == 0 {
		commandUsage("review")
		return usageErr("review requires a path to a received review-pack directory (or --repo)")
	}
	if batch {
		if sincePath != "" {
			return usageErr("review --batch does not combine with --since")
		}
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

	var prior *review.Report
	if sincePath != "" {
		p, err := loadPriorReport(sincePath)
		if err != nil {
			return usageErr(err.Error())
		}
		prior = &p
	}

	if !jsonOut {
		tty.PrintHeader("curbpack review")
	}
	fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Dim, "Offline document triage — not a product verdict."))

	rep, err := review.Run(review.Options{
		BundleRoot: paths[0],
		Writer:     os.Stdout,
		JSONOut:    jsonOut,
		Full:       full,
		Prior:      prior,
	})
	if err != nil {
		return usageErr(err.Error())
	}
	if jsonOut {
		if err := review.WriteJSON(rep, os.Stdout); err != nil {
			return usageErr(err.Error())
		}
	}
	printReviewHPURLFragment(paths[0], rep, false)
	if review.HasContradictions(rep) {
		fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Yellow, "Contradicted findings present — see triage note above."))
		return gatesErr()
	}
	return nil
}

func runReviewRepo(repoPath string, packList []string, jsonOut, full bool, sincePath, edgesPath string) error {
	root, err := filepath.Abs(filepath.Clean(strings.TrimSpace(repoPath)))
	if err != nil {
		return usageErr(fmt.Sprintf("review --repo: resolve path %q: %v", repoPath, err))
	}
	packIDs, err := config.ResolvePackIDs(root, packList)
	if err != nil {
		return usageErr(fmt.Sprintf("review --repo: resolve packs at %s: %v — fix .curbpack.json or review a received pack directory", root, err))
	}
	surfaces, err := pathway.ProsePaths(packIDs)
	if err != nil {
		return usageErr(fmt.Sprintf("review --repo: compose pack surfaces: %v — fix pack selection (`curbpack packs doctor`) or review a received pack directory", err))
	}
	if len(surfaces) == 0 {
		return usageErr("review --repo: no governed documentation surfaces from packs — add annex_file/file_present/anti_placeholder rules or review a received pack directory")
	}

	var prior *review.Report
	if sincePath != "" {
		p, err := loadPriorReport(sincePath)
		if err != nil {
			return usageErr(err.Error())
		}
		prior = &p
	}

	if !jsonOut {
		tty.PrintHeader("curbpack review --repo")
	}
	fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Dim, "Offline in-repo document triage — not a product verdict."))
	if len(surfaces) <= 2 {
		fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Yellow,
			fmt.Sprintf("Scope-limited: only %d governed surface(s) from packs %s — use --packs for denser packs (e.g. cra-baseline).",
				len(surfaces), strings.Join(packIDs, ","))))
	}

	var subjectCommit string
	if head, err := gitutil.HeadSHA(root); err == nil {
		subjectCommit = head
	}

	rep, err := review.Run(review.Options{
		BundleRoot:     root,
		Writer:         os.Stdout,
		JSONOut:        jsonOut,
		Full:           full,
		Prior:          prior,
		ReferencesOnly: true,
		TriageSurfaces: surfaces,
		SubjectCommit:  subjectCommit,
	})
	if err != nil {
		return usageErr(err.Error())
	}
	if edgesPath != "" {
		loaded, err := review.LoadEdgesFile(edgesPath)
		if err != nil {
			return usageErr(err.Error())
		}
		rep, err = review.AttachEdges(rep, loaded)
		if err != nil {
			return usageErr(err.Error())
		}
	}
	if jsonOut {
		if err := review.WriteJSON(rep, os.Stdout); err != nil {
			return usageErr(err.Error())
		}
	}
	printReviewHPURLFragment(root, rep, true)
	if review.HasContradictions(rep) {
		fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Yellow, "Contradicted findings present — see triage note above."))
		return gatesErr()
	}
	return nil
}

// loadPriorReport reads a prior review --json report. Errors are usage/env (exit 2).
func loadPriorReport(path string) (review.Report, error) {
	path = filepath.Clean(strings.TrimSpace(path))
	st, err := os.Lstat(path)
	if err != nil {
		return review.Report{}, fmt.Errorf("review --since: cannot read prior report %s: %w", path, err)
	}
	if st.Mode()&os.ModeSymlink != 0 {
		return review.Report{}, fmt.Errorf("review --since: refuses symlink %s", path)
	}
	if !st.Mode().IsRegular() {
		return review.Report{}, fmt.Errorf("review --since: prior report must be a file: %s", path)
	}
	if st.Size() > review.MaxPriorReportBytes {
		return review.Report{}, fmt.Errorf("review --since: prior report exceeds size cap: %s", path)
	}
	f, err := os.Open(path)
	if err != nil {
		return review.Report{}, fmt.Errorf("review --since: cannot read prior report %s: %w", path, err)
	}
	defer f.Close()
	limited := io.LimitReader(f, review.MaxPriorReportBytes+1)
	data, err := io.ReadAll(limited)
	if err != nil {
		return review.Report{}, fmt.Errorf("review --since: cannot read prior report %s: %w", path, err)
	}
	if int64(len(data)) > review.MaxPriorReportBytes {
		return review.Report{}, fmt.Errorf("review --since: prior report exceeds size cap: %s", path)
	}
	var rep review.Report
	if err := json.Unmarshal(data, &rep); err != nil {
		return review.Report{}, fmt.Errorf("review --since: prior report is not valid JSON: %s: %v", path, err)
	}
	if rep.Schema != review.SchemaVersion {
		return review.Report{}, fmt.Errorf("review --since: schema mismatch: prior %q current %q", rep.Schema, review.SchemaVersion)
	}
	return rep, nil
}

func runVerifyChain(parentPath, childPath string) error {
	parent, err := loadPriorReport(parentPath)
	if err != nil {
		return usageErr(err.Error())
	}
	child, err := loadPriorReport(childPath)
	if err != nil {
		return usageErr(err.Error())
	}
	want := strings.TrimSpace(parent.RecordDigest)
	got := strings.TrimSpace(child.ParentRecordDigest)
	if want == "" {
		fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Yellow, "parent record_digest empty"))
		return gatesErr()
	}
	if got == "" {
		fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Yellow, "child parent_record_digest empty"))
		return gatesErr()
	}
	if got != want {
		fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Yellow, fmt.Sprintf("chain break: child parent_record_digest=%s parent record_digest=%s", got, want)))
		return gatesErr()
	}
	fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Dim, "record chain ok"))
	return nil
}

// printReviewHPURLFragment renders the offline HPURL fragment on stderr (CLI only; not in Report JSON).
func printReviewHPURLFragment(bundleRoot string, rep review.Report, repoMode bool) {
	if rep.SubjectStateHash == "" || rep.SubjectCommit == "" {
		return
	}
	sigHint := reviewSigHint(bundleRoot, rep, repoMode)
	frag := attest.FormatHPURLFragment(rep.SubjectStateHash, rep.SubjectCommit, sigHint)
	fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Dim, "HPURL fragment: "+frag))
}

func reviewSigHint(bundleRoot string, rep review.Report, repoMode bool) string {
	if repoMode {
		bind, _ := attest.LatestBind(bundleRoot)
		if s := strings.TrimSpace(bind.SSHSignature); s != "" {
			return truncateReviewSig(s)
		}
		return "unsigned"
	}
	ptrPath := filepath.Join(bundleRoot, "hpurl-pointer.json")
	b, err := os.ReadFile(ptrPath)
	if err != nil {
		return "unsigned"
	}
	var ptr struct {
		HPURL string `json:"hpurl"`
	}
	if json.Unmarshal(b, &ptr) == nil && strings.TrimSpace(ptr.HPURL) != "" {
		if parts, ok := attest.ParseHPURLFragment(ptr.HPURL); ok && strings.TrimSpace(parts.SigHint) != "" {
			return parts.SigHint
		}
	}
	return "unsigned"
}

func truncateReviewSig(s string) string {
	s = strings.TrimSpace(s)
	if len(s) > 32 {
		return s[:32]
	}
	return s
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
	// --batch already refuses --json above; header stays on stdout (no JSON redirection case).
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
