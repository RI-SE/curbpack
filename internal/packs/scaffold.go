package packs

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
)

// RepoToken returns a best-effort product token for bind_repo_token and
// heal-stub overlap (stub + token insertion still counts as DefaultScaffoldBody).
// Preference: package.json "name", then go.mod module path, then directory basename.
func RepoToken(root string) (string, bool) {
	if name, ok := readPackageJSONName(root); ok {
		return name, true
	}
	if mod, ok := readGoModModule(root); ok {
		return mod, true
	}
	base := filepath.Base(filepath.Clean(root))
	if base == "" || base == "." || base == string(filepath.Separator) {
		return "", false
	}
	return base, true
}

func readPackageJSONName(root string) (string, bool) {
	b, err := os.ReadFile(filepath.Join(root, "package.json"))
	if err != nil {
		return "", false
	}
	var meta struct {
		Name string `json:"name"`
	}
	if err := json.Unmarshal(b, &meta); err != nil {
		return "", false
	}
	name := strings.TrimSpace(meta.Name)
	if name == "" {
		return "", false
	}
	return name, true
}

func readGoModModule(root string) (string, bool) {
	b, err := os.ReadFile(filepath.Join(root, "go.mod"))
	if err != nil {
		return "", false
	}
	for _, line := range strings.Split(string(b), "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "module ") {
			mod := strings.TrimSpace(strings.TrimPrefix(line, "module "))
			if mod != "" {
				return mod, true
			}
		}
	}
	return "", false
}

// ScaffoldOverlap reports whether text is still DefaultScaffoldBody(rel),
// allowing collapsed whitespace and a single optional repo-token insertion.
// Heal stubs are not grounding artifacts.
func ScaffoldOverlap(text, rel, token string) bool {
	scaffold := DefaultScaffoldBody(rel)
	normScaffold := collapseWS(scaffold)
	if collapseWS(text) == normScaffold {
		return true
	}
	if token != "" && collapseWS(stripFirst(text, token)) == normScaffold {
		return true
	}
	return false
}

func collapseWS(s string) string {
	return strings.Join(strings.Fields(s), " ")
}

func stripFirst(s, token string) string {
	if token == "" {
		return s
	}
	i := strings.Index(s, token)
	if i < 0 {
		return s
	}
	return s[:i] + s[i+len(token):]
}
