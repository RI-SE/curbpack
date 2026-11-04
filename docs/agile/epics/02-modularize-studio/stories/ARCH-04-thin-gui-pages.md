# ARCH-04 — Thin, subsystem-owned TypeScript UI

**Status:** Draft; after pilot baseline.  
**Epic:** [EP-02](../EPIC.md)

**As a developer**, I want TypeScript pages in the subsystem that owns each feature, so that UI changes do not alter Python domain logic.

**Accept when:**
- Pages live in the relevant `studio/<area>/pages/`, e.g. `pack/pages/extract/`, `claim/pages/discovery/`, `review/pages/` and `check/pages/`, not in a central `app/pages.py` or `app/pages/`.
- TypeScript handles presentation, user input, navigation and UI state; all business operations use the owning REST endpoint. No domain validation, filesystem access, persistence, signing or Check execution is reimplemented in TypeScript.
- Preserve actual pilot navigation, extraction progress, diffs, human selection and review behavior, including relevant PoC parity requirements, as the corresponding pages are replaced.
- Convert one feature flow at a time and verify it before removing its old server-rendered page. Do not redesign UI as part of this story.
- For each replaced legacy page, demonstrate real browser interaction triggering the owning REST endpoint and displaying/persisting the expected result, including error states; cover the named pilot journeys in `MIGRATION_COVERAGE.md`. A static page or unit test of Python rendering does not qualify.
