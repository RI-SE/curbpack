# ARCH-04 — Convert verified Python pages to thin TypeScript

**Status:** Draft  
**Epic:** [EP-02](../EPIC.md)  
**Stage:** 6, after a page's backend and FastAPI route pass their tests.

**As a developer**, I want each previously verified Python page converted individually to a thin subsystem-owned TypeScript page, so that the final UI uses REST without losing existing interactions.

## Work

- Convert **one** already extracted/moved/separated page or complete small flow at a time under its owner's `studio/<component>/pages/`.
- Preserve current user actions, navigation, field values, progress/abort, diffs, review flows and error states. A visual redesign or new workflow is not part of this story.
- Browser logic is limited to display, forms and interaction state. Domain validation, signing, persistence, evidence access and Check execution stay in backend operations called via REST.
- Remove the corresponding Python-rendered page **only after** the new browser → REST → backend flow is exercised and verified.

## Acceptance (Given / When / Then)

1. **Given** a Python page with verified interactions, **when** the TypeScript replacement is used, **then** users can perform the same workflow with matching persisted effects and error handling.
2. **Given** a UI operation, **when** triggered in the browser, **then** it invokes the owning REST endpoint and does not duplicate the business rule in TypeScript.
3. **Given** long-running Extract or Discovery work, **when** the page is replaced, **then** progress, abort, partial results and reload/resume behavior remain usable as applicable.
4. **Given** passing browser and API tests with no remaining callers, **when** the old Python page is removed, **then** behavior remains green and its coverage row is updated. A static screenshot alone is insufficient.
