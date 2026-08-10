package cli

import (
	"errors"
	"fmt"
	"os"
	"strings"

	"github.com/afelin/cyberready/internal/gitutil"
	"github.com/afelin/cyberready/internal/pathway"
	"github.com/afelin/cyberready/internal/tty"
)

func pathwayErr(err error) error {
	if err == nil {
		return nil
	}
	if errors.Is(err, pathway.ErrUsage) {
		return usageErr(err.Error())
	}
	return err
}

func cmdPathway(args []string) error {
	if len(args) == 0 {
		return usageErr("pathway requires subcommand: status|suggest|confirm-packs|confirm-prose|confirm-share|note")
	}
	root, err := gitutil.RepoRoot("")
	if err != nil {
		return usageErr("must run inside a git repository")
	}
	switch args[0] {
	case "status":
		return cmdPathwayStatus(root, args[1:])
	case "suggest":
		return cmdPathwaySuggest(root, args[1:])
	case "confirm-packs":
		return cmdPathwayConfirmPacks(root)
	case "confirm-prose":
		return cmdPathwayConfirmProse(root)
	case "confirm-share":
		return cmdPathwayConfirmShare(root)
	case "note":
		return cmdPathwayNote(root, args[1:])
	case "help", "-h", "--help":
		pathwayUsage()
		return nil
	default:
		return usageErr(fmt.Sprintf("unknown pathway subcommand %q (status|suggest|confirm-packs|confirm-prose|confirm-share|note)", args[0]))
	}
}

func pathwayUsage() {
	fmt.Fprintf(os.Stderr, "cyberready pathway — warm-start pack seed + HITL ticks\n\n")
	fmt.Fprintf(os.Stderr, "  status [--human|--technical]   One next ask (human default) or phase+next\n")
	fmt.Fprintf(os.Stderr, "  suggest --product=… --eu-docs=… --medtech=… --sector=… --house-first=… [--ce-context=…]\n")
	fmt.Fprintf(os.Stderr, "                                  Closed-world proposed_packs (enums only)\n")
	fmt.Fprintf(os.Stderr, "  confirm-packs                   Human: stamp packs_confirmed (+ RKG; next may be research)\n")
	fmt.Fprintf(os.Stderr, "  confirm-prose                   Human: stamp prose_owned (cite-check if packet present)\n")
	fmt.Fprintf(os.Stderr, "  confirm-share                   Human: stamp share_reviewed\n")
	fmt.Fprintf(os.Stderr, "  note --set|--forget …          Session notes / corrections / last_draft_pick (not a gate input)\n\n")
	fmt.Fprintf(os.Stderr, "Sole writer of .github/cyberready/cache/pathway-seed.json.\n")
	fmt.Fprintf(os.Stderr, "Does not affect check pass/fail. Agents stop at confirms/attest.\n")
	fmt.Fprintf(os.Stderr, "%s\n", pathway.ClaimFence)
}

func cmdPathwayNote(root string, args []string) error {
	if len(args) == 0 {
		return usageErr("pathway note requires --set <text|key=value> or --forget <key|text>")
	}
	var setVal, forgetVal string
	for i := 0; i < len(args); i++ {
		arg := args[i]
		switch {
		case arg == "--set" || arg == "-s":
			if i+1 >= len(args) {
				return usageErr("pathway note --set needs a value")
			}
			setVal = args[i+1]
			i++
		case strings.HasPrefix(arg, "--set="):
			setVal = strings.TrimPrefix(arg, "--set=")
		case arg == "--forget" || arg == "-f":
			if i+1 >= len(args) {
				return usageErr("pathway note --forget needs a value")
			}
			forgetVal = args[i+1]
			i++
		case strings.HasPrefix(arg, "--forget="):
			forgetVal = strings.TrimPrefix(arg, "--forget=")
		case arg == "-h" || arg == "--help":
			pathwayUsage()
			return nil
		default:
			return usageErr(fmt.Sprintf("pathway note: unknown flag %q (use --set or --forget)", arg))
		}
	}
	if setVal != "" && forgetVal != "" {
		return usageErr("pathway note: use either --set or --forget, not both")
	}
	if setVal == "" && forgetVal == "" {
		return usageErr("pathway note requires --set <text|key=value> or --forget <key|text>")
	}
	var (
		seed *pathway.Seed
		err  error
	)
	if setVal != "" {
		seed, err = pathway.NoteSet(root, setVal)
	} else {
		seed, err = pathway.NoteForget(root, forgetVal)
	}
	if err != nil {
		return pathwayErr(err)
	}
	tty.PrintHeader("cyberready pathway note")
	if setVal != "" {
		fmt.Printf("set: %s\n", setVal)
	} else {
		fmt.Printf("forgot: %s\n", forgetVal)
	}
	if seed.LastDraftPick != "" {
		fmt.Printf("last_draft_pick: %s\n", seed.LastDraftPick)
	}
	if len(seed.Corrections) > 0 {
		fmt.Printf("corrections: %d\n", len(seed.Corrections))
	}
	if len(seed.SessionNotes) > 0 {
		fmt.Printf("session_notes: %d\n", len(seed.SessionNotes))
	}
	fmt.Printf("%s\n", tty.C(tty.Dim, "session memory only — does not affect check pass/fail"))
	fmt.Printf("%s\n", tty.C(tty.Dim, pathway.ClaimFence))
	return nil
}

func cmdPathwayStatus(root string, args []string) error {
	human := true // default: plain next ask for humans / site recipes
	for _, a := range args {
		switch a {
		case "--human":
			human = true
		case "--technical", "--tech", "--agent":
			human = false
		case "-h", "--help":
			pathwayUsage()
			return nil
		default:
			return usageErr(fmt.Sprintf("pathway status: unknown flag %q (use --human or --technical)", a))
		}
	}
	snap, err := pathway.Project(root)
	if err != nil {
		return pathwayErr(err)
	}
	if human {
		fmt.Print(pathway.FormatHumanStatus(snap))
	} else {
		fmt.Print(pathway.FormatSnapshot(snap))
	}
	return nil
}

func cmdPathwaySuggest(root string, args []string) error {
	ans, err := parsePathwaySuggestFlags(args)
	if err != nil {
		return usageErr(err.Error())
	}
	res, err := pathway.Suggest(ans)
	if err != nil {
		return usageErr(err.Error())
	}
	seed, err := pathway.ApplySuggest(root, res)
	if err != nil {
		return pathwayErr(err)
	}
	tty.PrintHeader("cyberready pathway suggest")
	fmt.Printf("proposed_packs: %s\n", strings.Join(seed.ProposedPacks, ", "))
	if seed.NextHint != "" {
		fmt.Printf("next_hint: %s (see docs/write-your-own-pack.md)\n", seed.NextHint)
	}
	fmt.Printf("seed: %s\n", pathway.SeedPath(root))
	fmt.Printf("%s\n", tty.C(tty.Dim, pathway.ClaimFence))
	fmt.Printf("%s\n", tty.C(tty.Dim, "next: human cyberready pathway confirm-packs"))
	return nil
}

func cmdPathwayConfirmPacks(root string) error {
	seed, err := pathway.ConfirmPacks(root)
	if err != nil {
		return pathwayErr(err)
	}
	tty.PrintHeader("cyberready pathway confirm-packs")
	fmt.Printf("packs_confirmed: %s\n", strings.Join(seed.ProposedPacks, ", "))
	fmt.Printf("%s\n", tty.C(tty.Dim, pathway.ClaimFence))
	snap, _ := pathway.Project(root)
	fmt.Print(pathway.FormatSnapshot(snap))
	return nil
}

func cmdPathwayConfirmProse(root string) error {
	_, err := pathway.ConfirmProse(root)
	if err != nil {
		return pathwayErr(err)
	}
	tty.PrintHeader("cyberready pathway confirm-prose")
	fmt.Printf("%s\n", tty.C(tty.Dim, "prose_owned stamped — re-check before share"))
	fmt.Printf("%s\n", tty.C(tty.Dim, pathway.ClaimFence))
	snap, _ := pathway.Project(root)
	fmt.Print(pathway.FormatSnapshot(snap))
	return nil
}

func cmdPathwayConfirmShare(root string) error {
	_, err := pathway.ConfirmShare(root)
	if err != nil {
		return pathwayErr(err)
	}
	tty.PrintHeader("cyberready pathway confirm-share")
	fmt.Printf("%s\n", tty.C(tty.Dim, "share_reviewed stamped — human attest next; agents stop"))
	fmt.Printf("%s\n", tty.C(tty.Dim, pathway.ClaimFence))
	snap, _ := pathway.Project(root)
	fmt.Print(pathway.FormatSnapshot(snap))
	return nil
}

func parsePathwaySuggestFlags(args []string) (pathway.Answers, error) {
	var a pathway.Answers
	a.CeContext = "none"
	set := map[string]bool{}
	for i := 0; i < len(args); i++ {
		arg := args[i]
		key, val, ok := splitFlag(arg)
		if !ok {
			if i+1 >= len(args) {
				return a, fmt.Errorf("pathway suggest: flag %s needs a value", arg)
			}
			key = strings.TrimPrefix(arg, "--")
			val = args[i+1]
			i++
		}
		switch key {
		case "product":
			a.Product = val
			set["product"] = true
		case "eu-docs":
			a.EuDocs = val
			set["eu-docs"] = true
		case "medtech":
			a.Medtech = val
			set["medtech"] = true
		case "sector":
			a.Sector = val
			set["sector"] = true
		case "house-first":
			a.HouseFirst = val
			set["house-first"] = true
		case "ce-context":
			a.CeContext = val
			set["ce-context"] = true
		default:
			return a, fmt.Errorf("pathway suggest: unknown flag --%s", key)
		}
	}
	for _, req := range []string{"product", "eu-docs", "medtech", "sector", "house-first"} {
		if !set[req] {
			return a, fmt.Errorf("pathway suggest: missing --%s (enums only; see docs/getting-started/pathway.md)", req)
		}
	}
	return a, nil
}

func splitFlag(arg string) (key, val string, ok bool) {
	if !strings.HasPrefix(arg, "--") {
		return "", "", false
	}
	body := strings.TrimPrefix(arg, "--")
	if i := strings.IndexByte(body, '='); i >= 0 {
		return body[:i], body[i+1:], true
	}
	return "", "", false
}
