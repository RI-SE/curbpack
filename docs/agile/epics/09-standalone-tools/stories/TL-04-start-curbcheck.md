# TL-04 — Start curbcheck alone

**Status:** Draft. Not authorization to implement.
**Epic:** [EP-09 Start each Packs v2 tool on its own](../EPIC.md)

**As a CI job**, I want to start curbcheck by itself, so that the pipeline gets one run result and an exit code without a UI and without the pilot.

**Accept when:**

- `python3 -m checks` remains the start. The run result's `tool` is `curbcheck`.
- The process does not import `app`, `pilot_app`, `requirements.ui`, `claims.ui`, review, or scaffold.
- It reads `curbpack.json`, pack directories, and Claim files, and writes one run result. It does not write Requirement, Claim, or report files.
- Exit 0 only when at least one Check ran and every row passed. A failed, skipped, or empty run exits 1. A usage error exits 2.
- The package directory stays `checks/`. This story does not rename it.
