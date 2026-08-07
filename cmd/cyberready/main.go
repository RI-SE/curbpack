package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/afelin/cyberready/internal/ask"
	"github.com/afelin/cyberready/internal/attest"
	"github.com/afelin/cyberready/internal/config"
	"github.com/afelin/cyberready/internal/demo"
	"github.com/afelin/cyberready/internal/doctor"
	"github.com/afelin/cyberready/internal/formhints"
	"github.com/afelin/cyberready/internal/gitutil"
	"github.com/afelin/cyberready/internal/packs"
	"github.com/afelin/cyberready/internal/packscmd"
	"github.com/afelin/cyberready/internal/release"
	"github.com/afelin/cyberready/internal/remediation"
	"github.com/afelin/cyberready/internal/sbom"
	"github.com/afelin/cyberready/internal/skilldata"
	"github.com/afelin/cyberready/internal/sock"
	"github.com/afelin/cyberready/internal/tty"
	"github.com/afelin/cyberready/internal/validate"
	"github.com/afelin/cyberready/internal/vex"
)

// version is set at release build via -ldflags "-X main.version=..."
var version = "0.3.0"

// Stable exit codes (document in README):
//
//	0 = pass / success
//	1 = gate failures (or operational error during check/validate)
//	2 = usage / environment (unknown command, bad flags, not a git repo when required)
const (
	exitOK    = 0
	exitGates = 1
	exitUsage = 2
)

type exitError struct {
	code int
	msg  string
}

func (e *exitError) Error() string { return e.msg }

func usageErr(msg string) error { return &exitError{code: exitUsage, msg: msg} }
func gatesErr() error           { return &exitError{code: exitGates, msg: ""} }

func main() {
	args := os.Args[1:]
	var err error

	if len(args) == 0 {
		err = cmdDefault()
	} else {
		cmd := args[0]
		rest := args[1:]
		switch cmd {
		case "help", "-h", "--help":
			usage()
		case "version", "-v", "--version":
			fmt.Println("cyberready", version)
		case "init":
			err = cmdInit(rest)
		case "check":
			err = cmdCheck(rest)
		case "validate":
			err = cmdValidate(rest)
		case "prepare-release":
			err = cmdPrepareRelease(rest)
		case "packs":
			err = cmdPacks(rest)
		case "ask":
			err = cmdAsk(rest)
		case "attest":
			err = cmdAttest(rest)
		case "view":
			err = attest.View("")
		case "sock":
			err = cmdSock(rest)
		case "doctor":
			err = doctor.Run(doctor.Options{Version: version})
		case "demo":
			err = cmdDemo(rest)
		default:
			fmt.Printf("%s\n\n", tty.C(tty.Red, "Unknown command '"+cmd+"'"))
			usage()
			os.Exit(exitUsage)
		}
	}

	if err != nil {
		var ee *exitError
		if errors.As(err, &ee) {
			if ee.msg != "" {
				fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Red, ee.msg))
			}
			os.Exit(ee.code)
		}
		fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Red, err.Error()))
		os.Exit(exitGates)
	}
}

// cmdDefault: bare `cyberready` → doctor if not inited, else check (one mental model).
func cmdDefault() error {
	root, err := gitutil.RepoRoot("")
	if err != nil {
		return doctor.Run(doctor.Options{Version: version})
	}
	cfg, err := config.Load(root)
	if err != nil {
		return usageErr(err.Error())
	}
	if cfg == nil {
		return doctor.Run(doctor.Options{Version: version})
	}
	return cmdCheck(nil)
}

func usage() {
	fmt.Fprintf(os.Stderr, "%s\n", tty.C(tty.Bold+tty.Cyan, "CyberReady+ "+version))
	fmt.Fprintf(os.Stderr, "Regulation-agnostic evidence CLI — packs encode policy. Not a certification product.\n\n")
	fmt.Fprintf(os.Stderr, "Usage: cyberready [<command>] [args]\n")
	fmt.Fprintf(os.Stderr, "  (no command)                  doctor if uninitialized, else check\n\n")
	fmt.Fprintf(os.Stderr, "Commands:\n")
	fmt.Fprintf(os.Stderr, "  doctor                         Environment confidence (PATH, packs, hooks)\n")
	fmt.Fprintf(os.Stderr, "  demo [--keep]                  Safe sandbox: temp git + house-policy check\n")
	fmt.Fprintf(os.Stderr, "  init [--packs a,b] [--hooks] [--skill] [--ide]\n")
	fmt.Fprintf(os.Stderr, "                                 Scaffold config + stubs (+ hook/skill/tasks)\n")
	fmt.Fprintf(os.Stderr, "  check [--diff] [--json] [--form-hints] [--apply-stub] [--heal]\n")
	fmt.Fprintf(os.Stderr, "                                 Daily loop; --heal = hints→stub→re-check (max 3)\n")
	fmt.Fprintf(os.Stderr, "  validate [--delta] [--json]   Pack gates (JSON + markdown dual-rep)\n")
	fmt.Fprintf(os.Stderr, "  prepare-release               Write review-pack/ + CycloneDX/VEX evidence\n")
	fmt.Fprintf(os.Stderr, "  packs list|update|import      Embedded packs; update/import helpers\n")
	fmt.Fprintf(os.Stderr, "  ask [file|-] [--propose]      Explain GateFailure JSON (optional --propose)\n")
	fmt.Fprintf(os.Stderr, "  attest                        Reproducible Git Notes capsule + HPURL pointer\n")
	fmt.Fprintf(os.Stderr, "  view                          Show Git Notes capsule for HEAD\n")
	fmt.Fprintf(os.Stderr, "  sock                          Unix socket validate_delta server (optional Coreward)\n\n")
	fmt.Fprintf(os.Stderr, "Exit codes: 0=pass  1=gates/error  2=usage/env\n")
}

func cmdDemo(args []string) error {
	keep := false
	out := ""
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--keep":
			keep = true
		case "--out":
			if i+1 < len(args) {
				out = args[i+1]
				i++
			}
		}
	}
	return demo.Run(demo.Options{KeepDir: keep, OutDir: out, Version: version})
}

func cmdInit(args []string) error {
	tty.PrintHeader("INITIALIZING COMPLIANCE WORKSPACE")
	root, err := gitutil.RepoRoot("")
	if err != nil {
		return usageErr("workspace is not a git repository")
	}
	tty.PrintStatus("Git repository", true, root)

	crPath := filepath.Join(root, ".github", "cyberready")
	_ = os.MkdirAll(filepath.Join(crPath, "policies"), 0o755)
	_ = os.MkdirAll(filepath.Join(crPath, "cache"), 0o755)
	_ = os.MkdirAll(filepath.Join(crPath, "evidence"), 0o755)

	// Cold-start default: house-policy (lowest regulatory anxiety) unless --packs set.
	packList := []string{"house-policy"}
	hooks := false
	skill := false
	ide := false
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
			if !explicitPacks {
				packList = []string{"cra-baseline", "medtech-iec62304"}
			} else {
				packList = appendUnique(packList, "medtech-iec62304")
			}
			fmt.Printf("%s\n", tty.C(tty.Yellow, "[!] --medtech is deprecated; prefer --packs cra-baseline,medtech-iec62304"))
		case a == "--hooks":
			hooks = true
		case a == "--skill":
			skill = true
		case a == "--ide":
			ide = true
		}
	}
	if len(packList) == 0 {
		packList = []string{"house-policy"}
	}

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
		tty.PrintStatus("pre-commit hook", true, "cyberready check --heal")
	}

	if skill {
		dest, err := skilldata.Install(root)
		if err != nil {
			return err
		}
		tty.PrintStatus("Cursor skill", true, dest)
	}

	if ide {
		dest, err := skilldata.WriteIDETasks(root)
		if err != nil {
			return err
		}
		tty.PrintStatus("VS Code tasks", true, dest)
	}

	fmt.Printf("\n%s\n", tty.C(tty.Bold+tty.Green, "[+] Init complete. Next: cyberready check"))
	fmt.Printf("%s\n", tty.C(tty.Dim, "Prepares evidence for human review — not a conformity assessment."))
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
# --heal: create missing stubs only (never overwrite filled docs; never attest)
if command -v cyberready >/dev/null 2>&1; then
  cyberready check --heal || exit 1
elif [ -x ./bin/cyberready ]; then
  ./bin/cyberready check --heal || exit 1
elif [ -x ./cyberready ]; then
  ./cyberready check --heal || exit 1
else
  echo "cyberready not on PATH — skip pre-commit check" >&2
fi
exit 0
`
	if err := os.WriteFile(path, []byte(script), 0o755); err != nil {
		return err
	}
	if cfg, err := config.Load(root); err == nil && cfg != nil {
		cfg.Hooks = true
		_ = config.Write(root, *cfg)
	}
	return nil
}

func parseValidateFlags(args []string) (packIDs []string, jsonOut, diffOnly, formHints, applyStub, heal bool) {
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
		case "--form-hints":
			formHints = true
		case "--apply-stub":
			applyStub = true
			formHints = true // apply implies show hints
		case "--heal":
			heal = true
			applyStub = true
			formHints = true
		}
	}
	return packIDs, jsonOut, diffOnly, formHints, applyStub, heal
}

const healMaxRounds = 3

func cmdCheck(args []string) error {
	root, err := gitutil.RepoRoot("")
	if err != nil {
		return usageErr("must run inside a git repository")
	}
	packIDs, jsonOut, diffOnly, wantHints, applyStub, heal := parseValidateFlags(args)

	if !jsonOut {
		tty.PrintHeader("CYBERREADY CHECK")
	}

	var res validate.Result
	var lastHints []formhints.Hint
	for round := 0; round <= healMaxRounds; round++ {
		res, err = validate.Run(validate.Options{RepoRoot: root, PackIDs: packIDs, DiffOnly: diffOnly, Quiet: jsonOut})
		if err != nil {
			return err
		}
		if res.Passed || !heal || round == healMaxRounds {
			break
		}
		// Heal: form-hints → apply-stub (missing only) → persist cache → re-check.
		// Never auto-attest / never invent approved legal prose.
		cache, _ := remediation.Load(root)
		hints := formhints.ForFailuresCached(res.Payload.Failures, cache)
		hints, err = formhints.ApplyStubs(root, hints)
		if err != nil {
			return err
		}
		_ = formhints.PersistCache(root, hints)
		lastHints = hints
		applied := 0
		for _, h := range hints {
			if h.Applied {
				applied++
			}
		}
		if !jsonOut {
			fmt.Printf("%s\n", tty.C(tty.Yellow, fmt.Sprintf("heal round %d/%d: applied %d missing stub(s); re-checking…", round+1, healMaxRounds, applied)))
		}
		if applied == 0 {
			break // nothing more heal can write
		}
	}

	if jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		_ = enc.Encode(res.Payload)
	} else if res.Passed {
		// Green: one thermometer line + claim dim line (zero babysitting).
		if tty.IsTerminal {
			tty.RenderThermometer(res.Score)
		} else {
			fmt.Printf("readiness=%d%% gates=green\n", res.Score)
		}
		fmt.Printf("%s\n", tty.C(tty.Dim, "Prepares evidence for human review — not a conformity assessment."))
	} else {
		if tty.IsTerminal {
			tty.RenderThermometer(res.Score)
		}
		// Failures: top 3 + ask pointer (no log archaeology).
		fmt.Println(topFailuresSummary(res, 3))
		fmt.Printf("%s\n", tty.C(tty.Dim, "ask: cyberready ask .github/cyberready/cache/latest_failure.json --propose"))
		fmt.Printf("%s\n", tty.C(tty.Dim, "cache: .github/cyberready/cache/latest_*.json"))
		fmt.Printf("%s\n", tty.C(tty.Dim, "Prepares evidence for human review — not a conformity assessment."))
	}

	if wantHints && (len(res.Payload.Failures) > 0 || len(lastHints) > 0) {
		hints := lastHints
		if len(hints) == 0 && len(res.Payload.Failures) > 0 {
			cache, _ := remediation.Load(root)
			hints = formhints.ForFailuresCached(res.Payload.Failures, cache)
			if applyStub && !heal {
				hints, err = formhints.ApplyStubs(root, hints)
				if err != nil {
					return err
				}
				_ = formhints.PersistCache(root, hints)
			}
		}
		fmt.Println()
		fmt.Print(formhints.Format(hints))
	}

	if !res.Passed {
		return gatesErr()
	}
	return nil
}

func topFailuresSummary(res validate.Result, n int) string {
	var b strings.Builder
	b.WriteString(res.ActionReport)
	if len(res.Payload.Failures) == 0 {
		return b.String()
	}
	b.WriteString("\n## Top findings\n\n")
	for i, f := range res.Payload.Failures {
		if i >= n {
			fmt.Fprintf(&b, "\n_…and %d more — see latest_failure.json_\n", len(res.Payload.Failures)-n)
			break
		}
		fmt.Fprintf(&b, "%d. `%s` (%s) %s\n", i+1, f.GateID, f.Severity, f.SanitizedDescription)
	}
	return b.String()
}

func cmdValidate(args []string) error {
	root, err := gitutil.RepoRoot("")
	if err != nil {
		return usageErr("must run inside a git repository")
	}
	packIDs, jsonOut, diffOnly, _, _, _ := parseValidateFlags(args)
	if !jsonOut {
		tty.PrintHeader("EXECUTING COMPLIANCE GATES")
	}
	res, err := validate.Run(validate.Options{RepoRoot: root, PackIDs: packIDs, DiffOnly: diffOnly, Quiet: jsonOut})
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
		return gatesErr()
	}
	return nil
}

func cmdPrepareRelease(args []string) error {
	tty.PrintHeader("PREPARE RELEASE REVIEW PACK")
	root, err := gitutil.RepoRoot("")
	if err != nil {
		return usageErr(err.Error())
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
		return usageErr(fmt.Sprintf("unknown packs subcommand %q (list|update|import)", args[0]))
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
		return usageErr(err.Error())
	}
	if !allowDirty && gitutil.IsDirty(root) {
		return usageErr("OCC conflict: working directory has uncommitted files")
	}
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
