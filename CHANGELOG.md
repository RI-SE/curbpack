# Changelog

## v0.4.1

Activation polish + one pin truth (trust-surface freeze continues from v0.4.0).

- **Pin truth** — Action/docs/examples/site/`install.sh` default → `@v0.4.1` (no floating `latest` story)
- **Quiet UX** — activation #12–#16 on the pin: Ladder A defaults, quiet init/attest, Action-only `--workflow`, time-to-green harness, Δ whisper on green
- **Site CTA** — install link targets working `#install` anchor

## v0.4.0

Single adoptable pin after Ladder A + RKG + exporters.

- **Ladder A UX** — doctor → demo → init → check → prepare-release → attest; house-policy cold start
- **Local RKG** — `packs export-graph` / `policy-graph.json`; medtech extends cra-baseline compose
- **Exporters** — SARIF (`ruleId` = `gate_id`), explain-packet airlock, watchlist∩SBOM join (informational)
- **Elite tests** — package tests for exportx + SSH-agent sign (`-f` is key; reject `agent-bind:`)
- **Thin CLI** — `cmd/cyberready` dispatcher; commands in `internal/cli`
- **CI** — required job name `redteam-pilot`; merges to main should require it green
- **gtm-oss** — NON-PRODUCT quarantine (not for Pages / adopters)
- **Coreward dogfood** — contract consumer test + bridge checklist; tutors must re-check

Trust-surface freeze (30 days) starts at this tag — see `docs/security-model.md`.
