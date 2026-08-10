package cli

import (
	"fmt"
	"os"
	"strings"

	"github.com/afelin/cyberready/internal/config"
	"github.com/afelin/cyberready/internal/gitutil"
	"github.com/afelin/cyberready/internal/research"
	"github.com/afelin/cyberready/internal/tty"
)

func cmdResearch(args []string) error {
	fetch := false
	listSources := false
	openSources := false
	citePath := ""
	packsFlag := ""
	gateIDs := ""
	for i := 0; i < len(args); i++ {
		a := args[i]
		switch {
		case a == "--fetch":
			fetch = true
		case a == "--list-sources":
			listSources = true
		case a == "--open-sources":
			openSources = true
		case a == "--cite-check":
			if i+1 >= len(args) {
				return usageErr("research --cite-check requires a draft path")
			}
			citePath = args[i+1]
			i++
		case strings.HasPrefix(a, "--cite-check="):
			citePath = strings.TrimPrefix(a, "--cite-check=")
		case a == "--packs":
			if i+1 >= len(args) {
				return usageErr("research --packs requires a value")
			}
			packsFlag = args[i+1]
			i++
		case strings.HasPrefix(a, "--packs="):
			packsFlag = strings.TrimPrefix(a, "--packs=")
		case a == "--gate-id" || a == "--gate-ids":
			if i+1 >= len(args) {
				return usageErr("research --gate-id requires a value")
			}
			gateIDs = args[i+1]
			i++
		case strings.HasPrefix(a, "--gate-id="):
			gateIDs = strings.TrimPrefix(a, "--gate-id=")
		case strings.HasPrefix(a, "--gate-ids="):
			gateIDs = strings.TrimPrefix(a, "--gate-ids=")
		case a == "help", a == "-h", a == "--help":
			researchUsage()
			return nil
		default:
			return usageErr(fmt.Sprintf("research: unknown flag %q", a))
		}
	}

	root, err := gitutil.RepoRoot("")
	if err != nil {
		return usageErr("must run inside a git repository")
	}

	if citePath != "" {
		return cmdResearchCiteCheck(root, citePath)
	}
	if listSources || openSources {
		return cmdResearchSources(root, openSources)
	}

	var packIDs []string
	if packsFlag != "" {
		packIDs = config.ParsePacksFlag(packsFlag)
	}
	var gates []string
	if gateIDs != "" {
		gates = config.ParsePacksFlag(gateIDs) // comma-split helper
	}

	pkt, err := research.Build(research.Options{
		RepoRoot: root,
		PackIDs:  packIDs,
		GateIDs:  gates,
		Fetch:    fetch,
	})
	if err != nil {
		return err
	}
	jsonPath, mdPath, err := research.Write(root, pkt)
	if err != nil {
		return err
	}
	tty.PrintHeader("cyberready research")
	fmt.Printf("packs: %s\n", strings.Join(pkt.PackIDs, ", "))
	fmt.Printf("sources: %d\n", len(pkt.Sources))
	fmt.Printf("requirements: %d\n", len(pkt.Requirements))
	if fetch {
		fmt.Printf("fetch: on (fail-open per URL; allowlisted HTTPS only)\n")
	} else {
		fmt.Printf("fetch: off (air-gap default)\n")
	}
	fmt.Printf("packet: %s\n", jsonPath)
	fmt.Printf("brief:  %s\n", mdPath)
	fmt.Printf("%s\n", tty.C(tty.Dim, research.PacketNote))
	fmt.Printf("%s\n", tty.C(tty.Dim, research.ClaimFence))
	return nil
}

func cmdResearchCiteCheck(root, draft string) error {
	pkt, err := research.LoadPacket(root)
	if err != nil {
		return err
	}
	if pkt == nil {
		return usageErr("research --cite-check: missing research-packet.json — run cyberready research first")
	}
	res, err := research.CiteCheckFile(*pkt, root, draft)
	if err != nil {
		return err
	}
	tty.PrintHeader("cyberready research --cite-check")
	fmt.Printf("draft: %s\n", draft)
	if res.OK {
		fmt.Printf("%s\n", tty.C(tty.Green, "cite-check: ok"))
		fmt.Printf("%s\n", tty.C(tty.Dim, "Still not conformity assessment — human confirm-prose / attest only."))
		return nil
	}
	fmt.Printf("%s\n", tty.C(tty.Red, "cite-check: refuse"))
	for _, e := range res.Errors {
		fmt.Printf("  - %s\n", e)
	}
	return gatesErr()
}

func cmdResearchSources(root string, open bool) error {
	pkt, err := research.LoadPacket(root)
	if err != nil {
		return err
	}
	if pkt == nil {
		return usageErr("no research-packet.json — run cyberready research first")
	}
	fmt.Print(research.FormatSourcesList(*pkt))
	if open {
		for _, s := range pkt.Sources {
			if err := research.ValidateSourceURL(s.URL); err != nil {
				fmt.Fprintf(os.Stderr, "skip %s: %v\n", s.ID, err)
				continue
			}
			_ = openAllowlistedURL(s.URL) // best-effort
		}
	}
	return nil
}

func researchUsage() {
	fmt.Fprintf(os.Stderr, "cyberready research — allowlisted citation packet + human brief\n\n")
	fmt.Fprintf(os.Stderr, "  research [--packs a,b] [--gate-id ID] [--fetch]\n")
	fmt.Fprintf(os.Stderr, "                                  Build research-packet.json + research-brief.md\n")
	fmt.Fprintf(os.Stderr, "  research --cite-check <draft.md> Cite-or-refuse groundedness (RAGChecker-lite)\n")
	fmt.Fprintf(os.Stderr, "  research --list-sources          Print allowlisted source ids + URLs\n")
	fmt.Fprintf(os.Stderr, "  research --open-sources          List and best-effort open allowlisted URLs\n\n")
	fmt.Fprintf(os.Stderr, "Never affects cyberready check pass/fail. Hosts: eur-lex.europa.eu, iso.org, …\n")
	fmt.Fprintf(os.Stderr, "%s\n", research.ClaimFence)
}
