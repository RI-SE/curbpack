# Curbpack — Claude Code

**Local pack gates. Humans review. Not conformity assessment.**

Same contract as [AGENTS.md](AGENTS.md). Full platform matrix + memory map: [docs/assistant-loop.md](docs/assistant-loop.md). Warm-start: [docs/getting-started/pathway.md](docs/getting-started/pathway.md).

## Loop

```bash
curbpack pathway status   # human next ask by default (--technical for phase path)
curbpack check
# red: curbpack check --heal && curbpack ask .github/curbpack/cache/latest_failure.json --propose
# optional research sidecar (never gates check): curbpack research [--fetch] [--gate-id=…]
# dual-draft: Option A + Option B + Recommended A|B (≤3 reasons) → human pick →
#   curbpack pathway note --set last_draft_pick=A|B|edited
# before confirm-prose: curbpack research --cite-check <draft.md> (confirm-prose also ground-checks; every prose path must be independent)
# green (optional share): curbpack export --context-pack
# human only: pathway confirm-* / attest / proof verify — never auto-attest; never invent pack ids
```

Exit code is authoritative. Never claim certification. Pin **`@v0.5.2`**. Cite-or-refuse: do not invent regulation text; link allowlisted sources only.

Thin MCP (optional): [examples/mcp/](examples/mcp/) — propose-only; no confirm/attest tools.
