package formhints

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/afelin/cyberready/internal/debugagent"
	"github.com/afelin/cyberready/internal/ir"
	"github.com/afelin/cyberready/internal/packs"
	"github.com/afelin/cyberready/internal/remediation"
)

// Hint is a deterministic gate→snippet proposal (Witness-style templates).
type Hint struct {
	GateID   string
	File     string
	Snippet  string
	Action   string
	Applied  bool
	Proposed bool
	FromCache bool
}

// ForFailures maps each failure to a file + exact scaffold snippet.
// Optional cache supplies last-good snippets by gate_id (never invents legal prose).
func ForFailures(failures []ir.Failure) []Hint {
	return ForFailuresCached(failures, remediation.Cache{})
}

// ForFailuresCached prefers remediations.json entries when present.
func ForFailuresCached(failures []ir.Failure, cache remediation.Cache) []Hint {
	var out []Hint
	for _, f := range failures {
		h := Hint{
			GateID: f.GateID,
			File:   resolveFile(f),
			Action: f.Remediation.ActionRequired,
		}
		if e, ok := remediation.Lookup(cache, f.GateID); ok {
			if e.File != "" {
				h.File = e.File
			}
			if e.Snippet != "" {
				h.Snippet = e.Snippet
				h.FromCache = true
			}
			if e.Action != "" && h.Action == "" {
				h.Action = e.Action
			}
		}
		if h.Snippet == "" {
			if snip, ok := snippetForGate(f.GateID, h.File); ok {
				h.Snippet = snip
			} else if h.File != "" {
				h.Snippet = packs.DefaultScaffoldBody(h.File)
			}
		}
		out = append(out, h)
	}
	return out
}

func resolveFile(f ir.Failure) string {
	file := strings.TrimSpace(f.ASTCoordinates.TargetFile)
	guessed := guessFile(f.GateID)
	if file == "" {
		return guessed
	}
	// Prefer guessed path when IR only has a basename (common for nested stubs).
	if guessed != "" && !strings.Contains(file, "/") && !strings.Contains(file, string(filepath.Separator)) {
		base := filepath.Base(guessed)
		if base == file || strings.HasSuffix(guessed, file) {
			return guessed
		}
	}
	return filepath.ToSlash(file)
}

// Format prints human-readable propose-only hints.
func Format(hints []Hint) string {
	var b strings.Builder
	b.WriteString("## Form hints (deterministic — propose-only by default)\n\n")
	b.WriteString("CyberReady will not invent legal prose. Snippets are structural Witness templates.\n")
	b.WriteString("Heal never auto-attests and never marks VEX final.\n\n")
	for _, h := range hints {
		b.WriteString(fmt.Sprintf("### %s\n", h.GateID))
		if h.File != "" {
			b.WriteString(fmt.Sprintf("- Target: `%s`\n", h.File))
		}
		if h.Action != "" {
			b.WriteString(fmt.Sprintf("- Action: %s\n", h.Action))
		}
		if h.FromCache {
			b.WriteString("- Source: remediation cache\n")
		}
		if h.Snippet != "" {
			b.WriteString("\n```\n")
			b.WriteString(strings.TrimRight(h.Snippet, "\n"))
			b.WriteString("\n```\n\n")
		}
		if h.Applied {
			b.WriteString("_Written with --apply-stub / --heal (overwrite only if missing or empty)._\n\n")
		} else {
			b.WriteString("_Propose-only — pass `--apply-stub` or `--heal` to write missing stubs._\n\n")
		}
	}
	return b.String()
}

// ApplyStubs writes missing/empty target files with snippets. Never overwrites non-empty files.
// Refuses absolute paths and path traversal. Never calls attest.
func ApplyStubs(repoRoot string, hints []Hint) ([]Hint, error) {
	out := make([]Hint, 0, len(hints))
	for _, h := range hints {
		h.Proposed = true
		if h.File == "" || h.Snippet == "" {
			out = append(out, h)
			continue
		}
		rel, err := safeRelPath(h.File)
		if err != nil {
			return out, err
		}
		h.File = rel
		path := filepath.Join(repoRoot, filepath.FromSlash(rel))
		// #region agent log
		underGit := strings.HasPrefix(rel, ".git/") || rel == ".git"
		debugagent.Log("H5", "formhints.go:ApplyStubs", "stub write candidate", map[string]any{
			"rel": rel, "underGit": underGit, "gate": h.GateID,
		})
		// #endregion
		if st, err := os.Stat(path); err == nil && st.Size() > 0 {
			out = append(out, h)
			continue
		}
		if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
			return out, err
		}
		if err := os.WriteFile(path, []byte(h.Snippet), 0o644); err != nil {
			return out, err
		}
		h.Applied = true
		// #region agent log
		if underGit {
			debugagent.Log("H5", "formhints.go:ApplyStubs", "WROTE under .git", map[string]any{"rel": rel})
		}
		// #endregion
		out = append(out, h)
	}
	return out, nil
}

// PersistCache upserts applied/proposed hints into remediations.json.
func PersistCache(repoRoot string, hints []Hint) error {
	c, err := remediation.Load(repoRoot)
	if err != nil {
		return err
	}
	var entries []remediation.Entry
	for _, h := range hints {
		if h.GateID == "" || h.Snippet == "" {
			continue
		}
		entries = append(entries, remediation.Entry{
			GateID:  h.GateID,
			File:    h.File,
			Snippet: h.Snippet,
			Action:  h.Action,
		})
	}
	remediation.Upsert(&c, entries...)
	return remediation.Save(repoRoot, c)
}

func safeRelPath(p string) (string, error) {
	p = strings.TrimSpace(p)
	p = filepath.ToSlash(p)
	if p == "" {
		return "", fmt.Errorf("empty remediation path")
	}
	if filepath.IsAbs(p) || strings.HasPrefix(p, "/") {
		return "", fmt.Errorf("refusing absolute remediation path: %s", p)
	}
	clean := filepath.ToSlash(filepath.Clean(p))
	if clean == ".." || strings.HasPrefix(clean, "../") {
		return "", fmt.Errorf("refusing path traversal in remediation: %s", p)
	}
	// Mirror validate.SafeJoin: refuse escape after Abs when joined under a fake root.
	root := string(os.PathSeparator) + "repo"
	full := filepath.Join(root, filepath.FromSlash(clean))
	rootAbs, err := filepath.Abs(root)
	if err != nil {
		return "", err
	}
	fullAbs, err := filepath.Abs(full)
	if err != nil {
		return "", err
	}
	sep := string(os.PathSeparator)
	if fullAbs != rootAbs && !strings.HasPrefix(fullAbs, rootAbs+sep) {
		return "", fmt.Errorf("refusing path escape in remediation: %s", p)
	}
	// #region agent log
	if clean == ".git" || strings.HasPrefix(clean, ".git/") {
		debugagent.Log("H5", "formhints.go:safeRelPath", "ALLOWED path under .git", map[string]any{"clean": clean})
	}
	// #endregion
	return clean, nil
}

func guessFile(gateID string) string {
	switch {
	case strings.Contains(gateID, "RISK"):
		return "docs/annex-vii/risk_assessment.md"
	case strings.Contains(gateID, "SUPPORT"):
		return "docs/annex-vii/support_period.md"
	case strings.Contains(gateID, "MANUAL"):
		return "docs/annex-vii/user_manual_security.md"
	case strings.Contains(gateID, "SECURITY-MD") || strings.Contains(gateID, "SECURITY_MD"):
		return "SECURITY.md"
	case strings.Contains(gateID, "SECURITY-TXT") || strings.Contains(gateID, "SECURITY_TXT"):
		return ".well-known/security.txt"
	case strings.Contains(gateID, "SAFETY"):
		return "docs/iec62304/software_safety_class.md"
	case strings.Contains(gateID, "SOUP"):
		return "docs/iec62304/soup_list.md"
	case strings.Contains(gateID, "PROBLEM"):
		return "docs/iec62304/problem_resolution.md"
	default:
		return ""
	}
}

func snippetForGate(gateID, file string) (string, bool) {
	if strings.Contains(gateID, "DEP") || strings.Contains(gateID, "AXIOS") {
		return "# Dependency remediations are not auto-written.\n# Upgrade the banned package and refresh the lockfile, then re-run check.\n", true
	}
	if strings.Contains(gateID, "SECRET") {
		return "", false
	}
	if file == "" {
		return "", false
	}
	return packs.DefaultScaffoldBody(file), true
}
