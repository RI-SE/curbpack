package cli

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/afelin/curbpack/internal/clock"
	"github.com/afelin/curbpack/internal/config"
	"github.com/afelin/curbpack/internal/gitutil"
	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/packs"
	"github.com/afelin/curbpack/internal/tty"
	"github.com/afelin/curbpack/internal/validate"
)

func cmdScan(args []string) error {
	if len(args) > 0 {
		return usageErr("scan: unknown argument " + args[0])
	}
	root, err := gitutil.RepoRoot("")
	if err != nil {
		return usageErr("must run inside a git repository")
	}

	packIDs, err := config.ResolvePackIDs(root, nil)
	if err != nil {
		return err
	}

	res, err := validate.Run(validate.Options{
		RepoRoot: root,
		PackIDs:  packIDs,
		Quiet:    true,
		ReadOnly: true,
	})
	if err != nil {
		return err
	}

	tty.PrintHeader("CURBPACK SCAN")
	fmt.Printf("%s\n", tty.C(tty.Bold+tty.Yellow, "Read-only — no files written, no hooks, no init. Not conformity assessment."))
	fmt.Printf("%s\n\n", tty.C(tty.Dim, "Diagnosis only — use curbpack check --score for readiness %."))

	product, source := productHint(root)
	fmt.Printf("Product hint: %s (%s)\n", product, source)
	fmt.Printf("Repo: %s\n", root)
	fmt.Printf("Packs: %s\n", strings.Join(packIDs, ", "))

	days := clock.DaysUntilUTC(clock.Art14ReportingStart)
	switch {
	case days > 0:
		fmt.Printf("Art 14 reporting clock: %d days until 2026-09-11\n", days)
	case days == 0:
		fmt.Println("Art 14 reporting clock: starts today (2026-09-11)")
	default:
		fmt.Printf("Art 14 reporting clock: started %d days ago (2026-09-11)\n", -days)
	}

	notStarted, failing := classifyFindings(res.Payload.Failures)
	fmt.Printf("\nOpen signals: %d failing · %d not started\n", len(failing), len(notStarted))

	limit := 5
	shown := 0
	for _, f := range failing {
		if shown >= limit {
			break
		}
		fmt.Printf("  ✘ [%s] %s — %s\n", f.Severity, f.GateID, shortFinding(f))
		shown++
	}
	for _, f := range notStarted {
		if shown >= limit {
			break
		}
		fmt.Printf("  ○ [%s] %s — %s (not started)\n", f.Severity, f.GateID, shortFinding(f))
		shown++
	}
	rest := len(failing) + len(notStarted) - shown
	if rest > 0 {
		fmt.Printf("  … and %d more\n", rest)
	}

	if res.Passed {
		fmt.Printf("\n%s\n", tty.C(tty.Green, "No open gate findings on this tree — still not certification."))
	} else {
		fmt.Printf("\n%s\n", tty.C(tty.Dim, "Next: curbpack fix --art14 · curbpack init · curbpack check --score"))
	}
	fmt.Printf("%s\n", tty.C(tty.Dim, "Prepares evidence for human review — not a conformity assessment."))
	return nil
}

func productHint(root string) (name, source string) {
	if n, ok := packs.RepoToken(root); ok {
		if _, err := os.Stat(filepath.Join(root, "package.json")); err == nil {
			return n, "package.json"
		}
		if _, err := os.Stat(filepath.Join(root, "go.mod")); err == nil {
			return n, "go.mod"
		}
		return n, "repo name"
	}
	if title := readmeTitle(root); title != "" {
		return title, "README"
	}
	return filepath.Base(root), "directory"
}

func readmeTitle(root string) string {
	b, err := os.ReadFile(filepath.Join(root, "README.md"))
	if err != nil {
		return ""
	}
	for _, line := range strings.Split(string(b), "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "# ") {
			return strings.TrimSpace(strings.TrimPrefix(line, "# "))
		}
	}
	return ""
}

func classifyFindings(failures []ir.Failure) (notStarted, failing []ir.Failure) {
	for _, f := range failures {
		desc := strings.ToLower(f.SanitizedDescription)
		if strings.Contains(desc, "scaffold body overlap") ||
			strings.Contains(desc, "missing") ||
			strings.Contains(desc, "too short") ||
			strings.Contains(desc, "too small") {
			notStarted = append(notStarted, f)
			continue
		}
		failing = append(failing, f)
	}
	return notStarted, failing
}

func shortFinding(f ir.Failure) string {
	if p := strings.TrimSpace(f.ASTCoordinates.TargetFile); p != "" {
		return p
	}
	if len(f.SanitizedDescription) > 72 {
		return f.SanitizedDescription[:69] + "..."
	}
	return f.SanitizedDescription
}
