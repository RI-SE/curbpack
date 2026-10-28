# PE-10 — Sign Requirements

**Status:** Reviewed 2026-10-28 by danielfl.

**Epic:** [EP-01 Pack Editor](../EPIC.md)

**As a Pack author**, I want to sign a Requirement that I have reviewed so that its approved content can be verified later.

**Accept when:** The signature covers the actual Requirement payload according to Packs v2; verification indicates whether that content is unchanged; a changed payload cannot keep a valid old signature; a signature is not a claim of product compliance.

**Human review:** 2026-10-28, danielfl. Editing a signed Requirement shows **unsigned** at once. **Cancel** reloads the editor and the signed state is back. The saved file is not written by that edit. `markDirty` only changes the badge, and Cancel is `location.reload()`.
