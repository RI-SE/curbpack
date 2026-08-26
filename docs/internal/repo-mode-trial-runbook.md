# B0′ repo-mode trial — runbook template

> Maintainer ops. Fill after Part B enable + B2 wording land. **Human trial run** — not an agent gate.

## Purpose

Stratified trial of `curbpack review --repo` on real repositories. Gate (B0′): ≥1 human-tagged **`fix-doc`|`add-file`** on ≥3 pack-dense (CRA/medtech) repos → proceed to B1/B6/Gate B. Surfaces ≤2 everywhere → **stop: pack-authoring**.

## Command shape

```bash
# Prefer explicit packs for cold / thin repos (exit 2 without usable ProsePaths otherwise):
curbpack review --repo <path> --packs cra-baseline --json > report.json
# Optional denser packs:
curbpack review --repo <path> --packs cra-baseline,medtech-iec62304 --json
```

Record `method_version`, `digest_scope`, `triage_surfaces` / `surfaces_digest`, and human tags. Never invent pack ids.

## Stratified counts table (human fills)

| # | Repo (name only) | Pack ids | Surface count | Surfaces ≤2? | Genuine unresolved (n) | Human tags (`fix-doc` / `add-file` / `ignore-as-designed`) | Notes |
|---|------------------|----------|---------------|--------------|------------------------|---------------------------------------------------------------|-------|
| 1 | | | | ☐ | | | |
| 2 | | | | ☐ | | | |
| 3 | | | | ☐ | | | |
| 4 | | | | ☐ | | | |
| 5 | | | | ☐ | | | |

## Decision

- [ ] B0′ **go** — proceed B1 fuzz / B6 docs / ask Gate B
- [ ] B0′ **stop** — pack diagnosis only; do not build verify

Commit filled numbers as `docs/internal/repo-mode-trial-YYYY-MM-DD.md` when ready.

_Not certification. Document triage only. Not a measurement product._
