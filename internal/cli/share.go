package cli

import (
	"fmt"
	"github.com/afelin/curbpack/internal/outwrite"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/afelin/curbpack/internal/attest"
	"github.com/afelin/curbpack/internal/clock"
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
	f, err := parseShareFlags(args)
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
	packIDs := f.packIDs
	skipPrepare := f.skipPrepare
	wantBundle := f.wantBundle
	wantReveal := f.wantReveal

	if _, _, err := clock.EvaluationAsOf(f.asOf); err != nil {
		return err
	}
	tty.PrintHeader("curbpack share")
	if !skipPrepare {
		if err := release.PrepareScaffolds(root, packIDs); err != nil {
			return err
		}
	}
	res, verr := validate.Run(validate.Options{RepoRoot: root, PackIDs: packIDs, Quiet: false, AsOf: f.asOf})
	checkFailed := verr != nil || !res.Passed
	if verr != nil {
		return verr
	}

	cp, err := exportx.WriteContextPackFromResult(root, packIDs, "", res)
	if err != nil {
		return err
	}
	tty.PrintStatus("context-pack", true, cp)

	bq, n, err := exportx.WriteBuyerQuestionsFromResult(root, packIDs, "", res)
	if err != nil {
		return err
	}
	tty.PrintStatus("buyer-questions", true, fmt.Sprintf("%s questions=%d", bq, n))

	extras, err := collectShareArtifacts(root, cp, bq)
	if err != nil {
		return err
	}

	var revealTarget string
	prepared := false
	onepager := filepath.Join(root, "review-pack", "buyer-onepager.html")
	if !skipPrepare {
		if err := release.Prepare(release.Options{
			RepoRoot:          root,
			IncludeBundle:     wantBundle,
			PackIDs:           packIDs,
			AllowFailingGates: true,
			Result:            &res,
			ExtraArtifacts:    extras,
		}); err != nil {
			return fmt.Errorf("prepare-release: %w", err)
		} else {
			prepared = true
		}
	} else if err := publishShareExtras(root, extras); err != nil {
		return err
	}
	for _, name := range sortedArtifactNames(extras) {
		printAttach(filepath.Join(root, "review-pack", name))
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
		bundlePath := filepath.Join(root, "review-pack", "evidence-bundle.html")
		var err error
		if !prepared {
			bundlePath, err = release.WriteEvidenceBundle(root, res)
		}
		if err != nil {
			return fmt.Errorf("evidence-bundle: %w", err)
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

// copyEvidenceHPURLPointerToReviewPack copies attest hpurl-pointer.json into review-pack/
// when present under .github/curbpack/evidence/. Absent file is not an error.
func copyEvidenceHPURLPointerToReviewPack(root string) (string, error) {
	src := filepath.Join(root, ".github", "curbpack", "evidence", "hpurl-pointer.json")
	if _, err := os.Stat(src); err != nil {
		if os.IsNotExist(err) {
			return "", nil
		}
		return "", err
	}
	return copyFileIntoReviewPack(root, src)
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

	if err := outwrite.Contain(root, src); err != nil {
		return "", err
	}
	st, err := os.Lstat(src)
	if err != nil {
		return "", err
	}
	if !st.Mode().IsRegular() {
		return "", fmt.Errorf("share source must be a regular file")
	}
	data, err := os.ReadFile(src)
	if err != nil {
		return "", err
	}
	if _, err := outwrite.SaveFile(root, filepath.Join("review-pack", filepath.Base(src)), "", data, 0644); err != nil {
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

func sortedArtifactNames(files map[string][]byte) []string {
	names := make([]string, 0, len(files))
	for name := range files {
		names = append(names, name)
	}
	sort.Strings(names)
	return names
}

func collectShareArtifacts(root string, sources ...string) (map[string][]byte, error) {
	files := map[string][]byte{}
	read := func(src string, optional bool) error {
		if err := outwrite.Contain(root, src); err != nil {
			return err
		}
		st, err := os.Lstat(src)
		if optional && os.IsNotExist(err) {
			return nil
		}
		if err != nil {
			return err
		}
		if !st.Mode().IsRegular() {
			return fmt.Errorf("share source must be a regular file")
		}
		raw, err := os.ReadFile(src)
		if err != nil {
			return err
		}
		files[filepath.Base(src)] = raw
		return nil
	}
	for _, src := range sources {
		if err := read(src, false); err != nil {
			return nil, err
		}
		if companion := shareArtifactCompanion(src); companion != "" {
			if err := read(companion, true); err != nil {
				return nil, err
			}
		}
	}
	if err := read(filepath.Join(root, ".github", "curbpack", "evidence", "hpurl-pointer.json"), true); err != nil {
		return nil, err
	}
	return files, nil
}

func publishShareExtras(root string, files map[string][]byte) error {
	lock, err := outwrite.Acquire(root)
	if err != nil {
		return err
	}
	defer lock.Release()
	var artifacts []outwrite.Artifact
	for _, name := range sortedArtifactNames(files) {
		artifacts = append(artifacts, outwrite.Artifact{PermittedRoot: root, Path: filepath.Join(root, "review-pack", name), Data: files[name]})
	}
	return outwrite.Publish(artifacts)
}
