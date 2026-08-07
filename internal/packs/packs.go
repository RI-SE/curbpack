package packs

import (
	"embed"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

//go:embed data/cra-baseline/pack.json data/medtech-iec62304/pack.json data/_watchlist.json
var embedded embed.FS

// Rule is a single pack gate definition (JSON-eval, no OPA).
type Rule struct {
	ID             string   `json:"id"`
	Severity       string   `json:"severity"`
	Type           string   `json:"type"`
	Check          string   `json:"check"`
	Path           string   `json:"path,omitempty"`
	Paths          []string `json:"paths,omitempty"`
	MinBytes       int      `json:"min_bytes,omitempty"`
	RequireHeaders []string `json:"require_headers,omitempty"`
	Package        string   `json:"package,omitempty"`
	BannedVersions []string `json:"banned_versions,omitempty"`
	Description    string   `json:"description"`
	Remediation    string   `json:"remediation"`
	Expected       string   `json:"expected"`
}

// Pack is an embedded regulation pack.
type Pack struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Rules       []Rule `json:"rules"`
}

// Watchlist is informational only.
type Watchlist struct {
	Version int              `json:"version"`
	Updated string           `json:"updated"`
	Note    string           `json:"note"`
	Entries []WatchlistEntry `json:"entries"`
}

// WatchlistEntry is one informational advisory row.
type WatchlistEntry struct {
	ID        string   `json:"id"`
	Ecosystem string   `json:"ecosystem"`
	Package   string   `json:"package"`
	Versions  []string `json:"versions"`
	Reason    string   `json:"reason"`
	Refs      []string `json:"refs"`
}

var builtinIDs = []string{"cra-baseline", "medtech-iec62304"}

// LoadEmbedded returns all built-in packs.
func LoadEmbedded() ([]Pack, error) {
	out := make([]Pack, 0, len(builtinIDs))
	for _, id := range builtinIDs {
		p, err := LoadPack(id)
		if err != nil {
			return nil, err
		}
		out = append(out, p)
	}
	return out, nil
}

// LoadPack loads one pack by id from embed, or from CYBERREADY_PACKS_DIR override.
func LoadPack(id string) (Pack, error) {
	if dir := strings.TrimSpace(os.Getenv("CYBERREADY_PACKS_DIR")); dir != "" {
		data, err := os.ReadFile(filepath.Join(dir, id, "pack.json"))
		if err == nil {
			var p Pack
			if err := json.Unmarshal(data, &p); err != nil {
				return Pack{}, err
			}
			return p, nil
		}
	}
	data, err := embedded.ReadFile("data/" + id + "/pack.json")
	if err != nil {
		return Pack{}, fmt.Errorf("pack %q not found: %w", id, err)
	}
	var p Pack
	if err := json.Unmarshal(data, &p); err != nil {
		return Pack{}, err
	}
	return p, nil
}

// LoadWatchlist returns the embedded (or overridden) watchlist.
func LoadWatchlist() (Watchlist, error) {
	if dir := strings.TrimSpace(os.Getenv("CYBERREADY_PACKS_DIR")); dir != "" {
		data, err := os.ReadFile(filepath.Join(dir, "_watchlist.json"))
		if err == nil {
			var w Watchlist
			if err := json.Unmarshal(data, &w); err != nil {
				return Watchlist{}, err
			}
			return w, nil
		}
	}
	data, err := embedded.ReadFile("data/_watchlist.json")
	if err != nil {
		return Watchlist{}, err
	}
	var w Watchlist
	if err := json.Unmarshal(data, &w); err != nil {
		return Watchlist{}, err
	}
	return w, nil
}

// ListIDs returns sorted pack identifiers.
func ListIDs() ([]string, error) {
	packs, err := LoadEmbedded()
	if err != nil {
		return nil, err
	}
	ids := make([]string, 0, len(packs))
	for _, p := range packs {
		ids = append(ids, p.ID)
	}
	sort.Strings(ids)
	return ids, nil
}

// ExportPackJSON writes a pack JSON to destDir/<id>/pack.json (air-gap helper).
func ExportPackJSON(id, destDir string) error {
	p, err := LoadPack(id)
	if err != nil {
		return err
	}
	dir := filepath.Join(destDir, id)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(p, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(filepath.Join(dir, "pack.json"), append(data, '\n'), 0o644)
}
