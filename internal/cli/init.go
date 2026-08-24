package cli

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/afelin/curbpack/internal/paths"
	"github.com/afelin/curbpack/internal/tty"
	"github.com/afelin/curbpack/internal/workflowdata"
)

type initWriteItem struct {
	Rel  string
	Note string
}

func initProfileWhy(f initFlags) string {
	if f.explicitPacks {
		return "from --packs"
	}
	if f.explicitProfile {
		if len(f.packList) == 1 && f.packList[0] == "cra-baseline" {
			return "--profile cra to match scan"
		}
		if f.profileName != "" {
			return "--profile " + f.profileName
		}
		return "from --profile"
	}
	return "house-policy default; --profile cra to match scan"
}

func secretPathDecoyNote(rel string) string {
	switch filepath.Base(filepath.ToSlash(rel)) {
	case ".env", ".env.local", "credentials.json", "service-account.json", "id_rsa":
		return "secret-path decoy"
	default:
		return ""
	}
}

func initWritePlan(f initFlags, scaffold []string) []initWriteItem {
	var items []initWriteItem
	add := func(rel, note string) {
		items = append(items, initWriteItem{Rel: filepath.ToSlash(rel), Note: note})
	}
	add(".gitignore", "")
	add(paths.GitHubDir+"/policies/", "")
	add(paths.CacheRel+"/", "")
	add(paths.EvidenceRel+"/", "")
	add(paths.ConfigFile, "")
	for _, rel := range scaffold {
		add(rel, secretPathDecoyNote(rel))
	}
	add("proof/index.html", "")
	if f.hooks {
		add(".git/hooks/pre-commit", "hook")
	}
	if f.skill {
		add(filepath.ToSlash(filepath.Join(paths.SkillRel, "SKILL.md")), "skill")
	}
	if f.ide {
		add(".vscode/tasks.json", "")
	}
	if f.writeWorkflow {
		add(workflowdata.DestRel, "workflow")
	}
	return items
}

func printInitWriteList(items []initWriteItem) {
	fmt.Println("Will write:")
	for _, it := range items {
		if it.Note != "" {
			fmt.Printf("  %s  (%s)\n", it.Rel, it.Note)
			continue
		}
		fmt.Printf("  %s\n", it.Rel)
	}
}

func initNeedsTTYConfirm() bool {
	if !tty.IsTerminal {
		return false
	}
	st, err := os.Stdin.Stat()
	if err != nil {
		return false
	}
	return st.Mode()&os.ModeCharDevice != 0
}

// confirmInitIfNeeded prompts once on an interactive TTY unless --yes.
// Non-TTY skips confirm so tests and agents stay non-interactive.
func confirmInitIfNeeded(yes bool) (write bool, err error) {
	if yes || !initNeedsTTYConfirm() {
		return true, nil
	}
	fmt.Print("Write these files? [y/N]: ")
	reader := bufio.NewReader(os.Stdin)
	line, _ := reader.ReadString('\n')
	line = strings.TrimSpace(strings.ToLower(line))
	if line != "y" && line != "yes" {
		fmt.Println("Aborted — no files written.")
		return false, nil
	}
	return true, nil
}
