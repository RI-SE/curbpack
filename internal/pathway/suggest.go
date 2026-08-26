package pathway

import (
	"fmt"
	"strings"
)

// SuggestResult is the deterministic closed-world output of Suggest.
type SuggestResult struct {
	Answers       Answers
	ProposedPacks []string
	NextHint      string
}

var (
	enumProduct   = map[string]struct{}{"hygiene": {}, "shipping": {}}
	enumYesNo     = map[string]struct{}{"yes": {}, "no": {}}
	enumSector    = map[string]struct{}{"none": {}, "other": {}}
	enumCeContext = map[string]struct{}{"none": {}, "in_procedure": {}}
)

// ValidateAnswers checks closed enum sets. Returns a usage-style error on unknown values.
func ValidateAnswers(a Answers) error {
	a = normalizeAnswers(a)
	if _, ok := enumProduct[a.Product]; !ok {
		return fmt.Errorf("invalid --product %q (want hygiene|shipping)", a.Product)
	}
	if _, ok := enumYesNo[a.EuDocs]; !ok {
		return fmt.Errorf("invalid --eu-docs %q (want yes|no)", a.EuDocs)
	}
	if _, ok := enumYesNo[a.Medtech]; !ok {
		return fmt.Errorf("invalid --medtech %q (want yes|no)", a.Medtech)
	}
	if _, ok := enumSector[a.Sector]; !ok {
		return fmt.Errorf("invalid --sector %q (want none|other)", a.Sector)
	}
	if _, ok := enumYesNo[a.HouseFirst]; !ok {
		return fmt.Errorf("invalid --house-first %q (want yes|no)", a.HouseFirst)
	}
	if _, ok := enumCeContext[a.CeContext]; !ok {
		return fmt.Errorf("invalid --ce-context %q (want none|in_procedure)", a.CeContext)
	}
	return nil
}

func normalizeAnswers(a Answers) Answers {
	a.Product = strings.ToLower(strings.TrimSpace(a.Product))
	a.EuDocs = strings.ToLower(strings.TrimSpace(a.EuDocs))
	a.Medtech = strings.ToLower(strings.TrimSpace(a.Medtech))
	a.Sector = strings.ToLower(strings.TrimSpace(a.Sector))
	a.HouseFirst = strings.ToLower(strings.TrimSpace(a.HouseFirst))
	a.CeContext = strings.ToLower(strings.TrimSpace(a.CeContext))
	if a.CeContext == "" {
		a.CeContext = "none"
	}
	return a
}

// Suggest is a pure closed-world map: same enums → same proposed_packs.
// ce_context never changes packs. Never invents ids outside the frozen catalog.
func Suggest(a Answers) (SuggestResult, error) {
	a = normalizeAnswers(a)
	if err := ValidateAnswers(a); err != nil {
		return SuggestResult{}, err
	}

	out := SuggestResult{Answers: a}

	// Precedence: sector=other → house + write-your-own pointer;
	// else medtech → medtech-iec62304 (extends CRA);
	// else shipping + eu-docs → house + cra;
	// else house-policy (hygiene / house-first default).
	switch {
	case a.Sector == "other":
		out.ProposedPacks = []string{"house-policy"}
		out.NextHint = "write-your-own-pack"
	case a.Medtech == "yes":
		out.ProposedPacks = []string{"medtech-iec62304"}
	case a.Product == "shipping" && a.EuDocs == "yes":
		out.ProposedPacks = []string{"house-policy", "cra-baseline"}
	default:
		out.ProposedPacks = []string{"house-policy"}
	}

	// house-first is reserved: accepted for forward-compat, currently a no-op
	// (does not reorder proposed_packs). Help/docs must say so — honesty > fake feature.
	_ = a.HouseFirst
	// ce_context is context-only — never CE-positive packs.
	_ = a.CeContext

	out.ProposedPacks = uniqueStable(out.ProposedPacks)
	return out, nil
}

// IntersectKnown keeps only pack ids present in known (allowlist ∪ imported).
func IntersectKnown(proposed []string, known map[string]struct{}) []string {
	out := make([]string, 0, len(proposed))
	seen := map[string]struct{}{}
	for _, id := range proposed {
		id = strings.TrimSpace(id)
		if id == "" {
			continue
		}
		if _, ok := known[id]; !ok {
			continue
		}
		if _, dup := seen[id]; dup {
			continue
		}
		seen[id] = struct{}{}
		out = append(out, id)
	}
	return out
}

func uniqueStable(in []string) []string {
	seen := map[string]struct{}{}
	out := make([]string, 0, len(in))
	for _, id := range in {
		id = strings.TrimSpace(id)
		if id == "" {
			continue
		}
		if _, ok := seen[id]; ok {
			continue
		}
		seen[id] = struct{}{}
		out = append(out, id)
	}
	return out
}
