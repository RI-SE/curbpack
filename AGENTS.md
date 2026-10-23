# Instructions for coding agents

Curbpack Studio starts from the verified behavior of the **fresh PoC2 pilot**. The stories in `docs/agile/epics/01-pack-editor/` and derived requirements in `docs/req/pack-editor.md` describe desired changes; **they are not permission to implement them automatically**.

For an approved change:
1. Read the relevant epic/story (`docs/agile/`) and derived requirements (`docs/req/`). Do not guess at open decisions.
2. Check the relevant `docs/arch/` contract, `policies/` and existing implementation. Resolve contradictions instead of silently choosing an interpretation.
3. Use the authoritative **Packs v2** contract from the separate Curbpack repository (`../curbpack/docs/reference/packs2.md`) for persistent Pack, Requirement, Claim, signature and result data; do not invent fields.
4. After importing the pilot, read its existing architecture and active plans before altering affected code.
5. Check `git status`; preserve unrelated edits and signed/published data.

Implement one approved testable change at a time. Connect story → requirement → acceptance test. Run focused and relevant regression tests; report commands, actual results and remaining gaps. Avoid speculative layers, duplicated schemas or bulk refactoring. Do not mark unverified work complete. Do not push, publish, tag, rewrite history or perform destructive Git operations without permission.

Old CTAM and PoC1 are historical references only, not runtime dependencies or authorities for Packs v2.

## Working from a story

For any approved epic/story work (including resumptions), use the repo-local Cursor skill `.cursor/skills/story-workflow/SKILL.md` (`/story-workflow`). It defines the required sequence: derive and approve system requirements, use Plan Mode and save the step plan, write and execute a failing test first, implement and verify each small step, document the checkpoint, then commit locally. Do not push. The existing policies and authoritative Packs v2 contract still govern content; the skill governs execution.
