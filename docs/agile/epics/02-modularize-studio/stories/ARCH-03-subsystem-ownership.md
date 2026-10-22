# ARCH-03 - Subsystem ownership

**Status:** Draft; after pilot baseline.
**Epic:** [EP-02 Modularize Curbpack Studio](../EPIC.md)

**As a developer**, I want Requirements, Discovery, Claims, Checks, Compile and Review to own their operations and data handling, so that behavior has one implementation and can be reused by different clients.

**Accept when:**
- Each subsystem owns the Python functions for its domain behavior, validation and persistence.
- Page handlers delegate to these functions instead of recreating business rules, reading/writing domain files independently or running signing/checking logic in the UI.
- Subsystem dependencies are explicit; `common/` contains only genuinely shared utilities.
- Refactoring preserves existing behavior and the ownership boundaries established in the applicable architecture contracts.
