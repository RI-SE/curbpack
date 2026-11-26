# TL-01 — Use Pack and Requirements operations from CLI

**Status:** Draft; after relevant EP-02 Pack migration.
**Epic:** [EP-09](../EPIC.md)

**As a Pack maintainer**, I want a headless CLI for supported Pack/Requirements operations, so that I can use them in scripts without running Studio's GUI.

## Acceptance — Given / When / Then

**Given** a Pack operation is implemented in `studio/pack/impl/` **when** called from its CLI **then** the CLI invokes that same backend operation as the Pack REST router; no second extractor, editor, signer or exporter is created.

**Given** valid and invalid inputs **when** the CLI runs **then** results, validation failures, and file side effects match the backend contract, with usable messages and exit codes.

**Given** a headless installation **when** the CLI starts **then** it does not import Studio UI pages or depend on a running FastAPI server.

**Given** an operation planned for VL-01–VL-03 but not yet implemented **when** this story is accepted **then** no placeholder implementation is added for that future feature.

Preserve established CLI compatibility; decide any new entry-point spelling against the actual migrated packaging. Studio retains its single integrated GUI.
