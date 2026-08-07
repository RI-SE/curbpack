package validate

import (
	"encoding/json"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"github.com/afelin/cyberready/internal/gitutil"
	"github.com/afelin/cyberready/internal/ir"
	"github.com/afelin/cyberready/internal/packs"
	"github.com/afelin/cyberready/internal/tty"
)

var placeholderRE = regexp.MustCompile(`(?i)(lorem ipsum|\[insert[^\]]*\]|TODO:|FIXME:|placeholder|xxxx|<\s*company\s*>)`)

// Options controls validate.
type Options struct {
	RepoRoot string
	PackIDs  []string
	Quiet    bool
}

// Result is the outcome of a validate run.
type Result struct {
	Payload ir.GateFailurePayload
	Passed  bool
	Score   int
}

// Run evaluates embedded pack rules against the repo tree.
func Run(opts Options) (Result, error) {
	root := opts.RepoRoot
	if root == "" {
		var err error
		root, err = gitutil.RepoRoot("")
		if err != nil {
			return Result{}, err
		}
	}

	ids := opts.PackIDs
	if len(ids) == 0 {
		ids = []string{"cra-baseline"}
		// Auto-include medtech if medtech docs exist or .cyberready.json says so
		if cfg := readConfig(root); cfg != nil && len(cfg.Packs) > 0 {
			ids = cfg.Packs
		} else if _, err := os.Stat(filepath.Join(root, "docs", "medtech")); err == nil {
			ids = append(ids, "medtech-iec62304")
		}
	}

	var failures []ir.Failure
	var regions []string
	for _, id := range ids {
		pack, err := packs.LoadPack(id)
		if err != nil {
			return Result{}, err
		}
		for _, rule := range pack.Rules {
			fs := evalRule(root, rule)
			if len(fs) > 0 {
				regions = append(regions, rule.ID)
				failures = append(failures, fs...)
				if !opts.Quiet {
					tty.PrintStatus("Gate "+rule.ID, false, rule.Description)
				}
			} else if !opts.Quiet {
				tty.PrintStatus("Gate "+rule.ID, true, "ok")
			}
		}
	}

	// Built-in AST reachability (MVP lift) — only if file exists
	failures = append(failures, auditASTReachability(root)...)

	score := tty.ScoreFromFailures(len(failures))
	parent, _ := gitutil.HeadSHA(root)
	payload := ir.GateFailurePayload{
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		ConcurrencyControl: ir.ConcurrencyControl{
			ExpectedParentCommitSHA: parent,
			StateVersionToken:       "v3.29-OCC",
		},
		StatechartContext: ir.StatechartContext{
			ActiveParentStatePath:   []string{"Root", "ActiveVerification", "PackEval"},
			FailedOrthogonalRegions: unique(regions),
		},
		AgentIdentity: ir.AgentIdentity{
			AgentID:         "cyberready-cli",
			ModelHash:       "deterministic",
			ActiveMandateID: strings.Join(ids, "+"),
		},
		Failures:       failures,
		PackID:         strings.Join(ids, ","),
		ReadinessScore: score,
	}

	cacheDir := filepath.Join(root, ".github", "cyberready", "cache")
	_ = os.MkdirAll(cacheDir, 0o755)
	b, _ := json.MarshalIndent(payload, "", "  ")
	_ = os.WriteFile(filepath.Join(cacheDir, "latest_failure.json"), b, 0o644)
	_ = os.WriteFile(filepath.Join(cacheDir, "latest_result.json"), b, 0o644)

	return Result{Payload: payload, Passed: len(failures) == 0, Score: score}, nil
}

type configFile struct {
	Packs []string `json:"packs"`
}

func readConfig(root string) *configFile {
	data, err := os.ReadFile(filepath.Join(root, ".cyberready.json"))
	if err != nil {
		return nil
	}
	var c configFile
	if json.Unmarshal(data, &c) != nil {
		return nil
	}
	return &c
}

func evalRule(root string, rule packs.Rule) []ir.Failure {
	switch rule.Check {
	case "annex_file":
		return checkAnnexFile(root, rule)
	case "anti_placeholder":
		return checkAntiPlaceholder(root, rule)
	case "npm_dep_ban":
		return checkNPMDepBan(root, rule)
	default:
		return []ir.Failure{{
			GateID:               rule.ID,
			Severity:             "medium",
			Type:                 "CONFIG_ERROR",
			SanitizedDescription: fmt.Sprintf("Unknown check type %q in pack rule", rule.Check),
			Remediation: ir.Remediation{
				ActionRequired: "Fix pack JSON check field.",
				ExpectedState:  "Supported check type.",
			},
		}}
	}
}

func checkAnnexFile(root string, rule packs.Rule) []ir.Failure {
	path := filepath.Join(root, rule.Path)
	info, err := os.Stat(path)
	min := rule.MinBytes
	if min <= 0 {
		min = 50
	}
	if os.IsNotExist(err) || (err == nil && info.Size() < int64(min)) {
		return []ir.Failure{failFromRule(rule, rule.Path, "")}
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return []ir.Failure{failFromRule(rule, rule.Path, err.Error())}
	}
	content := string(data)
	for _, h := range rule.RequireHeaders {
		if !strings.Contains(content, h) {
			f := failFromRule(rule, rule.Path, "missing header: "+h)
			return []ir.Failure{f}
		}
	}
	return nil
}

func checkAntiPlaceholder(root string, rule packs.Rule) []ir.Failure {
	var out []ir.Failure
	for _, rel := range rule.Paths {
		data, err := os.ReadFile(filepath.Join(root, rel))
		if err != nil {
			continue // missing handled by annex_file rules
		}
		if placeholderRE.Match(data) {
			f := failFromRule(rule, rel, "placeholder pattern matched")
			out = append(out, f)
		}
	}
	return out
}

func checkNPMDepBan(root string, rule packs.Rule) []ir.Failure {
	packagePath := filepath.Join(root, "package.json")
	data, err := os.ReadFile(packagePath)
	if err != nil {
		return nil
	}
	var manifest ir.PackageManifest
	if err := json.Unmarshal(data, &manifest); err != nil {
		return nil
	}
	checkMap := func(deps map[string]string) []ir.Failure {
		if deps == nil {
			return nil
		}
		ver, ok := deps[rule.Package]
		if !ok {
			return nil
		}
		for _, banned := range rule.BannedVersions {
			if ver == banned {
				f := failFromRule(rule, "package.json", fmt.Sprintf("%s@%s", rule.Package, ver))
				f.ASTCoordinates.NodePath = "dependencies." + rule.Package
				f.ASTCoordinates.TargetSymbol = ver
				return []ir.Failure{f}
			}
		}
		return nil
	}
	if f := checkMap(manifest.Dependencies); len(f) > 0 {
		return f
	}
	return checkMap(manifest.DevDependencies)
}

func failFromRule(rule packs.Rule, file, detail string) ir.Failure {
	desc := rule.Description
	if detail != "" {
		desc = desc + " (" + detail + ")"
	}
	return ir.Failure{
		GateID:               rule.ID,
		Severity:             rule.Severity,
		Type:                 rule.Type,
		SanitizedDescription: desc,
		ASTCoordinates:       ir.ASTCoordinates{TargetFile: filepath.Base(file)},
		Remediation: ir.Remediation{
			ActionRequired: rule.Remediation,
			ExpectedState:  rule.Expected,
		},
	}
}

func auditASTReachability(gitRoot string) []ir.Failure {
	targetFile := filepath.Join(gitRoot, "src", "payment.go")
	if _, err := os.Stat(targetFile); os.IsNotExist(err) {
		return nil
	}
	fset := token.NewFileSet()
	node, err := parser.ParseFile(fset, targetFile, nil, parser.ParseComments)
	if err != nil {
		return nil
	}
	found := false
	var nodePos token.Position
	ast.Inspect(node, func(n ast.Node) bool {
		call, ok := n.(*ast.CallExpr)
		if !ok {
			return true
		}
		sel, ok := call.Fun.(*ast.SelectorExpr)
		if !ok {
			return true
		}
		ident, ok := sel.X.(*ast.Ident)
		if !ok {
			return true
		}
		if ident.Name == "axios" && sel.Sel.Name == "Post" {
			found = true
			nodePos = fset.Position(n.Pos())
			return false
		}
		return true
	})
	if !found {
		return nil
	}
	return []ir.Failure{{
		GateID:               "CR-AST-01",
		Severity:             "high",
		Type:                 "POLICY_VIOLATION",
		SanitizedDescription: "Unsafe direct execution of vulnerable module detected via AST Inspector.",
		ASTCoordinates: ir.ASTCoordinates{
			TargetFile:    "src/payment.go",
			NodePath:      "CallExpr.SelectorExpr[axios.Post]",
			TargetSymbol:  "axios.Post",
			FallbackLines: fmt.Sprintf("Line %d", nodePos.Line),
		},
		Remediation: ir.Remediation{
			ActionRequired: "Route calls through validated wrapper function in 'safe_http.go'.",
			ExpectedState:  "No direct unmitigated function calls found in AST.",
		},
	}}
}

func unique(in []string) []string {
	seen := map[string]struct{}{}
	var out []string
	for _, s := range in {
		if _, ok := seen[s]; ok {
			continue
		}
		seen[s] = struct{}{}
		out = append(out, s)
	}
	return out
}

// SemanticMarkdown renders dual-rep agent-facing markdown from a payload.
func SemanticMarkdown(payload ir.GateFailurePayload) string {
	var b strings.Builder
	parent := payload.ConcurrencyControl.ExpectedParentCommitSHA
	if len(parent) > 8 {
		parent = parent[:8]
	}
	fmt.Fprintf(&b, "# COMPLIANCE ALERT: GATE FAILURE [OCC-ID: %s:%s]\n",
		parent, payload.ConcurrencyControl.StateVersionToken)
	fmt.Fprintf(&b, "**Statechart Path:** %s\n", strings.Join(payload.StatechartContext.ActiveParentStatePath, " / "))
	fmt.Fprintf(&b, "**Failed Region:** %s\n\n", strings.Join(payload.StatechartContext.FailedOrthogonalRegions, ", "))
	for i, f := range payload.Failures {
		fmt.Fprintf(&b, "## VIOLATION %d: %s [%s] (%s)\n", i+1, f.Type, f.GateID, f.Severity)
		fmt.Fprintf(&b, "* **Location:** `%s`\n", f.ASTCoordinates.TargetFile)
		fmt.Fprintf(&b, "* **AST Path:** `%s`\n", f.ASTCoordinates.NodePath)
		fmt.Fprintf(&b, "* **Symbol Target:** `%s`\n", f.ASTCoordinates.TargetSymbol)
		b.WriteString("* **Context:**\n")
		b.WriteString("<untrusted_metadata>\n")
		b.WriteString(f.SanitizedDescription + "\n")
		b.WriteString("</untrusted_metadata>\n\n")
		b.WriteString("### REQUIRED REMEDIATION\n")
		fmt.Fprintf(&b, "* **Goal State:** %s\n", f.Remediation.ExpectedState)
		fmt.Fprintf(&b, "* **Resolution Path:** %s\n\n", f.Remediation.ActionRequired)
	}
	return b.String()
}
