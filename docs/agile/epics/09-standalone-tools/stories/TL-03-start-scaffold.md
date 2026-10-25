# TL-03 — Start curbpack-scaffold alone

**Status:** Draft. Not authorization to implement.
**Epic:** [EP-09 Start each Packs v2 tool on its own](../EPIC.md)

**As a developer**, I want to start curbpack-scaffold by itself, so that I can write a stub for a missing path without opening the pilot.

**Accept when:**

- One command starts the stub UI.
- It writes a new file at a relative path in the product repository and refuses to overwrite a file that already exists.
- The process does not import `pilot_app` or another tool.
- The written file is product content. It is not a Claim, a Requirement, or a run result.
- The tool does not propose a remediation from a check result. That role stays the deferred note in `docs/arch/ARCHITECTURE.md`.
