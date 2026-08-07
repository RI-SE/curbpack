---
description: Run CyberReady+ local compliance gates and explain GateFailure JSON. Use when the user asks about pack gates, prepare-release review packs, or cyberready check/validate/ask/attest/doctor/demo. Propose-only — never claim certification.
---

# CyberReady+

Local-first evidence CLI. Prepares review packs for **human review**. Does not certify conformity.

## When to use

- User wants pack-based documentation readiness checked offline (CRA, house-policy, medtech, custom)
- After editing annex / SECURITY.md / pack-referenced files, re-run `check`
- Explaining a `GateFailure` JSON payload from `.github/cyberready/cache/`
- Safe try without touching product: `cyberready demo`

## Commands

```bash
cyberready                 # doctor if uninitialized, else check
cyberready doctor
cyberready demo
cyberready init --packs house-policy --hooks --skill --ide
cyberready init --packs cra-baseline,house-policy
cyberready check
cyberready check --diff
cyberready check --form-hints
cyberready check --form-hints --apply-stub
cyberready check --heal
cyberready validate --json
cyberready prepare-release
cyberready ask .github/cyberready/cache/latest_failure.json --propose
cyberready attest
cyberready packs list
```

## Exit codes (stable)

| Code | Meaning |
|------|---------|
| 0 | Pass / success |
| 1 | Gate failures (or operational error on check/validate) |
| 2 | Usage / environment (unknown command, not a git repo when required) |

JSON payloads include `schema_version` for agents.

## Agent rules

1. Treat `cyberready check` / `validate` exit code as authoritative for gate pass/fail.
2. Prefer dual-rep markdown + JSON IR — do not invent legal prose as source of truth.
3. `ask --propose` and `check --form-hints` suggest edits only; apply in the editor (or `--apply-stub` / `--heal` for missing stubs), then re-check.
4. Never claim the product is certified, CE-marked, or notified-body approved.
5. Coreward is optional (`CYBERREADY_SOCK` + `cyberready sock`); fail-open if absent.
6. Cold start: prefer `--packs house-policy` unless the user asks for CRA/medtech.
7. After doc/dep edits in an initialized repo, run `cyberready check` (or bare `cyberready`).
8. **On red:** run `cyberready check --heal` then `cyberready ask … --propose`; never invent certification; `--heal` never auto-attests.
9. Remediations cache: `.github/cyberready/cache/remediations.json`.
10. Release path: `prepare-release` then human `attest` — never auto-attest.
