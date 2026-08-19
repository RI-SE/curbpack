# SDD gap analysis

**Baseline:** `feat/pr4-funnel` vs [software-design-document.md](software-design-document.md) v1.0 (19 Aug 2026).  
**Date:** 20 Aug 2026.

---

## §14 Remove list — status

| Item | Was present? | Wave A action |
|------|----------------|---------------|
| `internal/sock/` | Yes | **Removed** — package, CLI verb, stable-contracts section, contract test |
| `matchWithTimeout` in `validate.go` | Yes (3 sites) | **Removed** — uses `re.Match` directly |
| `auditASTReachability` duplicate call | Yes (main loop + `CheckImportReach`) | **Fixed** — main-loop call removed; rule path stamps pack rule id |
| `testdata/fuzz/` (18 root seeds) | Yes | **Removed** — kept `internal/validate/testdata/fuzz/FuzzSafeJoin/` |
| `writeIfChanged`, `attestInfo`, `loadAttestInfo`, `var _ = ir.Failure{}` in `release.go` | Yes | **Removed** |
| `scripts/cite-check.sh` | Yes, unreferenced | **Deleted** |
| `scripts/time-to-green-windows.ps1` | Yes, unreferenced | **Deleted** |
| `scripts/dogfood-explain-recheck.sh` | Yes, prose-only ref | **Deleted** |

**Residual sock prose:** site pages, `coreward-bridge.md`, whitepaper, and `CURBPACK_SOCK` bridge labeling in `internal/ir/identity.go` still mention optional socket IPC historically. MCP now shells out to CLI only. Full doc sweep deferred to a follow-up PR.

---

## Wave B — not started (by design)

| SDD item | Repo today |
|----------|------------|
| `internal/report` | Missing — findings re-declared across ~8 structures |
| `internal/sign` | Missing — attest uses ssh-agent notes, not `ssh-keygen -Y` pack verify |
| `verify` command | Missing — proof page is client-side hash compare only |
| `references` check primitive | Missing |
| Check-kind registry (§6.3) | Partial — `checkRegistry` map in `checks.go`, not unified `CheckKind` descriptor |
| `packs init --from-repo` | Missing |
| `packs sign` / `packs trust import` | Missing |
| Computed `assurance_class` | Author-declared in pack JSON today (SDD: computed at load) |
| Canonical report model | Missing |

---

## Check name mapping (SDD §6 vs shipped)

| SDD primitive | Shipped `check` kind | Notes |
|---------------|----------------------|-------|
| `exists` | `file_present`, `annex_file` | Same evaluator (`checkFilePresent`) |
| `structured` | (partial) heading/substance heuristics in packs | No dedicated primitive name |
| `content-forbids` | `text_forbid`, `anti_placeholder` | Split across two kinds |
| `manifest-constrains` | `npm_dep_ban`, `manifest_dep_ban` | Same handler |
| `owned` | `owned` | Shipped |
| `fresh` | `fresh` | Shipped |
| `references` | — | Wave B |
| `traces` | — | Wave D |
| `import_reach` | `import_reach` | Legacy AST demo; not in SDD eight |

---

## Command surface (SDD §9 vs shipped)

| Verb | SDD | Shipped |
|------|-----|---------|
| `scan` | Read-only diagnosis | **Yes** (`reality-check` alias) |
| `fix --<gap>` | One templated file | **Yes** (`--art14`, etc.) |
| `init` | Config + hooks | **Yes** |
| `check` | Evaluate; exit authoritative | **Yes** |
| `ask-my-suppliers` | Question set + pack | **Yes** |
| `verify` | Verify received artifact | **No** — Wave B |
| `packs init --from-repo` | Author by example | **No** — Wave B |
| `packs sign` / `packs trust import` | Sign / import signers | **No** — Wave B |
| `export --<format>` | SARIF, context pack, … | **Yes** |
| `attest` | Human-only capsule | **Yes** |
| `doctor` | Environment diagnosis | **Yes** |
| `pathway` / `research` / `drift` / `share` | Not in SDD verb table | Shipped — pathway/research sidecar; reconcile in agent contract |

---

## Wave A — completed vs deferred

| Wave A item | Status |
|-------------|--------|
| Canonical SDD in `docs/` | **Done** |
| Gap analysis (this doc) | **Done** |
| §14 removals | **Done** (residual sock prose noted above) |
| Agent contract §12 parity | **Done** — human-only list + scan-first loop in AGENTS/CLAUDE/SKILL |
| `house-policy` as general case (§11.3) | **Verified** — README, site, 60-second-paths already lead with house-policy |
| Zero-install distribution (npm/Docker/Homebrew) | **Deferred** — npm wrapper exists on other branch; not Wave A merge blocker |
| Pin signature scope spike | **Deferred** — §17 open question |
| Trust-import human-only enforcement | **Contract only** — `packs trust import` not built yet |

---

## §17 open questions (unchanged)

1. Does `ssh-keygen -Y` express multi-signer + namespace separation (source / derivation / review)? Afternoon spike before Wave B planning.
2. Does `packs init --from-repo` beat a blank template on three internal repos? Decide before building §7.1.

---

## Recommended next PR split

1. **This PR (Wave A core):** SDD + gap analysis + §14 removals + agent contract §12 — merge after `go test ./...` + `claim-safety.sh` green.
2. **PR5 distribution:** npm optionalDeps / Docker / Homebrew (Wave A remainder) — independent of PR4 merge.
3. **PR6 Wave B spike:** `ssh-keygen -Y` afternoon + check-kind registry scaffold — gated on three external `scan` runs per SDD precondition.
