# PoC2 Working Rules

The goal is code a human engineer can read and safely change six months later. Favor clarity over rapid generation, cleverness, compactness or theoretical extensibility.

1. **Follow the target subsystem architecture.** All new PoC2 development must follow the target structure and ownership in `docs/arch/ARCHITECTURE.md`. Deviations require an explicit architectural decision. Current physical paths remain valid until migration; do not change behaviour merely to match the layout.
2. **Read before editing.** Understand the affected implementation, relevant architecture, existing behavior, and applicable Packs v2 contract before changing code.
3. **One concern per function.** Prefer small named functions, ordinary Python data structures, explicit parameters and unsurprising control flow. Avoid giant orchestrators and accidental cross-component imports.
4. **UI is only UI.** No domain logic, file scanning, validation rules or data-format transformations in HTML handlers, pages, callbacks or event code. Use named use-case functions and test them independently.
5. **The model is not the UI.** Persist Packs v2 data, not widget state. Temporary display/view data can be computed, never treated as authoritative.
6. **No speculative abstractions.** No framework, event bus, generic plugin engine, service/repository/factory hierarchy, compatibility adapter or interface without at least two actual consumers and a demonstrated need.
7. **No duplicated truth.** One implementation of each validation and serialization rule. Avoid restating the same fact in different fields or formats. Do not reintroduce legacy `search` or `claim` fields inside Requirements.
8. **No silent behavior.** Fail with a useful error on an unknown check type, invalid arguments, or missing input. The PoC file search does not read `source` or `args`. Do not add an error contract for source types it does not implement yet.
9. **Name things by their purpose.** Prefer `load_requirement`, `save_requirement`, `discover_candidates` and `run_claim` to `handle`, `process_data`, `manager2` or framework vocabulary.
10. **Comments explain why.** Type hints and short docstrings at non-obvious boundaries; do not comment every line or auto-generate prose that restates code.
11. **Design for testability.** Keep domain behavior independently testable and external services behind deliberate boundaries rather than embedding them in business logic. Verification requirements are defined by the Testing Policy.
12. **Keep the old PoC pristine.** Use `poc/` as a behavior reference, not as a runtime dependency. Do not modify, import from or read its mutable data at runtime in `poc2/`.
13. **Keep changes reviewable.** Prefer small, coherent changes. Before editing, inspect status and preserve unrelated working-tree changes. Commit and remote-operation rules are defined by `/story-workflow` and `AGENTS.md`.
14. **Do not rely on agent memory.** Decisions and implementation state another engineer needs must live in the repository's designated story, plan, documentation, tests, or code rather than only in chat or temporary agent context.

## Component engineering criteria

A changed component must:

- operate on the applicable Packs v2 shapes;
- preserve relevant existing user-visible behavior unless the approved story changes it;
- keep business rules outside UI code;
- remain independently testable under the Testing Policy;
- not depend on `poc/` at runtime;
- remain understandable without reverse-engineering unnecessary framework layers.

These criteria do not by themselves make a story DONE. Story completion is governed by `/story-workflow` and the Testing Policy.
