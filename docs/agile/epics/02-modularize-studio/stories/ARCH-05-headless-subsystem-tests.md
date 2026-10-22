# ARCH-05 - Test functions without the GUI

**Status:** Draft; after pilot baseline.
**Epic:** [EP-02 Modularize Curbpack Studio](../EPIC.md)

**As a developer**, I want to call and test subsystem functionality directly in Python, so that tests and future clients do not need to open the Studio GUI.

**Accept when:**
- Representative operations in each affected subsystem run without starting FastAPI or a browser.
- Automated tests exercise domain behavior through subsystem functions, with separate tests for HTTP integration and GUI interactions as needed.
- The existing test suite remains usable; failures introduced by the refactoring are fixed before a story is marked complete.
- A future CLI, automation or remote client can reuse subsystem behavior through a deliberate interface without duplicating it; implementing those clients is not part of this story.
