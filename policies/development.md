## Architecture protection

All `ARCHITECTURE.md` files within `poc2/` are authoritative, read-only specifications during implementation.

Implementation agents MUST NOT create, modify, rename, move, or delete these files unless explicitly instructed by the user to perform an architecture-editing task.

If an implementation plan, source code, or another architecture document conflicts with the applicable architecture:

1. Stop the affected implementation task.
2. Report the exact conflict, including affected files and sections.
3. Record the blocker and next action in the active implementation plan.
4. Await an explicit decision.

Do not resolve architectural contradictions by editing specifications, changing their meaning, or silently choosing one interpretation.

Permission to implement a plan does not grant permission to modify architecture documents.
