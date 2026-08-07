package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/afelin/cyberready/internal/ask"
	"github.com/afelin/cyberready/internal/attest"
	"github.com/afelin/cyberready/internal/gitutil"
	"github.com/afelin/cyberready/internal/packscmd"
	"github.com/afelin/cyberready/internal/release"
	"github.com/afelin/cyberready/internal/sock"
	"github.com/afelin/cyberready/internal/tty"
	"github.com/afelin/cyberready/internal/validate"
)

const version = "0.1.0"

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
	fmt.Fprintf(os.Stderr, "Local-first evidence CLI — prepares review packs for humans. Not a certification product.\n\n")
	fmt.Fprintf(os.Stderr, "Usage: cyberready <command> [args]\n\n")
	fmt.Fprintf(os.Stderr, "Commands:\n")
	fmt.Fprintf(os.Stderr, "  init              Scaffold .cyberready.json + annex stubs\n")
	fmt.Fprintf(os.Stderr, "  validate          Run embedded pack gates (JSON + markdown dual-rep)\n")
	fmt.Fprintf(os.Stderr, "  prepare-release   Write review-pack/ (Annex VII, reports, buyer HTML)\n")
	fmt.Fprintf(os.Stderr, "  packs list        List embedded packs + watchlist\n")
	fmt.Fprintf(os.Stderr, "  packs update      Pack update channel stub / optional URL fetch\n")
	fmt.Fprintf(os.Stderr, "  packs import DIR  Air-gap import of pack JSON\n")
	fmt.Fprintf(os.Stderr, "  ask [file|-]      Explain GateFailure JSON (optional --propose)\n")
	fmt.Fprintf(os.Stderr, "  attest            Git Notes Merkle capsule + SSH-agent (best-effort)\n")
	fmt.Fprintf(os.Stderr, "  view              Show Git Notes capsule for HEAD\n")
	fmt.Fprintf(os.Stderr, "  sock              Unix socket validate_delta server (Coreward bridge)\n")
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

	packs := []string{"cra-baseline"}
	for _, a := range args {
		if a == "--medtech" {
			packs = append(packs, "medtech-iec62304")
		}
	}
	cfg := map[string]any{
		"packs":   packs,
		"version": version,
		"claim":   "Prepares evidence for human review — not a conformity assessment.",
	}
	b, _ := json.MarshalIndent(cfg, "", "  ")
	cfgPath := filepath.Join(root, ".cyberready.json")
	if _, err := os.Stat(cfgPath); os.IsNotExist(err) {
		if err := os.WriteFile(cfgPath, append(b, '\n'), 0o644); err != nil {
			return err
		}
		tty.PrintStatus(".cyberready.json", true, "created")
	} else {
		tty.PrintStatus(".cyberready.json", true, "exists")
	}

	// Minimal CRA stubs at repo root (MVP compat) + annex path via prepare-release
	for _, name := range []string{"risk_assessment.md", "user_manual.md", "support_rationale.md"} {
		p := filepath.Join(root, name)
		if _, err := os.Stat(p); os.IsNotExist(err) {
			_ = os.WriteFile(p, []byte("# "+name+"\n\nDraft — expand via prepare-release annex templates.\n"), 0o644)
			tty.PrintStatus("CRA stub "+name, true, "created")
		} else {
			tty.PrintStatus("CRA stub "+name, true, "found")
		}
	}

	_ = os.MkdirAll(filepath.Join(root, "proof"), 0o755)
	_ = os.WriteFile(filepath.Join(root, "proof", "index.html"), []byte(release.ProofPageHTML()), 0o644)
	tty.PrintStatus("proof/index.html", true, "HPURL viewer")

	fmt.Printf("\n%s\n", tty.C(tty.Bold+tty.Green, "[+] Init complete. Next: cyberready prepare-release"))
	return nil
}

func cmdValidate(args []string) error {
	tty.PrintHeader("EXECUTING COMPLIANCE GATES")
	root, err := gitutil.RepoRoot("")
	if err != nil {
		return fmt.Errorf("must run inside a git repository")
	}
	var packIDs []string
	jsonOut := false
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--pack":
			if i+1 < len(args) {
				packIDs = append(packIDs, args[i+1])
				i++
			}
		case "--json":
			jsonOut = true
		}
	}
	res, err := validate.Run(validate.Options{RepoRoot: root, PackIDs: packIDs})
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
	_, err := attest.Run(attest.Options{AllowDirty: allowDirty})
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
