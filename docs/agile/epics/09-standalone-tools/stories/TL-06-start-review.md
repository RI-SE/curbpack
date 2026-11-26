# TL-06 — Optional headless Review operations

**Status:** Draft; optional after EP-02 Review migration.
**Epic:** [EP-09](../EPIC.md)

**As a reviewer**, I want to invoke supported Review backend operations from CLI when useful, so that they can run without a browser while keeping Review decisions separate from Checks and Compile.

## Acceptance — Given / When / Then

**Given** an implemented Review operation **when** its CLI invokes it **then** the same `studio/review/` backend operation and validation used by REST is called, with no duplicate signature/decision logic.

**Given** a report read or signature operation **when** performed **then** its permitted side effects match the Review backend; Requirement, Claim and Run Result bytes stay unchanged.

**Given** a headless environment **when** started **then** no separate Review GUI server or `pilot_app` process is required.

Provide a CLI only for proven useful headless operations; do not create new report schemas or implement the historical resolver before VL-05.
