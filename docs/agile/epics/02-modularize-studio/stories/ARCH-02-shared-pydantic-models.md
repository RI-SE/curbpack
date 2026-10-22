# ARCH-02 - Shared Pydantic contracts

**Status:** Draft; after pilot baseline.
**Epic:** [EP-02 Modularize Curbpack Studio](../EPIC.md)

**As a developer**, I want Pydantic contracts shared by `app/` and the subsystems to live in `models/`, so that callers validate and exchange the same data.

**Accept when:**
- Models genuinely shared by app and subsystems are defined once in `models/` and used from both places.
- Models used only within one subsystem may remain local to that subsystem; no needless centralization.
- Shared models respect the authoritative Packs v2 structures and validation semantics; no competing persisted schema is introduced.
- Existing external data formats and relevant validation tests continue to pass.
