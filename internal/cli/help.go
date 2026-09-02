package cli

import (
	"errors"
	"fmt"
	"os"
	"strings"
)

// errHelpShown means usage was printed; the command should exit 0 without running.
var errHelpShown = errors.New("help shown")

func isHelpFlagErr(err error) bool {
	return err != nil && strings.Contains(err.Error(), "help requested")
}

func commandUsage(cmd string) {
	switch cmd {
	case "scan":
		fmt.Fprintf(os.Stderr, "Usage: curbpack scan [--packs a,b] [--badge] [--format markdown]\n")
		fmt.Fprintf(os.Stderr, "  Read-only repo diagnosis — no init, no files written.\n")
		fmt.Fprintf(os.Stderr, "  Exit 0 when diagnosis completes (findings may remain).\n")
	case "check":
		fmt.Fprintf(os.Stderr, "Usage: curbpack check [--heal] [--score] [--packs a,b] [--json]\n")
		fmt.Fprintf(os.Stderr, "  Daily gate pass/fail on this tree — exit code authoritative.\n")
	case "share":
		fmt.Fprintf(os.Stderr, "Usage: curbpack share [--bundle] [--reveal] [--packs a,b] [--skip-prepare-release]\n")
		fmt.Fprintf(os.Stderr, "  Recipe: check → context-pack → buyer-questions → prepare-release.\n")
	case "review":
		fmt.Fprintf(os.Stderr, "Usage: curbpack review <received-pack> [--json] [--full] [--since <prior-report.json>]\n")
		fmt.Fprintf(os.Stderr, "       curbpack review --repo [path] [--packs a,b] [--json] [--edges <edges.json>] [--full] [--since <prior-report.json>]\n")
		fmt.Fprintf(os.Stderr, "       curbpack review --batch <parent-or-pack-dir>…\n")
		fmt.Fprintf(os.Stderr, "  Offline triage of a curbpack-native review-pack (no git, no network).\n")
		fmt.Fprintf(os.Stderr, "  --repo triages pack-governed docs (ProsePaths) in a repository (default path: .); same method/classifier as pack mode.\n")
		fmt.Fprintf(os.Stderr, "  --repo --packs a,b overrides .curbpack.json; cold default without config is house-policy (often few surfaces).\n")
		fmt.Fprintf(os.Stderr, "  States: confirmed | unconfirmed | contradicted — document only, not a product verdict.\n")
		fmt.Fprintf(os.Stderr, "  Default output is terse; --full dumps all findings + dropped tokens; --json emits schema v2.\n")
		fmt.Fprintf(os.Stderr, "  --edges <file> (with --repo --json only) ingests human-approved edges JSON; does not synthesize mappings.\n")
		fmt.Fprintf(os.Stderr, "  --since compares to a prior --json report (NEW / CLEARED / PERSISTING); does not change exit codes.\n")
		fmt.Fprintf(os.Stderr, "  --batch expands a non-pack parent to immediate child packs; ranks unreadable, then contradicted, then genuine-desc.\n")
		fmt.Fprintf(os.Stderr, "  --batch does not combine with --full, --json, --since, or --repo (run per-pack with those flags).\n")
		fmt.Fprintf(os.Stderr, "  Exit 1 if any finding is contradicted (or any --batch child is contradicted/unreadable); exit 2 on usage errors.\n")
	case "drift":
		fmt.Fprintf(os.Stderr, "Usage: curbpack drift [--json]\n")
		fmt.Fprintf(os.Stderr, "  Multi-signal evidence checklist — informational; exit 0 always.\n")
	case "init":
		fmt.Fprintf(os.Stderr, "Usage: curbpack init [--profile house|cra|medtech] [--packs a,b] [--workflow] [--bare] [--dry-run] [--yes]\n")
		fmt.Fprintf(os.Stderr, "  Default: house-policy + hooks + skill + ide.\n")
	case "attest":
		fmt.Fprintf(os.Stderr, "Usage: curbpack attest [--allow-dirty] [--reviewed-by=Name]\n")
		fmt.Fprintf(os.Stderr, "  Human Git Notes capsule — never auto-attest. Then proof/index.html.\n")
	default:
		fmt.Fprintf(os.Stderr, "Usage: curbpack %s\n", cmd)
	}
}

func helpShownErr(cmd string) error {
	commandUsage(cmd)
	return errHelpShown
}

func helpRequested(err error) bool {
	return errors.Is(err, errHelpShown)
}
