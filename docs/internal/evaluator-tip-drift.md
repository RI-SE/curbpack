# Evaluator tip drift (directional)

> Maintainer note. Dual-remote mirror sync was removed (`scripts/curb-sync.sh` deprecated). **RI-SE/curbpack** is the sole public source of truth; **afelin/curbpack** is private development.

## Behavior bar (do not re-derive)

Vacuous-pass / not-started / target-absent semantics for tip evaluators are already locked by tests under `internal/validate`. Treat those cases as the behavior bar — do not invent a second definition of “aligned.”

Relevant cases include:

- `TestAntiPlaceholderTargetAbsentWhenAllMissing` — missing annex targets must **not** vacuous-pass `anti_placeholder` (target absent).
- `TestNPMDepBanVacuousPassPresentManifest` — present manifest with no banned pin may pass.
- `TestNPMDepBanTargetAbsentMissingManifest` — missing `package.json` must **not** vacuous-pass dep-ban (target absent).
- Related `anti_placeholder` stub / fresh-stub tests in the same package.

`AllNotStarted` / `IsNotStartedFailure` in `internal/validate` classify scaffold / absent / not-started findings for TTY; tip comparison must respect that split (○ not-started ≠ ✘ fail ≠ silent green).

Lean runner: [`scripts/evaluator-behavior-check.sh`](../../scripts/evaluator-behavior-check.sh).

## Drift checks must be directional

When comparing public tip to another tip (or a private development tip):

1. Report **which side is ahead** (commit/date), not only whether hashes differ.
2. **Fail loudly** if evaluator behavior diverges (vacuous-pass / AllNotStarted / anti_placeholder target-absent semantics).
3. Do **not** treat hash-only mirror noise as a pass/fail signal — missing dual-remote sync means tip inequality alone is expected noise, not a gate.

## Public SoR

Public tip comparison is against **RI-SE `main`**. Private afelin work is development; it is not a second public mirror to keep byte-identical for its own sake.

Not conformity assessment. Exit codes and local `curbpack check` remain authoritative for repo gates.
