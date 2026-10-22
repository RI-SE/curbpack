# ARCH-04 - Thin GUI pages

**Status:** Draft; after pilot baseline.
**Epic:** [EP-02 Modularize Curbpack Studio](../EPIC.md)

**As a developer**, I want separate, simple page modules under `app/pages/`, so that the GUI is easy to read and change without touching subsystem logic.

**Accept when:**
- The existing monolithic page code is divided into page-oriented modules where useful; no single catch-all `pages.py` remains responsible for unrelated tools.
- Pages handle rendering, inputs, feedback and calling the appropriate operations; they do not implement domain decisions.
- JavaScript is used for necessary browser interactions, not as a second implementation of Python business rules or normative validation.
- Existing navigation, forms, extraction progress, diff review and other supported GUI behavior still work.
