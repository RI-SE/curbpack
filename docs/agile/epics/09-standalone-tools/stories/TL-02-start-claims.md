# TL-02 — Start curbpack-claims alone

**Status:** Draft. Not authorization to implement.
**Epic:** [EP-09 Start each Packs v2 tool on its own](../EPIC.md)

**As a QA engineer**, I want to start curbpack-claims by itself, so that I can discover evidence, bind and maintain Claims, and sign them without opening the Requirements editor or the pilot.

**Accept when:**

- One command starts curbpack-claims and shows Discover and the Claims editor.
- Those operations also run from that command without a browser.
- The process does not import `pilot_app` or another tool's UI.
- Discover reads Requirement files and the product tree through `common/`. It does not import the extract pipeline (`requirements.extract`).
- An unsigned Claim can be saved and evaluated later by curbcheck. Signing sets `signed` on that Claim. Requirement files stay unchanged.
- Discover is a mode of this tool, not its own program.
