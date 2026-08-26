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
	fmt.Fprintf(&b, "\ndelta since record %s…", short)
	if current.MethodVersion != "" {
		fmt.Fprintf(&b, "   method %s", current.MethodVersion)
	}
	b.WriteByte('\n')
	if prior.MethodVersion != "" && current.MethodVersion != "" && prior.MethodVersion != current.MethodVersion {
		fmt.Fprintf(&b, "method_version differs: prior %s · current %s — findings may not be comparable\n",
			prior.MethodVersion, current.MethodVersion)
	}
	fmt.Fprintf(&b, "\n")
	fmt.Fprintf(&b, "  NEW          %3d   confirmed before, not now\n", len(d.New))
	fmt.Fprintf(&b, "  CLEARED      %3d   present before, absent now\n", len(d.Cleared))
	fmt.Fprintf(&b, "  PERSISTING   %3d   unresolved in both\n", len(d.Persisting))

	groups := GroupUnresolvedBySource(prior, current)
	if len(groups) > 0 {
		b.WriteByte('\n')
		for _, g := range groups {
			arrow := ""
			switch {
			case g.Current > g.Prior:
				arrow = "   ↑"
			case g.Current < g.Prior:
				arrow = "   ↓"
			}
			fmt.Fprintf(&b, "  %-40s %d unresolved   (was %d)%s\n", g.Source, g.Current, g.Prior, arrow)
		}
	}
	return b.String()
}

// SourceDecay is per-document unresolved counts for delta grouping.
type SourceDecay struct {
	Source  string
	Prior   int
	Current int
}

// GroupUnresolvedBySource tallies unresolved findings by Source for human action.
// Sort: descending current unresolved, then path. Empty Source buckets as "(no source)".
func GroupUnresolvedBySource(prior, current Report) []SourceDecay {
	type pair struct{ prior, current int }
	m := map[string]*pair{}
	touch := func(src string, which string) {
		src = strings.TrimSpace(src)
		if src == "" {
			src = "(no source)"
		}
		p := m[src]
		if p == nil {
			p = &pair{}
			m[src] = p
		}
		if which == "prior" {
			p.prior++
		} else {
			p.current++
		}
	}
	for _, f := range prior.Findings {
		if isUnresolved(f) {
			touch(f.Source, "prior")
		}
	}
	for _, f := range current.Findings {
		if isUnresolved(f) {
			touch(f.Source, "current")
		}
	}
	out := make([]SourceDecay, 0, len(m))
	for src, p := range m {
		out = append(out, SourceDecay{Source: src, Prior: p.prior, Current: p.current})
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].Current != out[j].Current {
			return out[i].Current > out[j].Current
		}
		return out[i].Source < out[j].Source
	})
	return out
}
