package cli

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/afelin/curbpack/internal/config"
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
	var packIDs []string
	skipPrepare := false
	wantBundle := false
	wantReveal := false
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--packs":
			if i+1 < len(args) {
				packIDs = append(packIDs, config.ParsePacksFlag(args[i+1])...)
				i++
			}
		case "--skip-prepare-release":
			skipPrepare = true
		case "--bundle":
			wantBundle = true
		case "--reveal":
			wantReveal = true
		}
	}

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
	if !skipPrepare {
		if err := release.Prepare(release.Options{
			RepoRoot:          root,
			PackIDs:           packIDs,
			AllowFailingGates: true,
		}); err != nil {
			fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Dim, "prepare-release: "+err.Error()))
		} else {
			onepager := filepath.Join(root, "review-pack", "buyer-onepager.html")
			tty.PrintStatus("prepare-release", true, "review-pack (human attest next)")
			printAttach(onepager)
			revealTarget = onepager
		}
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

	if wantReveal && revealTarget != "" {
		_ = platform.RevealInFileManager(revealTarget)
	}

	fmt.Printf("%s\n", tty.C(tty.Dim, "Recipe done. Human attest when ready — never auto-attest. Not a conformity assessment."))
	if checkFailed {
		return gatesErr()
	}
	return nil
}

// printAttach prints an identical abs-path Attach line on all OS.
func printAttach(path string) {
	abs, err := filepath.Abs(path)
	if err != nil {
		abs = path
	}
	fmt.Printf("Attach: %s\n", abs)
}
