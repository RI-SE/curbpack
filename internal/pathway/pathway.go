// Package pathway is the sole writer of pathway-seed.json — warm-start HITL ticks.
// Deterministic closed-world suggest; check does not consume this file for pass/fail.
package pathway

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// SchemaVersion is the on-disk pathway-seed.json version.
const SchemaVersion = 1

// ClaimFence is the fixed claim string stamped on every seed write.
const ClaimFence = "Prepares evidence for human review — not a conformity assessment."

// ValidDraftPicks are allowed last_draft_pick values.
var ValidDraftPicks = map[string]struct{}{
	"A": {}, "B": {}, "edited": {},
}

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
// SessionNotes, Corrections, and LastDraftPick are session memory only — never check inputs.
type Seed struct {
	SchemaVersion int               `json:"schema_version"`
	Answers       Answers           `json:"answers"`
	ProposedPacks []string          `json:"proposed_packs"`
	NextHint      string            `json:"next_hint,omitempty"`
	HumanTicks    HumanTicks        `json:"human_ticks"`
	SessionNotes  []string          `json:"session_notes,omitempty"`
	Corrections   map[string]string `json:"corrections,omitempty"`
	LastDraftPick string            `json:"last_draft_pick,omitempty"` // A | B | edited
	Claim         string            `json:"claim"`
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

// NoteSet applies --set: key=value → corrections (or last_draft_pick); bare text → session_notes.
func NoteSet(repoRoot, raw string) (*Seed, error) {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return nil, usagef("pathway note --set requires a note or key=value")
	}
	s, err := loadOrEmpty(repoRoot)
	if err != nil {
		return nil, err
	}
	if key, val, ok := strings.Cut(raw, "="); ok {
		key = strings.TrimSpace(key)
		val = strings.TrimSpace(val)
		if key == "" {
			return nil, usagef("pathway note --set: empty key before =")
		}
		if key == "last_draft_pick" {
			if _, ok := ValidDraftPicks[val]; !ok {
				return nil, usagef("pathway note: last_draft_pick must be A, B, or edited")
			}
			s.LastDraftPick = val
		} else {
			if s.Corrections == nil {
				s.Corrections = map[string]string{}
			}
			s.Corrections[key] = val
		}
	} else {
		s.SessionNotes = append(s.SessionNotes, raw)
	}
	if err := Write(repoRoot, *s); err != nil {
		return nil, err
	}
	return s, nil
}

// NoteForget applies --forget: last_draft_pick | correction key | exact session note text.
func NoteForget(repoRoot, raw string) (*Seed, error) {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return nil, usagef("pathway note --forget requires a key or note text")
	}
	s, err := Load(repoRoot)
	if err != nil {
		return nil, err
	}
	if s == nil {
		return nil, usagef("pathway note --forget: no pathway-seed.json — run pathway suggest first")
	}
	switch {
	case raw == "last_draft_pick":
		s.LastDraftPick = ""
	case s.Corrections != nil && hasCorrection(s.Corrections, raw):
		delete(s.Corrections, raw)
		if len(s.Corrections) == 0 {
			s.Corrections = nil
		}
	default:
		kept := s.SessionNotes[:0]
		found := false
		for _, n := range s.SessionNotes {
			if n == raw {
				found = true
				continue
			}
			kept = append(kept, n)
		}
		if !found {
			return nil, usagef("pathway note --forget: %q not found in corrections or session_notes", raw)
		}
		s.SessionNotes = kept
	}
	if err := Write(repoRoot, *s); err != nil {
		return nil, err
	}
	return s, nil
}

func hasCorrection(m map[string]string, key string) bool {
	_, ok := m[key]
	return ok
}

func loadOrEmpty(repoRoot string) (*Seed, error) {
	s, err := Load(repoRoot)
	if err != nil {
		return nil, err
	}
	if s != nil {
		return s, nil
	}
	return &Seed{
		SchemaVersion: SchemaVersion,
		Claim:         ClaimFence,
	}, nil
}
