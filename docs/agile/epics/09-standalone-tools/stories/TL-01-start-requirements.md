# TL-01 — Start Requirements alone

**Status:** Draft. Not authorization to implement.
**Epic:** [EP-09 Start each Packs v2 tool on its own](../EPIC.md)

**As a legal expert**, I want to start Requirements by itself, so that I can extract, import, review, edit, and seal Requirements without opening Claims, Check, or the pilot.

**Accept when:**

- One command starts Requirements and shows its catalog, extract, edit, and sign pages.
- The same operations run from that command without a browser.
- The process does not import `pilot_app`, claims, checks, compile, review, or scaffold.
- It reads and writes Packs v2 Requirements and `pack.json` through `common/`. A Requirement file the expert does not edit keeps its bytes, including `signed`.
- Discover, Check, Compile, and Review are not pages of this process. Extract stays inside it.
