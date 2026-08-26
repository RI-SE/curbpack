package packs

import (
	"encoding/json"
	"fmt"
	"sort"
	"strings"
	"time"
)

// ComposeResult is a merged pack view for evaluation.
type ComposeResult struct {
	Pack      Pack
	SourceIDs []string // topological load order (bases first)
}

// Compose loads requested pack IDs, expands extends/overlays, and unions rules by id
// (later wins). Detects extends cycles. Dedupes when an overlay and its base are both requested.
func Compose(ids []string) (Pack, []string, error) {
	if len(ids) == 0 {
		return Pack{}, nil, fmt.Errorf("compose: empty pack id list")
	}
	order := make([]string, 0, len(ids)*2)
	seen := map[string]struct{}{}
	visiting := map[string]struct{}{}

	var visit func(id string) error
	visit = func(id string) error {
		id = strings.TrimSpace(id)
		if id == "" {
			return fmt.Errorf("compose: empty pack id")
		}
		if _, ok := seen[id]; ok {
			return nil
		}
		if _, ok := visiting[id]; ok {
			return fmt.Errorf("compose: extends cycle involving %q", id)
		}
		visiting[id] = struct{}{}
		p, err := LoadPack(id)
		if err != nil {
			return err
		}
		if base := strings.TrimSpace(p.Extends); base != "" {
			if err := visit(base); err != nil {
				return err
			}
		}
		for _, ov := range p.Overlays {
			if err := visit(strings.TrimSpace(ov)); err != nil {
				return err
			}
		}
		delete(visiting, id)
		seen[id] = struct{}{}
		order = append(order, id)
		return nil
	}

	for _, id := range ids {
		if err := visit(id); err != nil {
			return Pack{}, nil, err
		}
	}

	byRule := map[string]Rule{}
	ruleOrder := make([]string, 0)
	var citations []Citation
	jurisdiction := ""
	var validity *Validity
	supersedes, supersededBy := "", ""
	nameParts := make([]string, 0, len(order))
	versions := make([]string, 0, len(order))

	assuranceClass := ""
	for _, id := range order {
		p, err := LoadPack(id)
		if err != nil {
			return Pack{}, nil, err
		}
		if len(p.Overlay) > 0 && string(p.Overlay) != "null" {
			merged, err := applyMergePatchPack(p)
			if err != nil {
				return Pack{}, nil, fmt.Errorf("pack %q overlay merge-patch: %w", id, err)
			}
			p = merged
		}
		if ac := strings.TrimSpace(p.AssuranceClass); ac != "" {
			assuranceClass = ac
		}
		nameParts = append(nameParts, p.Name)
		versions = append(versions, p.ID+"@"+p.Version)
		if p.Jurisdiction != "" {
			jurisdiction = p.Jurisdiction
		}
		if p.Validity != nil {
			validity = p.Validity
		}
		if p.Supersedes != "" {
			supersedes = p.Supersedes
		}
		if p.SupersededBy != "" {
			supersededBy = p.SupersededBy
		}
		citations = append(citations, p.Citations...)
		for _, r := range p.Rules {
			if _, ok := byRule[r.ID]; !ok {
				ruleOrder = append(ruleOrder, r.ID)
			}
			byRule[r.ID] = r
		}
	}

	rules := make([]Rule, 0, len(ruleOrder))
	for _, rid := range ruleOrder {
		rules = append(rules, byRule[rid])
	}

	composedID := strings.Join(uniquePreserve(ids), "+")
	out := Pack{
		ID:             composedID,
		Name:           strings.Join(nameParts, " + "),
		Version:        strings.Join(versions, ","),
		Description:    "Composed pack view (extends/overlays merged; later rule id wins).",
		AssuranceClass: assuranceClass,
		Jurisdiction:   jurisdiction,
		Validity:       validity,
		Supersedes:     supersedes,
		SupersededBy:   supersededBy,
		Citations:      citations,
		Rules:          rules,
	}
	if err := ValidatePack(out); err != nil {
		return Pack{}, nil, fmt.Errorf("composed pack invalid: %w", err)
	}
	return out, order, nil
}

func uniquePreserve(in []string) []string {
	seen := map[string]struct{}{}
	var out []string
	for _, s := range in {
		s = strings.TrimSpace(s)
		if s == "" {
			continue
		}
		if _, ok := seen[s]; ok {
			continue
		}
		seen[s] = struct{}{}
		out = append(out, s)
	}
	return out
}

// applyMergePatchPack applies optional RFC 7386-style merge-patch stored in Pack.Overlay
// onto a shallow JSON clone of the pack (rules arrays replaced when present in patch).
func applyMergePatchPack(p Pack) (Pack, error) {
	baseBytes, err := json.Marshal(p)
	if err != nil {
		return Pack{}, err
	}
	var base map[string]any
	if err := json.Unmarshal(baseBytes, &base); err != nil {
		return Pack{}, err
	}
	var patch map[string]any
	if err := json.Unmarshal(p.Overlay, &patch); err != nil {
		return Pack{}, err
	}
	merged := mergePatch(base, patch)
	delete(merged, "overlay") // avoid re-applying
	outBytes, err := json.Marshal(merged)
	if err != nil {
		return Pack{}, err
	}
	var out Pack
	if err := json.Unmarshal(outBytes, &out); err != nil {
		return Pack{}, err
	}
	return out, nil
}

func mergePatch(target, patch map[string]any) map[string]any {
	out := map[string]any{}
	for k, v := range target {
		out[k] = v
	}
	for k, v := range patch {
		if v == nil {
			delete(out, k)
			continue
		}
		pm, pok := v.(map[string]any)
		tm, tok := out[k].(map[string]any)
		if pok && tok {
			out[k] = mergePatch(tm, pm)
			continue
		}
		out[k] = v
	}
	return out
}

// DoctorFindings reports expired / superseded / pin-skew signals (informational).
type DoctorFindings struct {
	Expired     []string `json:"expired,omitempty"`
	Superseded  []string `json:"superseded,omitempty"`
	PinSkew     []string `json:"pin_skew,omitempty"`
	UnknownBase []string `json:"unknown_extends,omitempty"`
	OK          bool     `json:"ok"`
}

// DoctorPacks inspects embedded (or override) packs for validity/supersession issues.
func DoctorPacks() (DoctorFindings, error) {
	ids, err := ListIDs()
	if err != nil {
		return DoctorFindings{}, err
	}
	sort.Strings(ids)
	var f DoctorFindings
	f.OK = true
	now := timeNowDate()
	for _, id := range ids {
		p, err := LoadPack(id)
		if err != nil {
			return DoctorFindings{}, err
		}
		if p.SupersededBy != "" {
			f.Superseded = append(f.Superseded, fmt.Sprintf("%s superseded_by %s", id, p.SupersededBy))
			f.OK = false
		}
		if p.Validity != nil && strings.TrimSpace(p.Validity.EffectiveTo) != "" {
			if expired, err := dateOnOrBefore(p.Validity.EffectiveTo, now); err == nil && expired {
				f.Expired = append(f.Expired, fmt.Sprintf("%s effective_to=%s", id, p.Validity.EffectiveTo))
				f.OK = false
			}
		}
		if base := strings.TrimSpace(p.Extends); base != "" {
			if _, err := LoadPack(base); err != nil {
				f.UnknownBase = append(f.UnknownBase, fmt.Sprintf("%s extends missing %q", id, base))
				f.OK = false
			}
		}
	}
	// Pin skew: CURBPACK_PACKS_DIR / legacy CYBERREADY_PACKS_DIR present but versions differ from embed for same id.
	if dir := strings.TrimSpace(envPacksDir()); dir != "" {
		for _, id := range builtinIDs {
			override, err := loadPackFromDir(dir, id)
			if err != nil {
				continue
			}
			embedP, err := loadPackEmbeddedOnly(id)
			if err != nil {
				continue
			}
			if override.Version != embedP.Version {
				f.PinSkew = append(f.PinSkew, fmt.Sprintf("%s override=%s embed=%s", id, override.Version, embedP.Version))
				f.OK = false
			}
		}
	}
	return f, nil
}

func timeNowDate() time.Time {
	return time.Now().UTC().Truncate(24 * time.Hour)
}

func dateOnOrBefore(effectiveTo string, now time.Time) (bool, error) {
	effectiveTo = strings.TrimSpace(effectiveTo)
	var t time.Time
	var err error
	if t, err = time.Parse("2006-01-02", effectiveTo); err != nil {
		if t, err = time.Parse(time.RFC3339, effectiveTo); err != nil {
			return false, err
		}
	}
	return !t.After(now), nil
}
