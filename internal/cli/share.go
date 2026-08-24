package cli

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

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
	reviewCP, err := copyShareArtifactToReviewPack(root, cp)
	if err != nil {
		return err
	}
	printAttach(reviewCP)

	bq, n, err := exportx.WriteBuyerQuestions(root, packIDs, "")
	if err != nil {
		return err
	}
	tty.PrintStatus("buyer-questions", true, fmt.Sprintf("%s questions=%d", bq, n))
	reviewBQ, err := copyShareArtifactToReviewPack(root, bq)
	if err != nil {
		return err
	}
	printAttach(reviewBQ)

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

// copyShareArtifactToReviewPack copies a cache share artifact into review-pack/
// (and its .md/.json companion when present). Cache copies stay (SoR for pathway/MCP).
func copyShareArtifactToReviewPack(root, src string) (string, error) {
	dest, err := copyFileIntoReviewPack(root, src)
	if err != nil {
		return "", err
	}
	if companion := shareArtifactCompanion(src); companion != "" {
		if _, err := os.Stat(companion); err == nil {
			if _, cerr := copyFileIntoReviewPack(root, companion); cerr != nil {
				return "", cerr
			}
		}
	}
	return dest, nil
}

func copyFileIntoReviewPack(root, src string) (string, error) {
	dest := filepath.Join(root, "review-pack", filepath.Base(src))
	if err := os.MkdirAll(filepath.Dir(dest), 0o755); err != nil {
		return "", err
	}
	data, err := os.ReadFile(src)
	if err != nil {
		return "", err
	}
	if err := os.WriteFile(dest, data, 0o644); err != nil {
		return "", err
	}
	return dest, nil
}

func shareArtifactCompanion(src string) string {
	ext := strings.ToLower(filepath.Ext(src))
	stem := strings.TrimSuffix(src, filepath.Ext(src))
	switch ext {
	case ".json":
		return stem + ".md"
	case ".md", ".markdown":
		return stem + ".json"
	default:
		return ""
	}
}
