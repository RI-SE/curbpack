# Instructions for coding agents

Curbpack Studio starts from the verified behavior of the **fresh PoC2 pilot**. The stories in `docs/agile/epics/01-pack-editor/` and derived requirements in `docs/req/pack-editor.md` describe desired changes; **they are not permission to implement them automatically**.

For an approved change:
1. Read the relevant epic/story (`docs/agile/`) and derived requirements (`docs/req/`). Do not guess at open decisions.
2. Check `doc/ARCHITECTURE.md`, the applicable subsystem `ARCHITECTURE.md`, `policies/` and existing implementation. Resolve contradictions instead of silently choosing an interpretation.
3. Use the authoritative **Packs v2** contract at `docs/reference/packs2.md` in this repository for persistent Pack, Requirement, Claim, signature and result data; do not invent fields.
4. After importing the pilot, read its existing architecture and active plans before altering affected code.
5. Check `git status`; preserve unrelated edits and signed/published data.

Implement one approved testable change at a time. Connect story → requirement → acceptance test. Run focused and relevant regression tests; report commands, actual results and remaining gaps. Avoid speculative layers, duplicated schemas or bulk refactoring. Do not mark unverified work complete. Do not push, publish, tag, rewrite history or perform destructive Git operations without permission.

Old CTAM and PoC1 are historical references only, not runtime dependencies or authorities for Packs v2.

## Working from a story

For any approved epic/story work (including resumptions), follow `.cursor/skills/story-workflow/SKILL.md` (`/story-workflow`). Policies and the authoritative Packs v2 contract govern content; the skill governs execution.
