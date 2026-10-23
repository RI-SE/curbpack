# SEC-02 — Keep Pack selection inside its workspace

**Epic:** [EP-03 SSDF security baseline and evidence](../EPIC.md)  
**Status:** Draft; confirm the defect on current HEAD before implementation

**As a user**, I want Pack selection to reject identifiers that address directories outside the intended workspace, so that untrusted metadata cannot redirect reads or writes.

**Evidence to reproduce:** In `curbpack-studio-review(2).zip`, `scripts/security/workspace_selector.py` had two failing cases: `select_working_copy()` and `select_published_pack()` accepted traversal-bearing `pack_id` values when a matching external fixture existed. This is an observed library-boundary problem; HTTP exploitability has not been established.

**Accept when:**

- Reproduce or explicitly disprove the behavior against current HEAD with a temporary workspace; inspect all relevant reader, writer and UI selection entry points.
- Validate Pack identifiers and resolved path confinement for working copies and published Packs, including symlinks where applicable. Reject unsafe input with a defined error; do not silently redirect it.
- Existing valid Pack selection, publishing and reference resolution still work.
- Negative tests cover traversal, absolute paths, symlink escape and a valid control, as applicable to the entry point. Record exact test commands and outcomes.
- If untrusted input can reach the affected path, mark it a pilot release blocker until fixed or explicitly risk-accepted by the responsible owner.

**Out of scope:** general filesystem rewrite, new persistent models or unrelated UI changes.
