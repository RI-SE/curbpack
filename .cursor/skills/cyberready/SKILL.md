---
name: cyberready
description: Run CyberReady+ local compliance gates and explain GateFailure JSON. Use when the user asks about CRA/Annex VII evidence, prepare-release review packs, or cyberready validate/ask/attest. Propose-only — never claim certification.
---

# CyberReady+

Local-first evidence CLI. Prepares review packs for **human review**. Does not certify conformity.

## When to use

- User wants CRA / medtech documentation readiness checked offline
- After editing Annex VII or medtech markdown, re-validate
- Explaining a `GateFailure` JSON payload from `.github/cyberready/cache/`

## Commands

```bash
cyberready init
cyberready validate
cyberready validate --json
cyberready prepare-release
cyberready ask .github/cyberready/cache/latest_failure.json --propose
cyberready attest
cyberready packs list
```

## Agent rules

1. Treat `cyberready validate` exit code as authoritative for gate pass/fail.
2. Prefer dual-rep markdown + JSON IR — do not invent legal prose as source of truth.
3. `ask --propose` suggests edits only; apply changes in the editor, then re-validate.
4. Never claim the product is certified, CE-marked, or notified-body approved.
5. Coreward is optional (`CYBERREADY_SOCK` + `cyberready sock`); fail-open if absent.
