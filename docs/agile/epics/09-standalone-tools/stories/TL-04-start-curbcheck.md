# TL-04 — Keep Curbcheck independently executable

**Status:** Draft; EP-02 preserves this capability, EP-09 verifies its CLI interface.
**Epic:** [EP-09](../EPIC.md)

**As a CI operator**, I want to run Curbcheck without Studio, so that checks produce a Run Result and usable exit status in automation.

## Acceptance — Given / When / Then

**Given** a configured product repository **when** the existing `python3 -m checks` (and any packaged `curbcheck` executable) runs **then** it calls the same Curbcheck backend as `curbcheck/api.py`, without Studio server or GUI imports.

**Given** configured Claims **when** Checks execute **then** the Run Result, per-Check status and documented CLI exit behavior match the existing verified baseline; the CLI does not implement its own Check runner.

**Given** valid and invalid paths/configuration **when** executed **then** existing confinement, validation and error behavior remains covered by tests.

**Given** a future VL-04 stale or missing Requirement binding **when** the VL-04 contract is implemented **then** Curbcheck reports that separately and still runs configured Checks, as VL-04 requires.

This story adds neither a second HTTP server nor a new Make target. Do not change existing exit codes or Checks by assumption; changes require an accepted contract.
