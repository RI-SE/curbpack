# VL-01 — Name the version objects and keep layout honest

**Status:** Draft. Not authorization to implement.  
**Epic:** [EP-11 Pack version lifecycle and exchange](../EPIC.md)  
**Depends on:** Packs v2 layout as in `docs/reference/packs2.md` and `docs/concepts/packs.md`.

**As a Studio maintainer**, I want one shared vocabulary for “version”, so that UI copy, stories, and tests do not call a git commit, a working-copy timestamp, a Requirement digest, and `pack.version` by the same name.

## Pedagogical example (normative shape)

Organisation workspace root `W`:

```text
W/
  cra-baseline/
    2026-10-01T120000Z/     # dated working copy (editor), not pack.version
      pack.json             # "version": "1.1.0-draft" or the version being prepared
      CRA-ANNEX-VII-RISK.json
  published/
    cra-baseline/
      1.0.0/                # immutable pack release
      1.1.0/
```

| Phrase | Means | Does not mean |
| --- | --- | --- |
| Pack release | `published/<id>/<version>/` + `pack.json` `version` | Git commit, Requirement digest |
| Requirement version | Payload digest (canonical JSON without `signed`) | Filename suffix, git commit |
| Working copy | Dated directory under `<id>/` | Published release |
| Git commit | File history / optional seal reading | Packs v2 version graph |
| “Latest” (pilot) | The one release or working copy the operator is editing | Query over all releases in UI |

## Requirements (Given / When / Then)

Acceptance tests (doc or UI string checks) are derived **only** from these criteria.

### R1 — Distinct terms in epic-facing docs/UI touched by this work

**Given** a screen or help block introduced or rewritten under EP-11 that mentions baselines or versions  
**When** a reader compares it to the table in the pedagogical example  
**Then** it does not use one word for two rows of that table  
**And** it does not describe a git commit as `pack.version`.

### R2 — Layout unchanged as the store of releases

**Given** an existing published tree `published/cra-baseline/1.0.0/`  
**When** a newer release `1.1.0` is added under this epic’s later stories  
**Then** `1.0.0` remains on disk byte-identical  
**And** Requirement files are not renamed to embed semver or digest in the filename.

### R3 — Pilot latest-only is documented

**Given** EP-01 pilot guidance  
**When** an operator asks whether they must edit two pack versions at once  
**Then** pilot docs/UI may state that the pilot workflow focuses on the single active working copy / selected release  
**And** multi-version side-by-side editing is deferred to later VL stories, not required for pilot acceptance.

## Out of scope

- Implementing extract, release, zip, import, Claims rebind, or SQLite.
- Changing Packs v2 field names.
- Deciding Git branch-per-pack or repo-per-pack workflows.

## Open (not decided by this draft)

| Topic | Proposed resolution (not normative) | Status |
| --- | --- | --- |
| Whether UI drops the word “baseline” entirely in favour of “release” / “working copy” | Prefer drop “baseline” for Pack Editor copy | OPEN |

Do not implement until this story and any required OPEN rows are accepted.
