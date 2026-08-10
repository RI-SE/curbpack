package research

import (
	"fmt"
	"strings"
)

// FormatBrief renders a one-screen human markdown brief from the packet.
func FormatBrief(pkt Packet) string {
	var b strings.Builder
	b.WriteString("# Research brief (human)\n\n")
	b.WriteString("> Informational sources for drafting — not conformity assessment; not a gate input.\n\n")
	fmt.Fprintf(&b, "**Packs:** %s\n\n", strings.Join(pkt.PackIDs, ", "))
	if pkt.GraphDigest != "" {
		fmt.Fprintf(&b, "**Graph digest:** `%s`\n\n", truncate(pkt.GraphDigest, 16))
	}
	b.WriteString("## What to do next\n\n")
	b.WriteString("1. Open the official links below (allowlisted only).\n")
	b.WriteString("2. Draft house docs that satisfy the structural requirements (headers/paths).\n")
	b.WriteString("3. Tag every external factual claim with a source id (`[^src-1]` or `<!-- cite:src-1 -->`).\n")
	b.WriteString("4. Run `cyberready research --cite-check <draft.md>` before human `pathway confirm-prose`.\n")
	b.WriteString("5. Re-run `cyberready check` — research never changes pass/fail.\n\n")

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

	b.WriteString("## Structural requirements (local truth)\n\n")
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
