package cli

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/afelin/curbpack/internal/attest"
	"github.com/afelin/curbpack/internal/exportx"
	"github.com/afelin/curbpack/internal/gitutil"
	"github.com/afelin/curbpack/internal/platform"
	"github.com/afelin/curbpack/internal/release"
	"github.com/afelin/curbpack/internal/tty"
	"github.com/afelin/curbpack/internal/validate"
)

// cmdShare is a thin recipe wrapper: check → context-pack → buyer-questions → prepare-release.
// No new evaluation logic. Exit non-zero if check is red; still writes context-pack for the red state.
func cmdShare(args []string) error {
	root, err := gitutil.RepoRoot("")
	if err != nil {
		return usageErr("must run inside a git repository")
	}
	f, err := parseShareFlags(args)
	if err != nil {
		return err
	}
	packIDs := f.packIDs
	skipPrepare := f.skipPrepare
	wantBundle := f.wantBundle
	wantReveal := f.wantReveal

	tty.PrintHeader("curbpack share")
	res, verr := validate.Run(validate.Options{RepoRoot: root, PackIDs: packIDs, Quiet: false})
	checkFailed := verr != nil || !res.Passed
	if verr != nil {
		fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Dim, "check error: "+verr.Error()+" — still writing context-pack"))
	}

	cp, err := exportx.WriteContextPack(root, packIDs, "")
	if err != nil {
		return err
	}
	tty.PrintStatus("context-pack", true, cp)
	printAttach(cp)

	bq, n, err := exportx.WriteBuyerQuestions(root, packIDs, "")
	if err != nil {
		return err
	}
	tty.PrintStatus("buyer-questions", true, fmt.Sprintf("%s questions=%d", bq, n))
	printAttach(bq)

	var revealTarget string
	prepared := false
	onepager := filepath.Join(root, "review-pack", "buyer-onepager.html")
	if !skipPrepare {
		if err := release.Prepare(release.Options{
			RepoRoot:          root,
			PackIDs:           packIDs,
			AllowFailingGates: true,
		}); err != nil {
			fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Dim, "prepare-release: "+err.Error()))
		} else {
			prepared = true
		}
	}

	for _, line := range shareLadderLines(root, res.Score, res.Passed) {
		fmt.Printf("%s\n", tty.C(tty.Yellow, line))
	}

	if prepared {
		tty.PrintStatus("prepare-release", true, "review-pack (human attest next)")
		printAttach(onepager)
		revealTarget = onepager
	}

	if wantBundle {
		bundlePath, err := release.WriteEvidenceBundle(root, res)
		if err != nil {
			fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Dim, "evidence-bundle: "+err.Error()))
		} else {
			tty.PrintStatus("evidence-bundle", true, bundlePath)
			printAttach(bundlePath)
			revealTarget = bundlePath
		}
	}

	if wantReveal {
		if revealTarget != "" {
			_ = platform.RevealInFileManager(revealTarget)
		} else {
			fmt.Printf("%s\n", tty.C(tty.Dim, "share --reveal: nothing to reveal (need prepare-release output or --bundle)"))
		}
	}

	fmt.Printf("%s\n", tty.C(tty.Dim, "Recipe done. Human attest when ready — never auto-attest. Not a conformity assessment."))
	if checkFailed {
		return gatesErr()
	}
	return nil
}

// shareLadderLines returns share_stale / attest_commit_behind as the first post-prepare
// status lines when those conditions hold. Bundle still writes (no extra flag).
func shareLadderLines(root string, score int, passed bool) []string {
	bind, _ := attest.LatestBind(root)
	var lines []string
	sig, detail := release.ShareStaleReport(root, bind, score, passed)
	if sig == "share_stale" {
		lines = append(lines, "share_stale: "+detail)
	}
	head, err := gitutil.HeadSHA(root)
	if err == nil && bind.Found && bind.CommitSHA != head {
		lines = append(lines, fmt.Sprintf("attest_commit_behind: bind %s ≠ HEAD %s", shortSHA(bind.CommitSHA), shortSHA(head)))
	}
	return lines
}

func shortSHA(s string) string {
	if len(s) > 12 {
		return s[:12] + "…"
	}
	return s
}

// printAttach prints an identical abs-path Attach line on all OS.
func printAttach(path string) {
	abs, err := filepath.Abs(path)
	if err != nil {
		abs = path
	}
	fmt.Printf("Attach: %s\n", abs)
}
