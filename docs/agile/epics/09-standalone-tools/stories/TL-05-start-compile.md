# TL-05 — Start curbpack-compile alone

**Status:** Draft. Not authorization to implement.
**Epic:** [EP-09 Start each Packs v2 tool on its own](../EPIC.md)

**As the person preparing a handoff**, I want to start curbpack-compile by itself, so that I can build the review report from a run result that already exists, without running Checks and without opening the reviewer.

**Accept when:**

- One command reads an existing run result and writes one review report.
- It does not call the check runner, and it does not record a decision or a review signature.
- It does not import `pilot_app` or the review UI.
- An existing report file is replaced only when the caller confirms, using the confirmation `review/compile.py` already requires.
- Requirement files, Claim files, and the run result keep their bytes.
