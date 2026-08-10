// Package pathway is the sole writer of pathway-seed.json — warm-start HITL ticks.
// Deterministic closed-world suggest; check does not consume this file for pass/fail.
package pathway

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// SchemaVersion is the on-disk pathway-seed.json version.
const SchemaVersion = 1

// ClaimFence is the fixed claim string stamped on every seed write.
const ClaimFence = "Prepares evidence for human review — not a conformity assessment."

// SeedPath returns .github/cyberready/cache/pathway-seed.json under repo root.
func SeedPath(repoRoot string) string {
	return filepath.Join(repoRoot, ".github", "cyberready", "cache", "pathway-seed.json")
}

// Answers are closed enum answers from pathway suggest flags.
type Answers struct {
	Product    string `json:"product"`     // hygiene | shipping
	EuDocs     string `json:"eu_docs"`     // yes | no
	Medtech    string `json:"medtech"`     // yes | no
	Sector     string `json:"sector"`      // none | other
	HouseFirst string `json:"house_first"` // yes | no
	CeContext  string `json:"ce_context"`  // none | in_procedure (context only)
}

// HumanTicks are CLI-stamped HITL confirms — never forged by chat/MCP.
type HumanTicks struct {
	PacksConfirmed bool `json:"packs_confirmed"`
	ProseOwned     bool `json:"prose_owned"`
	ShareReviewed  bool `json:"share_reviewed"`
}

// Seed is the on-disk IR for pathway state.
type Seed struct {
	SchemaVersion int        `json:"schema_version"`
	Answers       Answers    `json:"answers"`
	ProposedPacks []string   `json:"proposed_packs"`
	NextHint      string     `json:"next_hint,omitempty"`
	HumanTicks    HumanTicks `json:"human_ticks"`
	Claim         string     `json:"claim"`
}

// Load reads pathway-seed.json. Returns nil, nil if missing.
func Load(repoRoot string) (*Seed, error) {
	path := SeedPath(repoRoot)
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, err
	}
	var s Seed
	if err := json.Unmarshal(data, &s); err != nil {
		return nil, fmt.Errorf("parse pathway-seed.json: %w", err)
	}
	return &s, nil
}

// Write persists seed (sole writer API for pathway CLI).
func Write(repoRoot string, s Seed) error {
	s.SchemaVersion = SchemaVersion
	s.Claim = ClaimFence
	dir := filepath.Dir(SeedPath(repoRoot))
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return err
	}
	b, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(SeedPath(repoRoot), append(b, '\n'), 0o644)
}
