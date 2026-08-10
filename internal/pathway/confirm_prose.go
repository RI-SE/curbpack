package pathway

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/afelin/cyberready/internal/packs"
	"github.com/afelin/cyberready/internal/research"
)

// ProsePaths returns documentation targets that must exist before confirm-prose
// (annex_file / file_present / anti_placeholder). Excludes text_forbid ban paths
// such as .env — those must not be required to exist.
func ProsePaths(packIDs []string) ([]string, error) {
	composed, _, err := packs.Compose(packIDs)
	if err != nil {
		return nil, err
	}
	seen := map[string]struct{}{}
	var out []string
	add := func(rel string) error {
		rel = strings.TrimSpace(rel)
		if rel == "" {
			return nil
		}
		if err := packs.ValidateRelPath(rel); err != nil {
			return err
		}
		clean := filepath.ToSlash(filepath.Clean(rel))
		if _, ok := seen[clean]; ok {
			return nil
		}
		seen[clean] = struct{}{}
		out = append(out, clean)
		return nil
	}
	for _, r := range composed.Rules {
		switch r.Check {
		case "annex_file", "file_present":
			if err := add(r.Path); err != nil {
				return nil, fmt.Errorf("rule %q: %w", r.ID, err)
			}
		case "anti_placeholder":
			for _, path := range r.Paths {
				if err := add(path); err != nil {
					return nil, fmt.Errorf("rule %q: %w", r.ID, err)
				}
			}
		}
	}
	sort.Strings(out)
	return out, nil
}

// ConfirmProse stamps prose_owned after documentation targets for proposed packs exist.
func ConfirmProse(repoRoot string) (*Seed, error) {
	if _, err := Guard(repoRoot, EventConfirmProse); err != nil {
		return nil, err
	}
	s, err := Load(repoRoot)
	if err != nil {
		return nil, err
	}
	if s == nil || len(s.ProposedPacks) == 0 {
		return nil, ErrNoSuggest
	}
	paths, err := ProsePaths(s.ProposedPacks)
	if err != nil {
		return nil, err
	}
	missing := make([]string, 0)
	for _, rel := range paths {
		p := filepath.Join(repoRoot, filepath.FromSlash(rel))
		st, err := os.Stat(p)
		if err != nil || st.IsDir() {
			missing = append(missing, rel)
		}
	}
	if len(missing) > 0 {
		return nil, usagef("pathway confirm-prose: missing scaffold file(s): %s — run cyberready check --heal then edit real prose", strings.Join(missing, ", "))
	}
	// Cite-or-refuse when research packet is present (Write→Check HITL). Bring-docs may skip research.
	if pkt, err := research.LoadPacket(repoRoot); err != nil {
		return nil, err
	} else if pkt != nil {
		res := research.CiteCheckProsePaths(repoRoot, *pkt, paths)
		if !res.OK {
			msg := "pathway confirm-prose: cite-check refuse — fix drafts or run cyberready research --cite-check <file>"
			if len(res.Errors) > 0 {
				msg += ": " + res.Errors[0]
				if len(res.Errors) > 1 {
					msg += fmt.Sprintf(" (+%d more)", len(res.Errors)-1)
				}
			}
			return nil, usagef("%s", msg)
		}
	}
	s.HumanTicks.ProseOwned = true
	if err := Write(repoRoot, *s); err != nil {
		return nil, err
	}
	return s, nil
}
