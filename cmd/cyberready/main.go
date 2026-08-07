package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/afelin/cyberready/internal/ask"
	"github.com/afelin/cyberready/internal/attest"
	"github.com/afelin/cyberready/internal/config"
	"github.com/afelin/cyberready/internal/gitutil"
	"github.com/afelin/cyberready/internal/packs"
	"github.com/afelin/cyberready/internal/packscmd"
	"github.com/afelin/cyberready/internal/release"
	"github.com/afelin/cyberready/internal/sbom"
	"github.com/afelin/cyberready/internal/sock"
	"github.com/afelin/cyberready/internal/tty"
	"github.com/afelin/cyberready/internal/validate"
	"github.com/afelin/cyberready/internal/vex"
)

const version = "0.2.0"

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(1)
	}
	cmd := os.Args[1]
	args := os.Args[2:]

	var err error
	switch cmd {
	case "help", "-h", "--help":
		usage()
	case "version", "-v", "--version":
		fmt.Println("cyberready", version)
	case "init":
		err = cmdInit(args)
	case "check":
		err = cmdCheck(args)
	case "validate":
		err = cmdValidate(args)
	case "prepare-release":
		err = cmdPrepareRelease(args)
	case "packs":
		err = cmdPacks(args)
	case "ask":
		err = cmdAsk(args)
	case "attest":
		err = cmdAttest(args)
	case "view":
		err = attest.View("")
	case "sock":
		err = cmdSock(args)
	default:
		fmt.Printf("%s\n\n", tty.C(tty.Red, "Unknown command '"+cmd+"'"))
		usage()
		os.Exit(1)
	}
	if err != nil {
		fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Red, err.Error()))
		os.Exit(1)
	}
}

func usage() {
	fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Bold+tty.Cyan, "CyberReady+ "+version))
	fmt.Fprintf(os.Stderr, "Regulation-agnostic evidence CLI — packs encode policy. Not a certification product.\n\n")
	fmt.Fprintf(os.Stderr, "Usage: cyberready <command> [args]\n\n")
	fmt.Fprintf(os.Stderr, "Commands:\n")
	fmt.Fprintf(os.Stderr, "  init [--packs a,b] [--hooks]  Scaffold config + pack-path stubs (+ optional pre-commit)\n")
	fmt.Fprintf(os.Stderr, "  check [--diff] [--json]       Daily loop: validate + thermometer + cache + Action Report\n")
	fmt.Fprintf(os.Stderr, "  validate [--delta] [--json]   Pack gates (JSON + markdown dual-rep)\n")
	fmt.Fprintf(os.Stderr, "  prepare-release               Write review-pack/ + CycloneDX/VEX evidence\n")
	fmt.Fprintf(os.Stderr, "  packs list|update|import      Embedded packs; update/import helpers\n")
	fmt.Fprintf(os.Stderr, "  ask [file|-] [--propose]      Explain GateFailure JSON (optional --propose)\n")
	fmt.Fprintf(os.Stderr, "  attest                        Reproducible Git Notes capsule + HPURL pointer\n")
	fmt.Fprintf(os.Stderr, "  view                          Show Git Notes capsule for HEAD\n")
	fmt.Fprintf(os.Stderr, "  sock                          Unix socket validate_delta server (optional Coreward)\n")
}

func cmdInit(args []string) error {
	tty.PrintHeader("INITIALIZING COMPLIANCE WORKSPACE")
	root, err := gitutil.RepoRoot("")
	if err != nil {
		return fmt.Errorf("workspace is not a git repository")
	}
	tty.PrintStatus("Git repository", true, root)

	crPath := filepath.Join(root, ".github", "cyberready")
	_ = os.MkdirAll(filepath.Join(crPath, "policies"), 0o755)
	_ = os.MkdirAll(filepath.Join(crPath, "cache"), 0o755)
	_ = os.MkdirAll(filepath.Join(crPath, "evidence"), 0o755)

	packList := []string{"cra-baseline"}
	hooks := false
	explicitPacks := false
	for i := 0; i < len(args); i++ {
		a := args[i]
		switch {
		case a == "--packs" && i+1 < len(args):
			packList = config.ParsePacksFlag(args[i+1])
			explicitPacks = true
			i++
		case strings.HasPrefix(a, "--packs="):
			packList = config.ParsePacksFlag(strings.TrimPrefix(a, "--packs="))
			explicitPacks = true
		case a == "--medtech":
			// Deprecated alias → packs list including medtech overlay
			if !explicitPacks {
				packList = []string{"cra-baseline", "medtech-iec62304"}
			} else {
				packList = appendUnique(packList, "medtech-iec62304")
			}
			fmt.Printf("%s\n", tty.C(tty.Yellow, "[!] --medtech is deprecated; prefer --packs cra-baseline,medtech-iec62304"))
		case a == "--hooks":
			hooks = true
		}
	}
	if len(packList) == 0 {
		packList = []string{"cra-baseline"}
	}

	// Validate pack ids early
	for _, id := range packList {
		if _, err := packs.LoadPack(id); err != nil {
			return err
		}
	}

	cfg := config.File{
		Packs:   packList,
		Hooks:   hooks,
		Version: version,
		Claim:   "Prepares evidence for human review — not a conformity assessment.",
	}
	cfgPath := filepath.Join(root, ".cyberready.json")
	if _, err := os.Stat(cfgPath); os.IsNotExist(err) {
		if err := config.Write(root, cfg); err != nil {
			return err
		}
		tty.PrintStatus(".cyberready.json", true, "created packs="+strings.Join(packList, ","))
	} else {
		tty.PrintStatus(".cyberready.json", true, "exists (not overwritten)")
	}

	// Scaffold only files referenced by active pack rules (aligned annex paths)
	paths, err := packs.ScaffoldPaths(packList)
	if err != nil {
		return err
	}
	for _, rel := range paths {
		p := filepath.Join(root, rel)
		if _, err := os.Stat(p); err == nil {
			tty.PrintStatus("stub "+rel, true, "found")
			continue
		}
		if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
			return err
		}
		body := packs.DefaultScaffoldBody(rel)
		if err := os.WriteFile(p, []byte(body), 0o644); err != nil {
			return err
		}
		tty.PrintStatus("stub "+rel, true, "created")
	}

	_ = os.MkdirAll(filepath.Join(root, "proof"), 0o755)
	_ = os.WriteFile(filepath.Join(root, "proof", "index.html"), []byte(release.ProofPageHTML()), 0o644)
	tty.PrintStatus("proof/index.html", true, "HPURL viewer + verify")

	if hooks {
		if err := installPreCommitHook(root); err != nil {
			return err
		}
		tty.PrintStatus("pre-commit hook", true, "cyberready check")
	}

	fmt.Printf("\n%s\n", tty.C(tty.Bold+tty.Green, "[+] Init complete. Next: cyberready check"))
	return nil
}

func appendUnique(in []string, id string) []string {
	for _, x := range in {
		if x == id {
			return in
		}
	}
	return append(in, id)
}

func installPreCommitHook(root string) error {
	hookDir := filepath.Join(root, ".git", "hooks")
	if err := os.MkdirAll(hookDir, 0o755); err != nil {
		return err
	}
	path := filepath.Join(hookDir, "pre-commit")
	script := `#!/bin/sh
# CyberReady — fail commit on high/critical gate findings
if command -v cyberready >/dev/null 2>&1; then
  cyberready check || exit 1
elif [ -x ./bin/cyberready ]; then
  ./bin/cyberready check || exit 1
elif [ -x ./cyberready ]; then
  ./cyberready check || exit 1
else
  echo "cyberready not on PATH — skip pre-commit check" >&2
fi
exit 0
`
	if err := os.WriteFile(path, []byte(script), 0o755); err != nil {
		return err
	}
	// Reflect hooks=true in config if file exists
	if cfg, err := config.Load(root); err == nil && cfg != nil {
		cfg.Hooks = true
		_ = config.Write(root, *cfg)
	}
	return nil
}

func parseValidateFlags(args []string) (packIDs []string, jsonOut, diffOnly bool) {
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--pack":
			if i+1 < len(args) {
				packIDs = append(packIDs, args[i+1])
				i++
			}
		case "--packs":
			if i+1 < len(args) {
				packIDs = append(packIDs, config.ParsePacksFlag(args[i+1])...)
				i++
			}
		case "--json":
			jsonOut = true
		case "--diff", "--delta":
			diffOnly = true
		}
	}
	return packIDs, jsonOut, diffOnly
}

func cmdCheck(args []string) error {
	tty.PrintHeader("CYBERREADY CHECK")
	root, err := gitutil.RepoRoot("")
	if err != nil {
		return fmt.Errorf("must run inside a git repository")
	}
	packIDs, jsonOut, diffOnly := parseValidateFlags(args)
	res, err := validate.Run(validate.Options{RepoRoot: root, PackIDs: packIDs, DiffOnly: diffOnly})
	if err != nil {
		return err
	}
	if jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		_ = enc.Encode(res.Payload)
	} else {
		if tty.IsTerminal {
			tty.RenderThermometer(res.Score)
		}
		fmt.Println(res.ActionReport)
		if res.SkippedRules > 0 {
			fmt.Printf("%s\n", tty.C(tty.Dim, fmt.Sprintf("diff mode skipped %d rules", res.SkippedRules)))
		}
		fmt.Printf("%s\n", tty.C(tty.Dim, "cache: .github/cyberready/cache/latest_*.json"))
	}
	if !res.Passed {
		os.Exit(1)
	}
	return nil
}

func cmdValidate(args []string) error {
	tty.PrintHeader("EXECUTING COMPLIANCE GATES")
	root, err := gitutil.RepoRoot("")
	if err != nil {
		return fmt.Errorf("must run inside a git repository")
	}
	packIDs, jsonOut, diffOnly := parseValidateFlags(args)
	res, err := validate.Run(validate.Options{RepoRoot: root, PackIDs: packIDs, DiffOnly: diffOnly})
	if err != nil {
		return err
	}
	if jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		_ = enc.Encode(res.Payload)
	} else {
		if tty.IsTerminal {
			tty.RenderThermometer(res.Score)
		}
		if !res.Passed {
			fmt.Printf("\n%s\n", tty.C(tty.Bold+tty.Magenta, "--- DUAL-REPRESENTATION OUTPUT ---"))
			fmt.Println(validate.SemanticMarkdown(res.Payload))
		} else {
			fmt.Printf("\n%s\n", tty.C(tty.BGGreen, "[✔] ALL DETERMINISTIC GATES PASSED"))
		}
	}
	if !res.Passed {
		os.Exit(1)
	}
	return nil
}

func cmdPrepareRelease(args []string) error {
	tty.PrintHeader("PREPARE RELEASE REVIEW PACK")
	root, err := gitutil.RepoRoot("")
	if err != nil {
		return err
	}
	var packIDs []string
	out := ""
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--pack":
			if i+1 < len(args) {
				packIDs = append(packIDs, args[i+1])
				i++
			}
		case "--packs":
			if i+1 < len(args) {
				packIDs = append(packIDs, config.ParsePacksFlag(args[i+1])...)
				i++
			}
		case "--out":
			if i+1 < len(args) {
				out = args[i+1]
				i++
			}
		}
	}
	return release.Prepare(release.Options{RepoRoot: root, PackIDs: packIDs, OutDir: out})
}

func cmdPacks(args []string) error {
	if len(args) == 0 {
		return packscmd.List()
	}
	switch args[0] {
	case "list":
		return packscmd.List()
	case "update":
		return packscmd.UpdateStub()
	case "import":
		src := ""
		if len(args) > 1 {
			src = args[1]
		}
		return packscmd.ImportAirGap(src)
	default:
		return fmt.Errorf("unknown packs subcommand %q (list|update|import)", args[0])
	}
}

func cmdAsk(args []string) error {
	propose := false
	path := ""
	for _, a := range args {
		if a == "--propose" {
			propose = true
			continue
		}
		if !strings.HasPrefix(a, "-") {
			path = a
		}
	}
	return ask.Run(path, propose)
}

func cmdAttest(args []string) error {
	tty.PrintHeader("CRYPTO ATTESTATION ENGINE")
	allowDirty := false
	for _, a := range args {
		if a == "--allow-dirty" {
			allowDirty = true
		}
	}
	root, err := gitutil.RepoRoot("")
	if err != nil {
		return err
	}
	if !allowDirty && gitutil.IsDirty(root) {
		return fmt.Errorf("OCC conflict: working directory has uncommitted files")
	}
	// Regenerate evidence digests as part of attest (after dirty gate)
	_, _, _ = sbom.WriteCycloneDX(root, "")
	if res, err := validate.Run(validate.Options{RepoRoot: root, Quiet: true}); err == nil {
		doc := vex.FromGateFailures(filepath.Base(root), res.Payload)
		_, _ = vex.Write(root, doc, "")
	}
	_, err = attest.Run(attest.Options{RepoRoot: root, AllowDirty: true})
	return err
}

func cmdSock(args []string) error {
	path := ""
	root := ""
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--path":
			if i+1 < len(args) {
				path = args[i+1]
				i++
			}
		case "--repo":
			if i+1 < len(args) {
				root = args[i+1]
				i++
			}
		}
	}
	if root == "" {
		var err error
		root, err = gitutil.RepoRoot("")
		if err != nil {
			root, _ = os.Getwd()
		}
	}
	return sock.Serve(path, root)
}
