# CyberReady — Claude Code

**Local pack gates. Humans review. Not conformity assessment.**

Same contract as [AGENTS.md](AGENTS.md). Full platform matrix + memory map: [docs/assistant-loop.md](docs/assistant-loop.md). Warm-start: [docs/getting-started/pathway.md](docs/getting-started/pathway.md).

## Loop

```bash
cyberready pathway status   # human next ask by default (--technical for phase path)
cyberready check
# red: cyberready check --heal && cyberready ask .github/cyberready/cache/latest_failure.json --propose
# optional research sidecar (never gates check): cyberready research [--fetch] [--gate-id=…]
# dual-draft: Option A + Option B + Recommended A|B (≤3 reasons) → human pick →
#   cyberready pathway note --set last_draft_pick=A|B|edited
# before confirm-prose: cyberready research --cite-check <draft.md>
# green (optional share): cyberready export --context-pack
# human only: pathway confirm-* / attest / proof verify — never auto-attest; never invent pack ids
```

Exit code is authoritative. Never claim certification. Pin **`@v0.4.3`**. Cite-or-refuse: do not invent regulation text; link allowlisted sources only.

Thin MCP (optional): [examples/mcp/](examples/mcp/) — propose-only; no confirm/attest tools.
