# TL-07 — Start the pilot

**Status:** Draft. Not authorization to implement.
**Epic:** [EP-09 Start each Packs v2 tool on its own](../EPIC.md)

**As a pilot operator**, I want to start pilot_app, so that one cover still links Requirements, Claims, Scaffold, Check, and Review for the end-to-end pilot.

**Accept when:**

- One command starts the cover that EP-01 uses today. The package and the command are `pilot_app`, the role `docs/arch/ARCHITECTURE.md` now calls `app/`.
- The cover reads pack directories, Claim files, the run result, and the report, and writes nothing. Its links open the tools.
- The cover's composition lives with pilot_app. `workflow.py` at the repository root is not a second shell.
- Each linked tool still starts on its own, as TL-01–TL-06 accept. pilot_app may import the tools. The tools do not import pilot_app.
- The EP-01 journeys from that cover still complete. This story does not redesign the launcher.
