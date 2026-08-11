// Package remediation stores last-good form-hint snippets by gate_id (spec §6.3 lite).
// Heal may write missing stubs only — never auto-attest.
package remediation

import (
	"encoding/json"
	"os"
	"path/filepath"
	"time"

	"github.com/afelin/curbpack/internal/paths"
)

// Entry is one cached remediation for a gate.
type Entry struct {
	GateID  string `json:"gate_id"`
	File    string `json:"file,omitempty"`
	Snippet string `json:"snippet,omitempty"`
	Action  string `json:"action,omitempty"`
	Updated string `json:"updated,omitempty"`
}

// Cache is the on-disk remediation map.
type Cache struct {
	Version int              `json:"version"`
	Updated string           `json:"updated,omitempty"`
	Entries map[string]Entry `json:"entries"`
}

// Path returns the write path for remediations.json under repoRoot.
func Path(repoRoot string) string {
	return filepath.Join(paths.CacheDir(repoRoot), "remediations.json")
}

// Load reads remediations.json (new or legacy cache); missing file yields empty cache.
func Load(repoRoot string) (Cache, error) {
	c := Cache{Version: 1, Entries: map[string]Entry{}}
	data, err := os.ReadFile(paths.ResolveUnderCache(repoRoot, "remediations.json"))
	if err != nil {
		if os.IsNotExist(err) {
			return c, nil
		}
		return c, err
	}
	if err := json.Unmarshal(data, &c); err != nil {
		return Cache{Version: 1, Entries: map[string]Entry{}}, err
	}
	if c.Entries == nil {
		c.Entries = map[string]Entry{}
	}
	if c.Version == 0 {
		c.Version = 1
	}
	return c, nil
}

// Save writes remediations.json.
func Save(repoRoot string, c Cache) error {
	c.Version = 1
	c.Updated = time.Now().UTC().Format(time.RFC3339)
	if c.Entries == nil {
		c.Entries = map[string]Entry{}
	}
	dir := filepath.Dir(Path(repoRoot))
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(c, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(Path(repoRoot), append(data, '\n'), 0o644)
}

// Upsert merges entries by gate_id.
func Upsert(c *Cache, entries ...Entry) {
	if c.Entries == nil {
		c.Entries = map[string]Entry{}
	}
	now := time.Now().UTC().Format(time.RFC3339)
	for _, e := range entries {
		if e.GateID == "" {
			continue
		}
		e.Updated = now
		c.Entries[e.GateID] = e
	}
}

// Lookup returns a cached entry if present.
func Lookup(c Cache, gateID string) (Entry, bool) {
	if c.Entries == nil {
		return Entry{}, false
	}
	e, ok := c.Entries[gateID]
	return e, ok
}
