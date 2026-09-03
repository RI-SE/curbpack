# Daily loop (habit)

Value recurs without babysitting. Pin stays **`@v0.5.2`**. Gate green is evidence for human review — not certification.

Three ways in (Write / Bring / CI) all land on the same local `check`; optional research briefs never gate pass/fail. See [60-second paths](60-second-paths.md).

**Instrument panel pitch:** after every change (human or agent), one `curbpack check` yields an honest map for *this* repo — structural evidence, not a certificate. Keep hooks: they are the agent force-multiplier.

```text
every PR  → Action @v0.5.2 (comment_on: red, upload_sarif) + hooks
local day → curbpack check   # Δ readiness / deps / secret-hits + covenant
handoff   → curbpack share [--bundle]
drift     → curbpack drift   # informational checklist (exit 0)
release   → prepare-release → attest → proof verify
optional  → export --lay-of-land · export --buyer-questions
```

## Every PR

Copy [`examples/workflows/curbpack-check.yml`](../../examples/workflows/curbpack-check.yml) once, or `curbpack init --workflow` (writes only if missing). Keep `comment_on: red` — no PR noise on green.

Opinionated `curbpack init` installs a non-healing pre-commit hook by default. **Keep it** for agent PRs so every edit re-enters `curbpack check`; remediation remains an explicit command.

## Local day

```bash
curbpack check
```

When a prior evidence cache exists, quiet dim lines show `Δ readiness`, and (when prior `instrument.json` exists) `Δ deps` / `Δ secret-hits`. Every check also prints the instrument-panel covenant. No dashboard.

When `check --heal` creates missing stubs, that invocation remains red until product-specific content replaces any generated scaffold text.

## Release

```bash
curbpack prepare-release
curbpack attest   # human only; never auto
# proof/index.html vs .github/curbpack/evidence/hpurl-pointer.json
```

## Evidence drift (optional)

```bash
curbpack drift        # human checklist — exit 0 always
curbpack drift --json
```

See [evidence-drift](evidence-drift.md).

## Self-dogfood

This repo runs [`.github/workflows/curbpack-dogfood.yml`](../../.github/workflows/curbpack-dogfood.yml) on every PR. Treat flakes as P0.

## Buyer / map share (optional)

```bash
curbpack export --lay-of-land      # shareable instrument map
curbpack export --buyer-questions  # human checklist
```

Details: [Buyer evidence](buyer-evidence.md).

See also: [60-second paths](60-second-paths.md) · [Design partners](../design-partners.md)
