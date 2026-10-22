# CHK-05 – Implement remaining registered Checks

**Epic:** EP-01 – Complete Functional Pilot

**As a user**, I want all registered Check types to be executable so that I can verify Claims using the available checks, not just `exist` and `contents`.

## Scope

Implement the three registered Check types:

- `fresh` – verify evidence freshness.
- `owned` – verify evidence ownership.
- `dep_ban` – detect prohibited dependencies.

Use the existing Check catalog, argument schemas and Packs v2 results.

## Acceptance criteria

1. All three Checks can be selected, configured and executed.
2. Arguments are validated against each Check's declared schema.
3. Each Check produces a deterministic PASS, FAIL or SKIP with a clear reason.
4. Missing evidence, invalid arguments and unsupported inputs must never produce a false PASS.
5. Results identify the relevant Claim, Check and checked evidence.
6. Multiple Checks attached to one Claim execute correctly.
7. Existing `exist` and `contents` behavior remains unchanged.
8. Unit tests cover successful, failing and invalid-input cases for each Check.
9. An end-to-end test demonstrates all three Checks through Check → Compile → Review.

## Before implementation

Verify that the existing catalog defines unambiguous semantics for each Check.

In particular, determine what establishes freshness, where ownership information comes from, and which dependency data sources `dep_ban` supports.

If these are not defined, document the missing contract before implementing behavior. Do not invent new Packs v2 fields.

## Out of scope

No new Check framework, data model, GUI redesign or changes to unrelated subsystems.
