package review

import (
	"fmt"
	"sort"
	"strings"
)

// Delta is a Finding.ID-keyed differ between two review reports.
type Delta struct {
	New        []string // unresolved now; absent or confirmed before
	Cleared    []string // unresolved before; absent or confirmed now
	Persisting []string // unresolved in both
}

func isUnresolved(f Finding) bool {
	return f.State == StateUnconfirmed || f.State == StateContradicted
}

func findingByID(rep Report) map[string]Finding {
	out := make(map[string]Finding, len(rep.Findings))
	for _, f := range rep.Findings {
		out[f.ID] = f
	}
	return out
}

// ComputeDelta compares prior and current reports by Finding.ID.
func ComputeDelta(prior, current Report) Delta {
	pMap := findingByID(prior)
	cMap := findingByID(current)
	var d Delta

	for id, cf := range cMap {
		if !isUnresolved(cf) {
			continue
		}
		pf, ok := pMap[id]
		if !ok || pf.State == StateConfirmed {
			d.New = append(d.New, id)
			continue
		}
		if isUnresolved(pf) {
			d.Persisting = append(d.Persisting, id)
		}
	}
	for id, pf := range pMap {
		if !isUnresolved(pf) {
			continue
		}
		cf, ok := cMap[id]
		if !ok || cf.State == StateConfirmed {
			d.Cleared = append(d.Cleared, id)
		}
	}
	sort.Strings(d.New)
	sort.Strings(d.Cleared)
	sort.Strings(d.Persisting)
	return d
}

// FormatDelta returns the terse delta block for markdown output.
func FormatDelta(prior, current Report) string {
	d := ComputeDelta(prior, current)
	short := prior.RecordDigest
	if len(short) > 8 {
		short = short[:8]
	}
	if short == "" {
		short = "unknown"
	}
	var b strings.Builder
	fmt.Fprintf(&b, "\ndelta since record %s…\n", short)
	if prior.MethodVersion != "" && current.MethodVersion != "" && prior.MethodVersion != current.MethodVersion {
		fmt.Fprintf(&b, "method_version differs: prior %s · current %s — findings may not be comparable\n",
			prior.MethodVersion, current.MethodVersion)
	}
	fmt.Fprintf(&b, "\n")
	fmt.Fprintf(&b, "  NEW          %3d   confirmed before, not now\n", len(d.New))
	fmt.Fprintf(&b, "  CLEARED      %3d   present before, absent now\n", len(d.Cleared))
	fmt.Fprintf(&b, "  PERSISTING   %3d   unresolved in both\n", len(d.Persisting))
	return b.String()
}
