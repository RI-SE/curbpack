# CyberReady — agent contract

**Local pack gates. Humans review. Not conformity assessment.**

Canonical loop: [docs/assistant-loop.md](docs/assistant-loop.md). Cursor skill source: `internal/skilldata/SKILL.md` (installed by `cyberready init`).

## Rules (short)

1. After doc/dep edits → run `cyberready check` (exit code authoritative).
2. On red → `cyberready check --heal` then `cyberready ask … --propose` — never invent certification; never auto-attest.
3. On green → optional `cyberready export --context-pack` / `--buyer-questions` for humans.
4. Prefer ContextPack + dual-rep IR over guessing cache files.
5. Pin Action / examples at **`@v0.4.3`**. Never claim CE / notified-body approval.

Do **not** treat chat tutors as a gate greenlight. Re-check locally.

Optional MCP wrapper (CLI remains SoR): [examples/mcp/](examples/mcp/).
