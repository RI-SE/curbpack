package cli

import (
	"fmt"
	"strings"
)

// top-level commands and common flags for static shell completions (freeze-safe).
var completionCommands = []string{
	"help", "version", "doctor", "demo", "init", "check", "validate",
	"prepare-release", "packs", "ask", "attest", "view", "sock",
	"export", "share", "completion",
}

var completionExportFlags = []string{
	"--sarif", "--explain-packet", "--watchlist-join", "--buyer-questions",
	"--lay-of-land", "--context-pack", "--spdx", "--slsa", "--out", "--packs",
}

var completionShells = []string{"bash", "zsh", "fish"}

func cmdCompletion(args []string) error {
	if len(args) == 0 {
		return usageErr("completion requires shell: bash|zsh|fish")
	}
	shell := strings.ToLower(strings.TrimSpace(args[0]))
	switch shell {
	case "bash":
		fmt.Print(bashCompletionScript())
	case "zsh":
		fmt.Print(zshCompletionScript())
	case "fish":
		fmt.Print(fishCompletionScript())
	default:
		return usageErr("completion shell must be bash, zsh, or fish")
	}
	return nil
}

func bashCompletionScript() string {
	cmds := strings.Join(completionCommands, " ")
	exports := strings.Join(completionExportFlags, " ")
	return `# cyberready bash completion — eval "$(cyberready completion bash)"
_cyberready() {
  local cur prev
  COMPREPLY=()
  cur="${COMP_WORDS[COMP_CWORD]}"
  prev="${COMP_WORDS[COMP_CWORD-1]}"
  if [[ ${COMP_CWORD} -eq 1 ]]; then
    COMPREPLY=( $(compgen -W "` + cmds + `" -- "$cur") )
    return 0
  fi
  case "${COMP_WORDS[1]}" in
    export)
      COMPREPLY=( $(compgen -W "` + exports + `" -- "$cur") )
      ;;
    completion)
      COMPREPLY=( $(compgen -W "` + strings.Join(completionShells, " ") + `" -- "$cur") )
      ;;
    packs)
      COMPREPLY=( $(compgen -W "list update import export-graph doctor" -- "$cur") )
      ;;
    check)
      COMPREPLY=( $(compgen -W "--heal --diff --json --form-hints --apply-stub --packs" -- "$cur") )
      ;;
    demo)
      COMPREPLY=( $(compgen -W "--open --keep --out" -- "$cur") )
      ;;
    init)
      COMPREPLY=( $(compgen -W "--bare --packs --workflow" -- "$cur") )
      ;;
    ask)
      COMPREPLY=( $(compgen -W "--propose" -- "$cur") )
      ;;
    share)
      COMPREPLY=( $(compgen -W "--packs --skip-prepare-release" -- "$cur") )
      ;;
  esac
}
complete -F _cyberready cyberready
`
}

func zshCompletionScript() string {
	var b strings.Builder
	b.WriteString("#compdef cyberready\n")
	b.WriteString("# cyberready zsh completion — eval \"$(cyberready completion zsh)\"\n")
	b.WriteString("_cyberready() {\n")
	b.WriteString("  local -a cmds\n")
	b.WriteString("  cmds=(")
	for _, c := range completionCommands {
		fmt.Fprintf(&b, " %q", c)
	}
	b.WriteString(" )\n")
	b.WriteString("  if (( CURRENT == 2 )); then\n")
	b.WriteString("    _describe 'command' cmds\n")
	b.WriteString("    return\n")
	b.WriteString("  fi\n")
	b.WriteString("  case $words[2] in\n")
	b.WriteString("    export) _values 'export flag'")
	for _, f := range completionExportFlags {
		fmt.Fprintf(&b, " %q", f)
	}
	b.WriteString(" ;;\n")
	b.WriteString("    completion) _values 'shell' 'bash' 'zsh' 'fish' ;;\n")
	b.WriteString("    packs) _values 'packs' 'list' 'update' 'import' 'export-graph' 'doctor' ;;\n")
	b.WriteString("  esac\n")
	b.WriteString("}\n")
	b.WriteString("compdef _cyberready cyberready\n")
	return b.String()
}

func fishCompletionScript() string {
	var b strings.Builder
	b.WriteString("# cyberready fish completion — cyberready completion fish | source\n")
	b.WriteString("complete -c cyberready -f\n")
	for _, c := range completionCommands {
		fmt.Fprintf(&b, "complete -c cyberready -n '__fish_use_subcommand' -a %q\n", c)
	}
	for _, f := range completionExportFlags {
		fmt.Fprintf(&b, "complete -c cyberready -n '__fish_seen_subcommand_from export' -a %q\n", f)
	}
	for _, s := range completionShells {
		fmt.Fprintf(&b, "complete -c cyberready -n '__fish_seen_subcommand_from completion' -a %q\n", s)
	}
	return b.String()
}
