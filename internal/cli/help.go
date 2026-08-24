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
