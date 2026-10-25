# TL-06 — Start curbpack-review alone

**Status:** Draft. Not authorization to implement.
**Epic:** [EP-09 Start each Packs v2 tool on its own](../EPIC.md)

**As a reviewer**, I want to start curbpack-review by itself, so that I can read a report I received, write my decision, and sign that report without running Checks or editing Requirements.

**Accept when:**

- One command starts the review UI on an existing report file.
- The reviewer can record `decision` and `review-sign` on that report.
- The process does not call the check runner and does not import `pilot_app`, the Requirements UI, or the Claims UI.
- Signing the report leaves Requirement files, Claim files, and the run result unchanged.
- A missing report is an error from this tool. Compiling a report is curbpack-compile, not a second button that runs Checks.
