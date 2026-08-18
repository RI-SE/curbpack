---
name: curbpack
description: Run Curbpack local compliance gates and explain GateFailure JSON. Use when the user asks about pack gates, prepare-release review packs, or curbpack check/validate/ask/attest/doctor/demo/export. Propose-only — never claim certification.
---

# Curbpack

Local-first evidence CLI. Prepares review packs for **human review**. Does not certify conformity.

**Pin:** `@v0.5.2`. Action runners = Linux/macOS only; local CLI includes Windows.

**Instrument panel:** after edits, one `curbpack check` yields an honest map for *this* repo — structural evidence, not a certificate. Green is expensive to fake.

## Install

**Windows (PowerShell)**

```powershell
irm https://raw.githubusercontent.com/afelin/curbpack/main/scripts/install.ps1 | iex
```

**macOS / Linux**

```bash
curl -fsSL https://raw.githubusercontent.com/afelin/curbpack/main/scripts/install.sh | sh
```

Then: `curbpack doctor` → `demo` → `init` → `check` → `share [--bundle] [--reveal]`. After PATH loss: `curbpack doctor --repair` (local only — not auto-update; Windows also `install.ps1 -Repair`). Hub: `docs/getting-started/install.md`.

## When to use

- User wants pack-based documentation readiness checked offline (CRA, house-policy, medtech, custom)
- After editing annex / SECURITY.md / pack-referenced files, re-run `check`
- Explaining a `GateFailure` JSON payload from `.github/curbpack/cache/`
- Safe try without touching product: `curbpack demo`
- Exporting SARIF / RKG / explain-packet / lay-of-land / **ContextPack** for IDEs, tutors, or humans
- Canonical assistant contract: `docs/assistant-loop.md` (AGENTS.md / CLAUDE.md / Copilot instructions in this repo)

## Commands

```bash
curbpack                 # doctor if uninitialized, else check
curbpack doctor
curbpack doctor --repair     # local PATH/alias only — no download (Windows: install.ps1 -Repair)
curbpack demo
curbpack init            # house-policy default; --profile house|cra|medtech (--packs wins)
curbpack init --packs cra-baseline,house-policy
curbpack check
curbpack check --heal
curbpack validate --json
curbpack prepare-release
curbpack export --sarif
curbpack export --explain-packet
curbpack export --watchlist-join
curbpack export --lay-of-land
curbpack export --buyer-questions
curbpack export --context-pack   # one washed assistant artifact (prefer this)
curbpack share [--bundle] [--reveal]  # Attach: abs paths; --reveal opens Explorer/Finder
curbpack drift [--json]          # evidence checklist — exit 0 always (not a compliance meter)
curbpack pathway status          # one next ask (human default; --technical for phase)
curbpack pathway suggest --product=hygiene --eu-docs=no --medtech=no --sector=none --house-first=yes
# --house-first is reserved (accepted, currently a no-op)
# human only: pathway confirm-packs|confirm-prose|confirm-share --i-am-human (or CURBPACK_ALLOW_CONFIRM=1; TTY alone is not enough)
curbpack pathway note --set|--forget …   # session notes / corrections / last_draft_pick (not a gate input)
curbpack research [--fetch] [--gate-id=…]   # allowlisted packet + brief; never gates check
curbpack research --cite-check <draft.md>   # cite-or-refuse before confirm-prose
curbpack completion bash|zsh|fish
curbpack packs list
curbpack packs export-graph
curbpack packs doctor
curbpack ask .github/curbpack/cache/latest_failure.json --propose
curbpack attest                  # human only — never auto-attest
```

## Exit codes (stable)

| Code | Meaning |
|------|---------|
| 0 | Pass / success |
| 1 | Gate failures (or operational error on check/validate) |
| 2 | Usage / environment (unknown command, not a git repo when required) |

JSON payloads include `schema_version` for agents. SARIF `ruleId` equals `gate_id`.

## Agent rules

1. Treat `curbpack check` / `validate` exit code as authoritative for gate pass/fail.
2. Prefer dual-rep markdown + JSON IR — do not invent legal prose as source of truth.
3. `ask --propose` and `check --form-hints` suggest edits only; apply in the editor (or `--apply-stub` / `--heal` for missing stubs), then re-check.
4. Never claim the product is certified, CE-marked, or notified-body approved.
5. Coreward is optional integrator-only — see `docs/coreward-pointer.md`; not part of activation. Chat tutors must re-check; they never greenlight.
6. Cold start: prefer `curbpack init` (house-policy) unless the user asks for CRA/medtech.
7. **After edits** (human or agent) in an initialized repo, run `curbpack check` (or bare `curbpack`).
8. **On red:** run `curbpack check --heal` then `curbpack ask … --propose` (explain-packet optional for tutors); never invent certification; `--heal` never auto-attests; **never attest**.
9. **On green:** optional `export --context-pack` (preferred), and/or `--lay-of-land` / `--buyer-questions` for human share — not a security program. Thin recipe: `curbpack share`.
10. Remediations cache: `.github/curbpack/cache/remediations.json`. Instrument map: `.github/curbpack/cache/instrument.json`. ContextPack: `.github/curbpack/cache/context-pack.json`.
11. Release path: `prepare-release` then human `attest` — never auto-attest. Optional MCP: `examples/mcp` (CLI remains SoR; no new sock ops).

12. **No auto-demo loops.** Demo does **not** open a browser unless `--open`.
13. RKG: `packs export-graph` → `.github/curbpack/graph/policy-graph.json`. Prefer `export --sarif` / `check --json` over inventing findings.
14. Explain-packets are sanitized teaching surfaces only (`CURBPACK_EXPLAIN_ALLOW_CLOUD=0` default).
15. Keep git hooks from `init` for agent PRs — they force the check loop.
16. Agent lineage env (optional): `CURBPACK_AGENT_ID`, `CURBPACK_MODEL_HASH`, `CURBPACK_MANDATE_ID`.
17. Authoring packs: set `assurance_class` (e.g. `structural_draft`); `packs import` refuses missing class / claim-adjacent theater copy.
18. **Pathway:** orchestrate via `curbpack pathway status|suggest|note` only — never hand-write `pathway-seed.json`. Stop and ask a human to run `confirm-packs` / `confirm-prose` / `confirm-share` / `attest` (`--i-am-human` or `CURBPACK_ALLOW_CONFIRM=1`; TTY alone is not enough). Never invent pack ids (closed world: suggest ∩ `packs list`). After `confirm-packs`, prefer RKG (`.github/curbpack/graph/policy-graph.json`) + `curbpack research` + form-hints / remediations for L4 drafts — never invent regulation text. Every external factual claim needs a cite id from the research packet; uncited Claims → refuse (`research --cite-check`). Prefer ContextPack `pathway` next over seed spelunking. After attest, status next is local proof verify (`proof/index.html` + evidence pointer) — human only. MCP never confirms or attests. Seed and research packet do not affect check pass/fail. See `docs/getting-started/pathway.md`.
19. **Three ways in:** Write→Check (optional pathway), Bring-docs→Check (files on pack paths; no portal PDF ingest), or CI alone — same local `check`. On red, optional `curbpack research --gate-id=<failed_id>`.
20. **Dual-draft HITL (always):** When drafting house prose or remediating with external claims: (1) read seed notes/corrections/last_draft_pick + research packet + ContextPack failures; (2) propose **Option A** and **Option B** with cite ids; (3) state **Recommended: A|B** with ≤3 reasons; (4) stop for human pick/edit; (5) run `research --cite-check`; (6) record via `curbpack pathway note --set last_draft_pick=A|B|edited`. Never auto-apply or auto-attest.
21. **Dual remotes:** phrases “sync both” / “sync curbpack remotes” → run `./scripts/curb-sync.sh` only (never force-push).
