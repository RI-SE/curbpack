package research

import (
	"fmt"
	"path/filepath"
	"strings"
)

// FormatBrief renders a one-screen human markdown brief from the packet.
// Top: packs + ≤5 files to edit + Sources. Full pack rules below. No graph digest.
func FormatBrief(pkt Packet) string {
	var b strings.Builder
	b.WriteString("# Research brief (human)\n\n")
	b.WriteString("> Informational sources for drafting — not conformity assessment; not a gate input.\n\n")
	fmt.Fprintf(&b, "**Packs:** %s\n\n", strings.Join(pkt.PackIDs, ", "))

	b.WriteString("## What to do next\n\n")
	b.WriteString("1. Open the official links below (allowlisted only).\n")
	b.WriteString("2. Edit the top files listed here (structural headers/paths).\n")
	b.WriteString("3. Tag every external factual claim with a source id (`[^src-1]` or `<!-- cite:src-1 -->`).\n")
	b.WriteString("4. Run `curbpack research --cite-check <draft.md>` before human `pathway confirm-prose`.\n")
	b.WriteString("5. Re-run `curbpack check` — research never changes pass/fail.\n\n")

	files := topEditFiles(pkt, 5)
	b.WriteString("## Files to edit (top 5)\n\n")
	if len(files) == 0 {
		b.WriteString("_No path targets in composed pack rules._\n\n")
	} else {
		for _, f := range files {
			fmt.Fprintf(&b, "- `%s`\n", f)
		}
		b.WriteString("\n")
	}

	b.WriteString("## Sources (allowlisted)\n\n")
	if len(pkt.Sources) == 0 {
		b.WriteString("_No citation URLs on active packs. Link-only drafting still uses pack rule headers locally._\n\n")
	} else {
		for _, s := range pkt.Sources {
			label := s.Instrument
			if label == "" {
				label = s.Framework
			}
			if label == "" {
				label = s.ID
			}
			fmt.Fprintf(&b, "- **%s** (`%s`): %s\n", s.ID, label, s.URL)
			if s.FetchError != "" {
				fmt.Fprintf(&b, "  - fetch: error — %s (fail-open; use link only)\n", s.FetchError)
			} else if s.Excerpt != "" {
				fmt.Fprintf(&b, "  - excerpt: %s\n", truncate(s.Excerpt, 240))
			}
		}
		b.WriteString("\n")
	}

	b.WriteString("## All pack rules\n\n")
	if len(pkt.Requirements) == 0 {
		b.WriteString("_No rules in composed packs._\n\n")
	} else {
		for _, r := range pkt.Requirements {
			fmt.Fprintf(&b, "### `%s`\n\n", r.GateID)
			if r.Path != "" {
				fmt.Fprintf(&b, "- **Path:** `%s`\n", r.Path)
			}
			if len(r.RequireHeaders) > 0 {
				fmt.Fprintf(&b, "- **Headers:** %s\n", strings.Join(quoteAll(r.RequireHeaders), ", "))
			}
			if r.Remediation != "" {
				fmt.Fprintf(&b, "- **Remediation:** %s\n", r.Remediation)
			}
			b.WriteString("\n")
		}
	}

	fmt.Fprintf(&b, "---\n\n_%s_\n", ClaimFence)
	return b.String()
}

func topEditFiles(pkt Packet, n int) []string {
	seen := map[string]struct{}{}
	var out []string
	for _, r := range pkt.Requirements {
		for _, part := range strings.Split(r.Path, ",") {
			p := filepath.ToSlash(strings.TrimSpace(part))
			if p == "" {
				continue
			}
			if _, ok := seen[p]; ok {
				continue
			}
			seen[p] = struct{}{}
			out = append(out, p)
			if len(out) >= n {
				return out
			}
		}
	}
	return out
}

func quoteAll(ss []string) []string {
	out := make([]string, len(ss))
	for i, s := range ss {
		out[i] = "`" + s + "`"
	}
	return out
}

func truncate(s string, n int) string {
	s = strings.TrimSpace(s)
	if n <= 0 || len(s) <= n {
		return s
	}
	return s[:n] + "…"
}

// FormatSourcesList prints allowlisted sources for humans/agents.
func FormatSourcesList(pkt Packet) string {
	var b strings.Builder
	if len(pkt.Sources) == 0 {
		return "No allowlisted sources in research packet.\n"
	}
	for _, s := range pkt.Sources {
		fmt.Fprintf(&b, "%s\t%s\n", s.ID, s.URL)
	}
	return b.String()
}
