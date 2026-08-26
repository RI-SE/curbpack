# Curbpack — Claude Code

**Local pack gates. Humans review. Not conformity assessment.**

Same contract as [AGENTS.md](AGENTS.md). Design intent: [docs/software-design-document.md](docs/software-design-document.md). Full platform matrix + memory map: [docs/assistant-loop.md](docs/assistant-loop.md). Warm-start: [docs/getting-started/pathway.md](docs/getting-started/pathway.md).

## Loop (opens read-only)

```bash
curbpack scan              # read-only first — no init, no hooks, no score
# optional: curbpack fix --<gap>   # one file; diff shown; human confirm
curbpack init              # when ready — house-policy default
curbpack check
# red: curbpack check --heal && curbpack ask .github/curbpack/cache/latest_failure.json --propose
# green: curbpack ask-my-suppliers
# optional pathway: curbpack pathway status   # human next ask (--technical for phase path)
# optional research sidecar (never gates check): curbpack research [--fetch] [--gate-id=…]
# dual-draft: Option A + Option B + Recommended A|B (≤3 reasons) → human pick →
#   curbpack pathway note --set last_draft_pick=A|B|edited
# before confirm-prose: curbpack research --cite-check <draft.md>
# green (optional share): curbpack export --context-pack
# reviewers (offline): curbpack review <received-pack>  # document triage — not confirm/attest
# optional in-repo: curbpack review --repo [path] [--packs a,b]  # ProsePaths; cold default house-policy
```

## Human-only acts

```
trust-import · review-sign · Last tabletop: · confirm-* · attest · pin-bump
```

Gate: `--i-am-human` or `CURBPACK_ALLOW_CONFIRM=1` for confirms; TTY alone is not enough. Never auto-attest; never invent pack ids; never bump pin without human approval.

Exit code is authoritative. Never claim certification. Pin **`@v0.5.2`**. Cite-or-refuse: do not invent regulation text; link allowlisted sources only.

Claim discipline: [docs/claim-discipline.md](docs/claim-discipline.md) — never assert what the tool caused.

**Repository policy:** RI-SE/curbpack is the public SoR. Never parity/mirror PRs; never copy private-fork docs to RI-SE; afelin is downstream catch-up only. [docs/internal/fork-policy.md](docs/internal/fork-policy.md).

Thin MCP (optional): [examples/mcp/](examples/mcp/) — propose-only; no confirm/attest tools.
