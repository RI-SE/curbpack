package pathway

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/afelin/curbpack/internal/packs"
	"github.com/afelin/curbpack/internal/research"
)

// ErrCiteRefuse marks confirm-prose blocked by research cite-check (CLI → exit 1).
var ErrCiteRefuse = errors.New("pathway cite-check refuse")

// ErrInformedConsent marks confirm-prose when any displayed prose path is not independent (CLI → exit 1).
var ErrInformedConsent = errors.New("pathway informed-consent refuse")

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

// ConfirmProse stamps prose_owned after documentation targets exist, every
// displayed prose path is independent (non-stub, non-empty, non-cache), and ground-check passes.
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
		return nil, usagef("pathway confirm-prose: missing scaffold file(s): %s — run curbpack check --heal then edit real prose", strings.Join(missing, ", "))
	}
	// Informed-consent AND: every displayed prose path must be independent.
	independent := research.IndependentGrounding(repoRoot, paths)
	if len(independent) != len(paths) {
		stubs := research.NotIndependent(repoRoot, paths)
		msg := "pathway confirm-prose: informed-consent refuse — every displayed prose path must be independent (heal-stub / empty / agent-cache is not grounding)"
		if len(stubs) > 0 {
			msg += "; not independent: " + strings.Join(stubs, ", ")
		}
		return nil, fmt.Errorf("%w: %s", ErrInformedConsent, msg)
	}
	// Ground-check always (inward cite-check). Packet on disk if present; else in-memory from packs.
	pkt, err := research.LoadPacket(repoRoot)
	if err != nil {
		return nil, err
	}
	if pkt == nil {
		built, berr := research.Build(research.Options{RepoRoot: repoRoot, PackIDs: s.ProposedPacks})
		if berr != nil {
			return nil, berr
		}
		pkt = &built
	}
	res := research.CiteCheckProsePaths(repoRoot, *pkt, paths)
	if !res.OK {
		msg := "pathway confirm-prose: cite-check refuse — ungrounded factual assertion (repo artifact or allowlisted cite)"
		if len(res.Errors) > 0 {
			msg += ": " + res.Errors[0]
			if len(res.Errors) > 1 {
				msg += fmt.Sprintf(" (+%d more)", len(res.Errors)-1)
			}
		}
		return nil, fmt.Errorf("%w: %s", ErrCiteRefuse, msg)
	}
	s.HumanTicks.ProseOwned = true
	if err := Write(repoRoot, *s); err != nil {
		return nil, err
	}
	// Force AwaitCheck: stale green latest_result must not skip re-check after prose ownership.
	_ = invalidateLatestResult(repoRoot)
	return s, nil
}

func invalidateLatestResult(repoRoot string) error {
	path := filepath.Join(repoRoot, ".github", "curbpack", "cache", "latest_result.json")
	if err := os.Remove(path); err != nil && !os.IsNotExist(err) {
		return err
	}
	return nil
}
