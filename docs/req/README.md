# Formal, verifiable requirements

`docs/agile/` contains **epics and user stories**: who wants to do what, why, and the acceptance scenarios in human language.

`docs/req/` contains **derived system requirements**: precise observable behavior, data preservation rules, constraints, failure handling, and links to the story that motivated each requirement. A requirement should be testable without guessing how the implementation works.

The intended trace is **Epic → Story → REQ → Test → Implementation**, not one automatically generated requirement per story. Never pretend a draft requirement is already implemented or tested. Use stable IDs and maintain links when refining.

- `pack-editor.md`: **draft** derivation from EP-01. Requires review against actual code and the authoritative Packs v2 specification before being declared the implementation baseline.
- `checks.md`: **draft** derivation from CHK-05. The maintainer accepted the decisions on 2026-10-23. Rows stay draft until their tests pass.
- Other subsystems: requirements not written yet; do not invent them from their folder names.

Formal requirements plus agreed architecture, external contracts and executable tests should make **observable application behavior reproducible** by another implementation team or agent. They cannot guarantee byte-identical code or identical internal design.

Pack Editor design decisions and intentionally unresolved questions are recorded in [`docs/agile/DECISIONS.md`](../agile/DECISIONS.md). They are background, **not independently approved system requirements**.
