# Assistant loop (canonical contract)

**Local pack gates. Humans review. Not conformity assessment.**

One contract for Cursor, Copilot, Claude, Codex, Windsurf, Cline, Aider, Continue, and CI-only paths. Assistants **run `cyberready`**, then read ContextPack / IR — they never invent gate results or certification claims. There is **no** chat knowledge base over regulation text (by design).

Pin stays **`@v0.4.3`**. No pack unlock. Coreward is an optional external tutor pointer only — not part of activation.

## Canonical loop

```
doc/dep edits → cyberready check (exit code authoritative)
  ├─ red  → check --heal → ask … --propose → re-check
  └─ green → optional export --context-pack / --buyer-questions
             → prepare-release → human attest (never auto-attest)
```

Thin share recipe (same steps): `cyberready share` — see [buyer evidence](getting-started/buyer-evidence.md).

Warm-start: `cyberready pathway status` — optional interview that suggests checklists (see [pathway](getting-started/pathway.md)). Agents may `status` / `suggest` / `note` / `check` / `share` only. Human confirms and attest: TTY or `--i-am-human` (or `CYBERREADY_ALLOW_CONFIRM=1`) — never invent pack ids. Dual-draft when writing prose: Option A + Option B + **Recommended: A|B** → human pick → `research --cite-check` (refuses uncited Claims) → human `confirm-prose`. Prefer ContextPack `pathway` section over spelunking seed JSON. Illegal confirm order → usage exit 2. Seed is not a gate input. Research packet is informational only (never check pass/fail). Three ways in (Write / Bring / CI) all end in the same local `check`.

## Memory map (on-disk IR — not embeddings)

| Primitive | Path | Use |
|-----------|------|-----|
| GateFailure IR | `.github/cyberready/cache/latest_failure.json` | Authoritative findings; `statechart_context.active_parent_state_path` = pathway phase when seed exists |
| instrument.json | same cache dir | Δ deps / secret-hits whisper |
| remediations.json | same | Reuse gate_id hints |
| **ContextPack** | `.github/cyberready/cache/context-pack.json` (+ `.md`) | One washed assistant artifact (+ pathway next) |
| **pathway-seed.json** | same cache dir | Warm-start enums + HITL ticks + session_notes/corrections/last_draft_pick (CLI-only writer; not a gate input) |
| **research-packet.json** | same cache dir | Allowlisted citation trail + requirements (not a gate input) |
| **research-brief.md** | same cache dir | One-screen human brief |
| RKG | `.github/cyberready/graph/policy-graph.json` | Pack→rule navigation (exported on `confirm-packs`) |
| buyer-questions / lay-of-land | export outputs | Human share |
| HPURL pointer | `.github/cyberready/evidence/hpurl-pointer.json` | Post-attest client-side verify via `proof/index.html` |
| hooks + Action | `init` / `@v0.4.3` | Force re-check loop |

```bash
cyberready export --context-pack
# → .github/cyberready/cache/context-pack.json (+ .md)
```

## Pack chooser (cold start)

Prefer `cyberready pathway status` / `pathway suggest` for enum-driven warm start — see [pathway](getting-started/pathway.md). Manual override:

| Situation | Pack |
|-----------|------|
| Default / unknown product | **`house-policy`** (`cyberready init`) |
| CRA-style annex drafts (opt-in) | `cra-baseline` via `--packs` |
| Medtech IEC 62304-style (opt-in) | `medtech-iec62304` via `--packs` |

Catalog is frozen to those three ids until freeze review. See [Intent vs Scope](intent-vs-scope.md). Auditors: [for-authorities](for-authorities.md).

## Use with Cursor / Copilot / Claude / others

| System | Adoption artifact | How to enable |
|--------|-------------------|---------------|
| **Cursor** | Skill via `cyberready init` → `.cursor/skills/cyberready/SKILL.md` | `init` (already); then ContextPack |
| **GitHub Copilot** | [`.github/copilot-instructions.md`](../.github/copilot-instructions.md) | Auto-picked in this repo; copy into adopters if useful |
| **Claude Code / Claude in IDE** | Root [`CLAUDE.md`](../CLAUDE.md) | Drop-in; link this doc |
| **Generic agents** (Codex, Windsurf, Cline, Aider, Continue, …) | Root [`AGENTS.md`](../AGENTS.md) | De-facto agent readme |
| **Claude Desktop / Cursor MCP / VS Code MCP** | Thin MCP [examples/mcp/](../examples/mcp/) | Tools call CLI; CLI remains SoR |
| **ChatGPT / web Claude / Gemini** (no repo tools) | Paste `context-pack.md` or explain-packet only | Human must re-run `check` locally — no false “fixed” |
| **CI-only** | Action `@v0.4.3` + SARIF (+ ContextPack artifact when available) | Primary PR path |

**Init hygiene:** `cyberready init` does **not** auto-write `AGENTS.md` / `CLAUDE.md` / `copilot-instructions.md` into every product repo (avoids clutter). Cursor gets the skill; other tools read those files when present — adopters may copy them once from this repo.

## Web-chat paste path

1. Locally: `cyberready check` then `cyberready export --context-pack`.
2. Paste `.github/cyberready/cache/context-pack.md` (or washed explain-packet) into the chat.
3. Treat chat output as proposals only. Re-run `cyberready check` before any “fixed” claim.

## Why no chat KB / RAG

Regulation prose and raw source stay off the default tutor path. Dual-rep IR + ContextPack are the memory. Chat never greenlights gates.

## Related

- [60-second paths](getting-started/60-second-paths.md) · [Buyer evidence](getting-started/buyer-evidence.md) · [Pathway](getting-started/pathway.md) · [Daily loop](getting-started/daily-loop.md)
- [Stable contracts](stable-contracts.md) · [For authorities](for-authorities.md) · [Intent vs Scope](intent-vs-scope.md)
