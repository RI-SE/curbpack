# Instructions for coding agents

Stories and epics describe desired behavior. They are not permission to implement it.

## Story work

For all planning, implementation, testing, review, or resumption of approved story work, follow `.cursor/skills/story-workflow/SKILL.md` (`/story-workflow`).

1. Read the epic/story in `docs/agile/` and the requirements defined in the story. Older stories may instead have derived requirements in `docs/req/`.
2. Acceptance behavior for new stories is defined in the story using Given/When/Then, examples, or an equivalent semi-executable form. Do not create duplicate derived requirements when the story already defines the required behavior.
3. The canonical live plan is `plan/<STORY-ID>.md`. When the story is verified DONE, it moves to `impl/<STORY-ID>.md`. Do not resume implementation from a file in `impl/`.
4. Acceptance tests are derived directly from the story and must remain readable by a human as executable specifications. Do not invent behavior for unresolved decisions.

## Authority and constraints

Before changing affected code, inspect the applicable:

- epic/story in `docs/agile/`;
- legacy derived requirements in `docs/req/`, when applicable;
- `docs/arch/ARCHITECTURE.md`;
- `docs/arch/SYSTEM_REQUIREMENTS.md`;
- subsystem `ARCHITECTURE.md`;
- `policies/`, including the testing, architecture, and working rules;
- existing implementation and tests.

For persistent Pack, Requirement, Claim, signature, and result data, `docs/reference/packs2.md` is authoritative. Do not invent fields or duplicate the persistent schema.

Resolve contradictions through the story workflow rather than silently choosing an interpretation.

## Change discipline

Implement only approved story scope, one verified step at a time. Preserve unrelated working-tree changes, existing behavior outside the approved change, and signed or published data.

Avoid speculative abstractions, duplicated schemas, unrelated refactoring, or architecture changes outside the approved scope. Do not weaken tests merely to make them pass.

## Git and external actions

Local commits made according to `/story-workflow` are allowed.

Do not push, publish, create releases or tags, modify remotes, rewrite history, perform destructive Git operations, or upload confidential material without explicit permission.
