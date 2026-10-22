# PoC2 Working Rules

The goal is code a human engineer can read and safely change six months later. Favor clarity over rapid generation, cleverness, compactness or theoretical extensibility.

1. **Follow the target subsystem architecture.** All new PoC2 development must follow the target structure and ownership in `doc/ARCHITECTURE.md`. Deviations require an explicit architectural decision. Current physical paths remain valid until migration; do not change behaviour merely to match the layout.
2. **Read before editing.** Inspect the relevant old PoC behavior and the applicable `packs2.md` fields. State the input, output and acceptance check for the next small change.
3. **One concern per function.** Prefer small named functions, ordinary Python data structures, explicit parameters and unsurprising control flow. Avoid giant orchestrators and accidental cross-component imports.
4. **UI is only UI.** No domain logic, file scanning, validation rules or data-format transformations in HTML handlers, pages, callbacks or event code. Use named use-case functions and test them independently.
5. **The model is not the UI.** Persist Packs v2 data, not widget state. Temporary display/view data can be computed, never treated as authoritative.
6. **No speculative abstractions.** No framework, event bus, generic plugin engine, service/repository/factory hierarchy, compatibility adapter or interface without at least two actual consumers and a demonstrated need.
7. **No duplicated truth.** One implementation of each validation and serialization rule. Avoid restating the same fact in different fields or formats. Do not reintroduce legacy `search` or `claim` fields inside Requirements.
8. **No silent behavior.** Fail with a useful error on an unknown check type, invalid arguments, or missing input. The PoC file search does not read `source` or `args`. Do not add an error contract for source types it does not implement yet.
9. **Name things by their purpose.** Prefer `load_requirement`, `save_requirement`, `discover_candidates` and `run_claim` to `handle`, `process_data`, `manager2` or framework vocabulary.
10. **Comments explain why.** Type hints and short docstrings at non-obvious boundaries; do not comment every line or auto-generate prose that restates code.
11. **Tests prove behavior.** Small deterministic tests for transformations and round trips; one honest, non-mocked integration path at each milestone. Mock external services only at deliberate boundaries.
12. **Keep the old PoC pristine.** Use `poc/` as a behavior reference, not as a runtime dependency. Do not modify, import from or read its mutable data at runtime in `poc2/`.
13. **Keep commits reviewable.** Commit verified, coherent increments locally. Before editing, inspect status and do not include unrelated work. No push, PR, release, remote mutation or destructive Git operations without approval.
14. **Bound agent context.** At the end of each stage, write a short record of what works, tests run, unresolved issues and next action. Start a new context from that record when necessary; do not invent a complex agent coordination system.

## Minimal definition of done for one component

- The main operation works with Packs v2 shapes.
- The user-visible behavior is retained where relevant.
- No business rules have leaked into UI code.
- Tests cover both success and failure; a real example was run.
- The component does not depend on `poc/` at runtime.
- Source files are readable without needing to reverse-engineer a framework.
