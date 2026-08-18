// Package paths holds Curbpack on-disk locations with dual-read of legacy CyberReady paths.
package paths

import (
	"os"
	"path/filepath"
	"strings"
)

const (
	// Product / CLI
	ProductName = "Curbpack"
	CLIName     = "curbpack"
	CLIAlias    = "curb"

	// Config (write-new)
	ConfigFile       = ".curbpack.json"
	LegacyConfigFile = ".cyberready.json"

	// GitHub tree under repo (write-new)
	GitHubDir       = ".github/curbpack"
	LegacyGitHubDir = ".github/cyberready"

	CacheRel       = ".github/curbpack/cache"
	LegacyCacheRel = ".github/cyberready/cache"

	EvidenceRel       = ".github/curbpack/evidence"
	LegacyEvidenceRel = ".github/cyberready/evidence"

	GraphRel       = ".github/curbpack/graph"
	LegacyGraphRel = ".github/cyberready/graph"

	// Git notes (write-new)
	NotesRef         = "refs/notes/curbpack"
	LegacyNotesRef   = "refs/notes/cyberready"
	NotesShort       = "curbpack"
	LegacyNotesShort = "cyberready"

	// Cursor skill install path
	SkillRel       = ".cursor/skills/curbpack"
	LegacySkillRel = ".cursor/skills/cyberready"

	// Workflow drop-in
	WorkflowDestRel = ".github/workflows/curbpack.yml"
)

// ConfigPath is the write path for adopter config.
func ConfigPath(root string) string {
	return filepath.Join(root, ConfigFile)
}

// ResolveConfigPath returns new config if present, else legacy, else new (for create).
func ResolveConfigPath(root string) string {
	neu := filepath.Join(root, ConfigFile)
	if fileExists(neu) {
		return neu
	}
	legacy := filepath.Join(root, LegacyConfigFile)
	if fileExists(legacy) {
		return legacy
	}
	return neu
}

// CacheDir is the write path for cache artifacts.
func CacheDir(root string) string {
	return filepath.Join(root, filepath.FromSlash(CacheRel))
}

// ResolveCacheDir prefers new cache dir if it exists; else legacy; else new.
func ResolveCacheDir(root string) string {
	return resolveDir(root, CacheRel, LegacyCacheRel)
}

// EvidenceDir is the write path for evidence pointers.
func EvidenceDir(root string) string {
	return filepath.Join(root, filepath.FromSlash(EvidenceRel))
}

// ResolveEvidenceDir prefers new evidence dir if present; else legacy; else new.
func ResolveEvidenceDir(root string) string {
	return resolveDir(root, EvidenceRel, LegacyEvidenceRel)
}

// GraphDir is the write path for policy graph.
func GraphDir(root string) string {
	return filepath.Join(root, filepath.FromSlash(GraphRel))
}

// ResolveGraphDir prefers new graph dir if present; else legacy; else new.
func ResolveGraphDir(root string) string {
	return resolveDir(root, GraphRel, LegacyGraphRel)
}

// ResolveUnderCache joins name under resolved cache (read dual-path).
func ResolveUnderCache(root, name string) string {
	neu := filepath.Join(CacheDir(root), name)
	if fileExists(neu) {
		return neu
	}
	legacy := filepath.Join(root, filepath.FromSlash(LegacyCacheRel), name)
	if fileExists(legacy) {
		return legacy
	}
	return neu
}

// ResolveUnderEvidence joins name under resolved evidence (read dual-path).
func ResolveUnderEvidence(root, name string) string {
	neu := filepath.Join(EvidenceDir(root), name)
	if fileExists(neu) {
		return neu
	}
	legacy := filepath.Join(root, filepath.FromSlash(LegacyEvidenceRel), name)
	if fileExists(legacy) {
		return legacy
	}
	return neu
}

// ResolveUnderGraph joins name under resolved graph (read dual-path).
func ResolveUnderGraph(root, name string) string {
	neu := filepath.Join(GraphDir(root), name)
	if fileExists(neu) {
		return neu
	}
	legacy := filepath.Join(root, filepath.FromSlash(LegacyGraphRel), name)
	if fileExists(legacy) {
		return legacy
	}
	return neu
}

// Env reads CURBPACK_<key> then falls back to CYBERREADY_<key>.
func Env(key string) string {
	key = strings.TrimSpace(key)
	if key == "" {
		return ""
	}
	if v := strings.TrimSpace(os.Getenv("CURBPACK_" + key)); v != "" {
		return v
	}
	return strings.TrimSpace(os.Getenv("CYBERREADY_" + key))
}

// EnvIs1 is true when CURBPACK_<key> or legacy CYBERREADY_<key> is "1".
func EnvIs1(key string) bool {
	return Env(key) == "1"
}

// IsCacheRel reports whether rel is under the agent cache (write-new or legacy).
// Cache-only files are not independent grounding artifacts for confirm-prose.
func IsCacheRel(rel string) bool {
	rel = filepath.ToSlash(strings.TrimSpace(rel))
	rel = strings.TrimPrefix(rel, "./")
	if rel == "" {
		return false
	}
	return rel == CacheRel || strings.HasPrefix(rel, CacheRel+"/") ||
		rel == LegacyCacheRel || strings.HasPrefix(rel, LegacyCacheRel+"/")
}

func resolveDir(root, neuRel, legacyRel string) string {
	neu := filepath.Join(root, filepath.FromSlash(neuRel))
	if dirExists(neu) {
		return neu
	}
	legacy := filepath.Join(root, filepath.FromSlash(legacyRel))
	if dirExists(legacy) {
		return legacy
	}
	return neu
}

func fileExists(p string) bool {
	st, err := os.Stat(p)
	return err == nil && !st.IsDir()
}

func dirExists(p string) bool {
	st, err := os.Stat(p)
	return err == nil && st.IsDir()
}
