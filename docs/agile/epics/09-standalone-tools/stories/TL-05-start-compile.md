# TL-05 — Compile reports from CLI

**Status:** Draft; after EP-02 Compile migration.
**Epic:** [EP-09](../EPIC.md)

**As a report preparer**, I want a headless CLI for existing Compile operations, so that I can build reports from recorded results without opening Studio.

## Acceptance — Given / When / Then

**Given** an existing valid Run Result **when** a supported Compile CLI operation runs **then** it calls `studio/compile/` backend operations also used by its REST router and produces the same output.

**Given** existing JSON/PDF rendering commands **when** migration completes **then** their supported arguments, output content and overwrite/error behavior continue to work.

**Given** compilation **when** invoked **then** it neither executes Checks nor records a human Review decision or signature.

**Given** a headless environment **when** started **then** no Studio server, browser or Review UI is required. No duplicate report formatter is introduced.
