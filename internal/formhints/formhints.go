package formhints

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/packs"
	"github.com/afelin/curbpack/internal/pathjail"
	"github.com/afelin/curbpack/internal/remediation"
)

// Hint is a deterministic gate→snippet proposal (Witness-style templates).
type Hint struct {
	GateID    string
	File      string
	Snippet   string
	Action    string
	Applied   bool
	Proposed  bool
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
			if snip, ok := snippetForFailure(f, h.File); ok {
				h.Snippet = snip
			} else if h.File != "" {
				h.Snippet = packs.DefaultScaffoldBody(h.File)
			}
		}
		// Target-absent dep-ban: ensure heal can scaffold a valid empty manifest
		// even if remediations.json still holds the propose-only comment stub.
		if isPackageJSON(h.File) && isTargetAbsent(f) && !json.Valid([]byte(strings.TrimSpace(h.Snippet))) {
			h.Snippet = emptyPackageJSONStub()
			h.FromCache = false
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
	b.WriteString("Curbpack will not invent legal prose. Snippets are structural Witness templates.\n")
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
// Missing paths use O_CREATE|O_EXCL (atomic create). Empty non-symlink files are healed via
// Lstat-proven write/trunc. Refuses absolute paths, path traversal, .git/**, and symlink targets.
// Never writes non-JSON snippets into package.json (dep remediations stay propose-only).
// Never calls attest.
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
		// Dependency pin remediations are propose-only: never materialize the
		// "# … not auto-written" comment stub as package.json.
		if isPackageJSON(rel) && !json.Valid([]byte(strings.TrimSpace(h.Snippet))) {
			out = append(out, h)
			continue
		}
		path := filepath.Join(repoRoot, filepath.FromSlash(rel))
		applied, err := applyStubAt(path, rel, []byte(h.Snippet))
		if err != nil {
			return out, err
		}
		h.Applied = applied
		out = append(out, h)
	}
	return out, nil
}

// applyStubAt creates or heals a single stub path. Returns applied=false when a
// non-empty existing file is left untouched.
func applyStubAt(path, rel string, snippet []byte) (applied bool, err error) {
	st, err := os.Lstat(path)
	switch {
	case err == nil:
		if st.Mode()&os.ModeSymlink != 0 {
			return false, fmt.Errorf("refusing symlink remediation path: %s", rel)
		}
		if st.Size() > 0 {
			return false, nil
		}
		// Empty non-symlink: heal with write/trunc after Lstat proved safe.
		if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
			return false, err
		}
		return writeTruncAfterLstat(path, rel, snippet)
	case os.IsNotExist(err):
		if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
			return false, err
		}
		f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0o644)
		if err != nil {
			if errors.Is(err, os.ErrExist) {
				// Race: path appeared — do not skip-all; re-Lstat and heal empty only.
				return applyStubAt(path, rel, snippet)
			}
			return false, err
		}
		_, werr := f.Write(snippet)
		cerr := f.Close()
		if werr != nil {
			return false, werr
		}
		if cerr != nil {
			return false, cerr
		}
		return true, nil
	default:
		return false, err
	}
}

// writeTruncAfterLstat opens an existing non-symlink path for truncate+write.
// Re-Lstats immediately before open to refuse a symlink swap. Returns wrote=false
// if the file became non-empty between checks (leave content untouched).
func writeTruncAfterLstat(path, rel string, snippet []byte) (wrote bool, err error) {
	st, err := os.Lstat(path)
	if err != nil {
		return false, err
	}
	if st.Mode()&os.ModeSymlink != 0 {
		return false, fmt.Errorf("refusing symlink remediation path: %s", rel)
	}
	if st.Size() > 0 {
		return false, nil
	}
	f, err := os.OpenFile(path, os.O_WRONLY|os.O_TRUNC, 0o644)
	if err != nil {
		return false, err
	}
	_, werr := f.Write(snippet)
	cerr := f.Close()
	if werr != nil {
		return false, werr
	}
	if cerr != nil {
		return false, cerr
	}
	return true, nil
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
	if err := pathjail.ValidateRel(p); err != nil {
		if strings.Contains(err.Error(), ".git") {
			return "", fmt.Errorf("refusing remediation under .git: %s", p)
		}
		if strings.Contains(err.Error(), "traversal") {
			return "", fmt.Errorf("refusing path traversal in remediation: %s", p)
		}
		if strings.Contains(err.Error(), "absolute") {
			return "", fmt.Errorf("refusing absolute remediation path: %s", p)
		}
		if strings.Contains(err.Error(), "escape") {
			return "", fmt.Errorf("refusing path escape in remediation: %s", p)
		}
		return "", err
	}
	return filepath.ToSlash(filepath.Clean(p)), nil
}

func guessFile(gateID string) string {
	switch {
	case strings.Contains(gateID, "RISK"):
		return "docs/annex-vii/risk_assessment.md"
	case strings.Contains(gateID, "SUPPORT"):
		return "docs/annex-vii/support_period.md"
	case strings.Contains(gateID, "MANUAL"):
		return "docs/annex-vii/user_manual_security.md"
	case strings.Contains(gateID, "ART14") || strings.Contains(gateID, "ART-14"):
		return "docs/incident/art14-path.md"
	case strings.Contains(gateID, "SECURITY-MD") || strings.Contains(gateID, "SECURITY_MD"):
		return "SECURITY.md"
	case strings.Contains(gateID, "SECURITY-TXT") || strings.Contains(gateID, "SECURITY_TXT"):
		return ".well-known/security.txt"
	case strings.Contains(gateID, "SAFETY") || strings.Contains(gateID, "SW-CLASS") || strings.Contains(gateID, "SW_CLASS"):
		return "docs/medtech/software_safety_class.md"
	case strings.Contains(gateID, "SOUP"):
		return "docs/medtech/soup_list.md"
	case strings.Contains(gateID, "PROBLEM"):
		return "docs/medtech/problem_resolution.md"
	default:
		return ""
	}
}

func snippetForGate(gateID, file string) (string, bool) {
	return snippetForFailure(ir.Failure{GateID: gateID}, file)
}

func snippetForFailure(f ir.Failure, file string) (string, bool) {
	gateID := f.GateID
	if strings.Contains(gateID, "DEP") || strings.Contains(gateID, "AXIOS") {
		// Missing manifest: scaffold a present empty package.json so dep-ban can
		// vacuous-pass. Banned pins / invalid JSON stay propose-only comments.
		if isTargetAbsent(f) {
			return emptyPackageJSONStub(), true
		}
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

func isTargetAbsent(f ir.Failure) bool {
	return strings.Contains(strings.ToLower(f.SanitizedDescription), "target absent")
}

func isPackageJSON(file string) bool {
	return filepath.Base(filepath.ToSlash(strings.TrimSpace(file))) == "package.json"
}

// emptyPackageJSONStub is a present, pin-free manifest for heal of target-absent dep-ban.
func emptyPackageJSONStub() string {
	return "{\n  \"name\": \"app\",\n  \"version\": \"0.0.0\",\n  \"private\": true,\n  \"dependencies\": {}\n}\n"
}
