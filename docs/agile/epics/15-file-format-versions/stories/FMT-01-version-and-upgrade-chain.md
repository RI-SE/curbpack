# FMT-01 — Read an older file up to the current format version

**Status:** Draft. Not authorization to implement.

**Epic:** [EP-15 File format versions](../EPIC.md)

**Starts when:** Scheduled. Does not block EP-01.

**As a person opening a repository the pilot already knows,** I want an older `curbpack.json`, Pack, Requirement, or Claim to load as the current format version, so that I can see it and choose whether to save that version.

## Behavior

Each of the four file kinds carries a format version.

A missing version number means the file is the input to the step that produces the first numbered version. That first numbered version is the contract in force when the field is added. It is not a new Packs v2 field beyond the version number itself.

Later contract changes add a function each. The function from `1.0` to `1.1` does only that step. The function from `1.1` to `1.2` does only the next. The reader calls them in order until the object is the version the running code understands. The object stays in memory.

Load does not write the file. Save is a separate call. A file at a version the code does not know is rejected, and the file is unchanged.

`upgrade_stored_claim` stops writing the file when a claim is loaded. If the retired `{check, args}` shape must still be read, that rewrite is the Claim step that produces it, and it stays in memory until save.

## Acceptance — Given / When / Then

### FMT1-01 — Missing version loads as the first numbered version

**Given** a file of one of the four kinds that matches the contract in force when the version field is added, and that has no version number
**When** it is loaded
**Then** the object in memory is that first numbered version, and the file on disk is unchanged.

### FMT1-02 — One function per step

**Given** a file at version `1.0` and a chain whose next steps are `1.0` to `1.1` and `1.1` to `1.2`
**When** it is loaded by code that understands `1.2`
**Then** the `1.0` to `1.1` function runs, then the `1.1` to `1.2` function runs, and no function skips a version.

### FMT1-03 — Save is separate

**Given** a file loaded to a newer version in memory
**When** the caller does not save
**Then** the file on disk is the version that was read.

**And when** the caller saves
**Then** the file on disk is the version that was in memory.

### FMT1-04 — Unknown version

**Given** a file whose version number is newer than the code understands
**When** it is loaded
**Then** the load is rejected and the file is unchanged.

### FMT1-05 — Claim load does not write

**Given** a claim file in the retired `{check, args}` shape
**When** it is loaded
**Then** the object in memory is the current Claim shape, and the file on disk is unchanged until save.

## Out of scope

A new contract change beyond the version field. A reference-product migration. A screen that edits the version number by hand.
