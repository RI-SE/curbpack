# Changelog

## Unreleased

- **validate OCC parent** — when HEAD is unresolved, omit parent SHA (empty string) and continue gate evaluation; never inject `000…0`

## v0.5.1

Safe level-up adoption train — Gate 0 blocker fixes before UX commands.

- **HeadSHA** — fail-closed: empty repo returns error, never `000…0` with nil err; OCC parent in validate propagates
- **LatestBind** — shared attest resolution (hpurl-pointer → verify note → git notes fallback); refactors release, export, view
- **Drift** — `curbpack drift` multi-signal human checklist (exit 0 always; no boolean aligned/no_drift)
- **Share bundle** — `share --bundle` → offline `evidence-bundle.html` with schema marker + hpurl embed
- **Init profiles** — `--profile house|cra|medtech` (`--packs` wins); `--medtech` aligned with profile medtech
- **Fingerprint** — cache-only `share_stale` without validate.Run; JSON ParentNoteHash; cache write warnings
- **Templates** — buyer one-pager + proof HTML extracted to `internal/release/templates/` with golden fp tests
- Pin Action / docs → `@v0.5.1`

## v0.5.0

**Curbpack rebrand** (formerly CyberReady / CyberReady+). Same local pack gates and human-review loop; new product mark, module, and CLI.

- **Identity** — module `github.com/afelin/curbpack`; CLI `curbpack` + alias `curb` (no long-lived `cyberready` binary)
- **Dual-read / write-new** — reads legacy `.cyberready.json`, `.github/cyberready/`, `CYBERREADY_*`, `refs/notes/cyberready`; writes `.curbpack.json`, `.github/curbpack/`, `CURBPACK_*`, `refs/notes/curbpack`
- **Pin** — Action / install / docs → `@v0.5.0`; release assets `curbpack_*`
- **Pedagogy** — **Curb outlines** = pathway warm-start entry (Write→Check); Bring/CI skip outlines
- **Pages** — base `/curbpack/`; migration note `docs/migration-cyberready-to-curbpack.md`
- **Attest** — if you used old notes ref, **re-attest** so new capsules land on `refs/notes/curbpack`
- **Attest `state_hash` algorithm** — length-prefixed field stream (commit, parent, sbom, vex) replaces pipe-joined seed (from Unreleased). Existing capsules remain historically readable; re-attest after upgrade.

## v0.4.3

Instrument-panel honesty (trust-surface freeze **continues** from v0.4.0 — no Action resolve / SafeJoin / attest OCC rewrite). Pack ids unchanged.

- **Binding gates** — `bind_repo_token` / `require_tree_paths` on CRA annex drafts; hollow LLM green fails
- **Δ map** — `instrument.json` + capped readiness/deps/secret-hits whispers; `export --lay-of-land`
- **Always-on covenant** — check/doctor epilogue + SARIF `certification_claimed: false` / `instrument_panel: true`
- **Import honesty** — `packs import` requires `assurance_class`; redteam case 11
- **UNSIGNED buyers** — house-policy agent secret paths; loud UNSIGNED one-pager / attestation status

## v0.4.2

Honesty + SME utility (trust-surface freeze **continues** from v0.4.0 — no Action resolve / SafeJoin / attest OCC rewrite).

- **Version integrity** — single `internal/buildinfo.Version`; SBOM tool component matches pin
- **Pack display honesty** — CRA/medtech informational names + `assurance_class: structural_draft` (ids unchanged)
- **Buyer questions** — `export --buyer-questions` Markdown/JSON checklist for human review
- **RISE-neutral publish** — NOTICE funder/non-certify line + `docs/promotion-firewall.md`
- **Pack catalog freeze** — redteam allowlist (three pack ids only)

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
