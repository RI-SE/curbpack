# PE-09 — Edit Requirements

**Status:** Reviewed 2026-10-28 by danielfl.

**Epic:** [EP-01 Pack Editor](../EPIC.md)

**As a Pack author**, I want to edit saved Requirements so that I can improve or correct their interpretation.

**Accept when:** Edit opens the selected section's Requirements; I can inspect the original source passages and change supported fields; unrelated values and references are preserved; modifying signed content requires re-approval; editing one Requirement never silently changes another.

**Human review:** 2026-10-28, danielfl. The editor shows the Requirements and the source passages. Law text is read-only. The UI is accepted. Try discovery, save, and sign are available on this page. A thin frame around `concepts`, `expected_evidence`, and `path_hints`, titled Discovery Hints, is a possible polish and does not block this card.

One Requirement is saved as its own file. `_save_requirement_form` loads the id from the editor URL, `apply_edits` copies that object, and `save_working_requirement` writes `{id}.json` only. A second Requirement is another file and is not in that write.
