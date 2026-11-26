# TL-03 — Headless scaffold operation, if retained

**Status:** Draft; optional after EP-02 establishes ownership.
**Epic:** [EP-09](../EPIC.md)

**As a developer**, I want to invoke the existing scaffold/stub operation from a command, so that creating a missing product file does not require the Studio GUI.

## Acceptance — Given / When / Then

**Given** a safe repo-relative target path **when** the CLI invokes the existing scaffold backend **then** it creates the requested stub with the same behavior as the existing operation.

**Given** an existing file or a path outside the product root **when** invoked **then** the backend rejects the operation without overwriting or escaping the repository.

**Given** a headless environment **when** the CLI starts **then** it requires neither a separate GUI server nor an independent scaffold system.

Before implementation, verify whether scaffold remains a supported Studio operation and identify its actual EP-02 owner; do not invent a new Studio subsystem or new remediation policy solely for this draft story.
