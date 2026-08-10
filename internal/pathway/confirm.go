package pathway

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/afelin/cyberready/internal/config"
	"github.com/afelin/cyberready/internal/packs"
)

// KnownPackSet returns allowlisted embedded ids ∪ loadable imported ids.
func KnownPackSet() (map[string]struct{}, error) {
	ids, err := packs.ListIDs()
	if err != nil {
		return nil, err
	}
	out := make(map[string]struct{}, len(ids)+4)
	for _, id := range ids {
		out[id] = struct{}{}
	}
	// Imported / override packs under CYBERREADY_PACKS_DIR.
	if dir := strings.TrimSpace(os.Getenv("CYBERREADY_PACKS_DIR")); dir != "" {
		entries, err := os.ReadDir(dir)
		if err == nil {
			for _, e := range entries {
				if !e.IsDir() {
					continue
				}
				id := e.Name()
				if _, err := packs.LoadPack(id); err == nil {
					out[id] = struct{}{}
				}
			}
		}
	}
	return out, nil
}

// ErrNoSuggest is returned when confirm runs before suggest.
var ErrNoSuggest = usagef("pathway: run cyberready pathway suggest first")

// ConfirmPacks stamps packs_confirmed after validating proposed ids ∈ known set.
// On success, exports policy-graph.json (RKG) for confirmed packs (best-effort).
func ConfirmPacks(repoRoot string) (*Seed, error) {
	if _, err := Guard(repoRoot, EventConfirmPacks); err != nil {
		return nil, err
	}
	s, err := Load(repoRoot)
	if err != nil {
		return nil, err
	}
	if s == nil || len(s.ProposedPacks) == 0 {
		return nil, ErrNoSuggest
	}
	known, err := KnownPackSet()
	if err != nil {
		return nil, err
	}
	kept := IntersectKnown(s.ProposedPacks, known)
	if len(kept) != len(s.ProposedPacks) {
		unknown := missingFrom(s.ProposedPacks, known)
		return nil, usagef("pathway confirm-packs: unknown pack id(s) %s (∉ packs list ∪ imported)", strings.Join(unknown, ", "))
	}
	if len(kept) == 0 {
		return nil, usagef("pathway confirm-packs: no known pack ids in proposed_packs")
	}
	s.ProposedPacks = kept
	s.HumanTicks.PacksConfirmed = true
	if err := Write(repoRoot, *s); err != nil {
		return nil, err
	}
	// Workstream D: RKG after pack confirm (local policy graph for L4 navigation).
	if _, gerr := packs.ExportPolicyGraph(repoRoot, s.ProposedPacks, ""); gerr != nil {
		// Non-fatal: status may still hint packs export-graph when missing.
		_ = gerr
	}
	return s, nil
}

// ConfirmShare stamps share_reviewed when share artifacts are present.
func ConfirmShare(repoRoot string) (*Seed, error) {
	if _, err := Guard(repoRoot, EventConfirmShare); err != nil {
		return nil, err
	}
	s, err := Load(repoRoot)
	if err != nil {
		return nil, err
	}
	if s == nil || len(s.ProposedPacks) == 0 {
		return nil, ErrNoSuggest
	}
	if !shareArtifactsPresent(repoRoot) {
		return nil, usagef("pathway confirm-share: no share artifacts — run cyberready share first")
	}
	s.HumanTicks.ShareReviewed = true
	if err := Write(repoRoot, *s); err != nil {
		return nil, err
	}
	return s, nil
}

func shareArtifactsPresent(repoRoot string) bool {
	candidates := []string{
		filepath.Join(repoRoot, ".github", "cyberready", "cache", "buyer-questions.md"),
		filepath.Join(repoRoot, ".github", "cyberready", "cache", "buyer-questions.json"),
		filepath.Join(repoRoot, ".github", "cyberready", "cache", "context-pack.json"),
		filepath.Join(repoRoot, "review-pack"),
	}
	for _, p := range candidates {
		if st, err := os.Stat(p); err == nil {
			if st.IsDir() {
				// review-pack dir counts if non-empty
				ents, _ := os.ReadDir(p)
				if len(ents) > 0 {
					return true
				}
				continue
			}
			return true
		}
	}
	return false
}

func missingFrom(proposed []string, known map[string]struct{}) []string {
	var out []string
	for _, id := range proposed {
		if _, ok := known[id]; !ok {
			out = append(out, id)
		}
	}
	return out
}

// ApplySuggest writes a fresh seed from SuggestResult (resets human ticks).
func ApplySuggest(repoRoot string, r SuggestResult) (*Seed, error) {
	known, err := KnownPackSet()
	if err != nil {
		return nil, err
	}
	kept := IntersectKnown(r.ProposedPacks, known)
	if len(kept) == 0 {
		return nil, fmt.Errorf("pathway suggest: no known pack ids after closed-world intersect")
	}
	s := Seed{
		SchemaVersion: SchemaVersion,
		Answers:       r.Answers,
		ProposedPacks: kept,
		NextHint:      r.NextHint,
		HumanTicks:    HumanTicks{},
		Claim:         ClaimFence,
	}
	if err := Write(repoRoot, s); err != nil {
		return nil, err
	}
	return &s, nil
}

// ConfiguredPacks reports packs from .cyberready.json if present.
func ConfiguredPacks(repoRoot string) ([]string, bool) {
	cfg, err := config.Load(repoRoot)
	if err != nil || cfg == nil || len(cfg.Packs) == 0 {
		return nil, false
	}
	return cfg.Packs, true
}

// LastCheckGreen reads latest_result.json failures; missing file → false, false.
func LastCheckGreen(repoRoot string) (green bool, ok bool) {
	path := filepath.Join(repoRoot, ".github", "cyberready", "cache", "latest_result.json")
	data, err := os.ReadFile(path)
	if err != nil {
		return false, false
	}
	var payload struct {
		Failures []json.RawMessage `json:"failures"`
	}
	if err := json.Unmarshal(data, &payload); err != nil {
		return false, false
	}
	return len(payload.Failures) == 0, true
}
