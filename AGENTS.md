# Curbpack — agent contract

**Local pack gates. Humans review. Not conformity assessment.**

Canonical loop: [docs/assistant-loop.md](docs/assistant-loop.md). Warm-start pathway: [docs/getting-started/pathway.md](docs/getting-started/pathway.md). Cursor skill source: `internal/skilldata/SKILL.md` (installed by `curbpack init`).

## Rules (short)

1. After doc/dep edits → run `curbpack check` (exit code authoritative).
2. On red → `curbpack check --heal` then `curbpack ask … --propose` — never invent certification; never auto-attest.
3. On green → optional `curbpack export --context-pack` / `--buyer-questions` for humans.
4. Prefer ContextPack + dual-rep IR over guessing cache files.
5. Pin Action / examples at **`@v0.5.2`**. Never claim CE / notified-body approval.
6. **Pathway:** call `curbpack pathway status|suggest|note` only — never forge `pathway-seed.json` or invent pack ids. Stop for human `confirm-*` and `attest`. Prefer ContextPack pathway next + RKG after confirm-packs; post-attest next is local proof verify (human). MCP never confirms/attests. Seed is not a gate input.
7. **Research (optional sidecar):** `curbpack research` builds allowlisted citation packet + human brief — **never** inputs to check pass/fail. After confirm-packs / before prose: draft from packet; every factual assertion needs a repo artifact (path, config, test name, commit, metric, claim id) or an allowlisted cite (`[^src-N]` / `<!-- cite:src-N -->` / allowlisted URL). Heal stubs are not grounding. `confirm-prose` is AND: every displayed prose path must be independent (mixed stub+real still refuses). Run `curbpack research --cite-check <draft.md>` before asking a human for `confirm-prose` (confirm-prose also refuse-ungrounded). On red, optional `research --gate-id=<id>`. Link-only if no `--fetch`.
8. **Dual-draft HITL:** always propose Option A and Option B, state **Recommended: A|B** with ≤3 reasons (from seed notes / last_pick / requirements), stop for human pick; then cite-check; record via `curbpack pathway note --set last_draft_pick=A|B|edited`.
9. **Dual remotes:** phrases “sync both” / “sync curbpack remotes” → run `./scripts/curb-sync.sh` only (never force-push).

Do **not** treat chat tutors as a gate greenlight. Re-check locally.

Optional MCP wrapper (CLI remains SoR): [examples/mcp/](examples/mcp/).
