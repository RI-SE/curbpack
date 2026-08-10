# CyberReady — agent contract

**Local pack gates. Humans review. Not conformity assessment.**

Canonical loop: [docs/assistant-loop.md](docs/assistant-loop.md). Warm-start pathway: [docs/getting-started/pathway.md](docs/getting-started/pathway.md). Cursor skill source: `internal/skilldata/SKILL.md` (installed by `cyberready init`).

## Rules (short)

1. After doc/dep edits → run `cyberready check` (exit code authoritative).
2. On red → `cyberready check --heal` then `cyberready ask … --propose` — never invent certification; never auto-attest.
3. On green → optional `cyberready export --context-pack` / `--buyer-questions` for humans.
4. Prefer ContextPack + dual-rep IR over guessing cache files.
5. Pin Action / examples at **`@v0.4.3`**. Never claim CE / notified-body approval.
6. **Pathway:** call `cyberready pathway status|suggest|note` only — never forge `pathway-seed.json` or invent pack ids. Stop for human `confirm-*` and `attest`. Prefer ContextPack pathway next + RKG after confirm-packs; post-attest next is local proof verify (human). MCP never confirms/attests. Seed is not a gate input.
7. **Research (optional sidecar):** `cyberready research` builds allowlisted citation packet + human brief — **never** inputs to check pass/fail. After confirm-packs / before prose: draft from packet; every external claim needs a cite id (`[^src-N]` / `<!-- cite:src-N -->`); refuse uncited Claims. Run `cyberready research --cite-check <draft.md>` before asking a human for `confirm-prose`. On red, optional `research --gate-id=<id>`. Link-only if no `--fetch`.
8. **Dual-draft HITL:** always propose Option A and Option B, state **Recommended: A|B** with ≤3 reasons (from seed notes / last_pick / requirements), stop for human pick; then cite-check; record via `cyberready pathway note --set last_draft_pick=A|B|edited`.

Do **not** treat chat tutors as a gate greenlight. Re-check locally.

Optional MCP wrapper (CLI remains SoR): [examples/mcp/](examples/mcp/).
