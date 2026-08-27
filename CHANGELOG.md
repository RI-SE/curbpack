# Changelog

## Unreleased (on `main`, not yet pinned — Action pin stays `@v0.5.2`)

- **v6 reference integrity (Shared Frame + W1–W6)** — method [`docs/method/review-method-1.3.0.md`](docs/method/review-method-1.3.0.md); classifier **`refclass:2`** via [`internal/claimid`](internal/claimid) (Option A + deny-list; Shared Frame **0a decided**, **0b** edges still OPEN). `parent_record_digest` + `review --verify-chain`. Buyer/holding settlement three-state: indicative never renders **Yes**; `export --holding-report` refuses when `answers_suppressed`. Production MCP [`cmd/curbpack-mcp`](cmd/curbpack-mcp) (stdio library; no `net/http`). Shared Frame pin `RI-SE/curbpack@a36aeef` (PR #31 merge). Action pin unchanged (no bump). Not certification.
- **Review Part B through B2** — `review --repo --packs a,b`; thin-surfaces stderr (≤2); Report always emits sorted `triage_surfaces` + `surfaces_digest`; method [`docs/method/review-method-1.1.1.md`](docs/method/review-method-1.1.1.md) + dual re-pin; repo-mode Detail wording (`in-repo …` / `path not found in repo:`) without a second method bump. Operator docs + edges reservation expiry calendar stub. Nomenclature fence: never describe curbpack as measurement (`claim-safety` NOMEN deny). Pin stays `@v0.5.2`. Not certification.
- **Review repository mode** — `curbpack review --repo [path]` (default `.`) triages governed documentation surfaces via the same classifier/method as received-pack review; `ReferencesOnly` + closure `digest_scope`; `Finding.source` + per-document `--since` decay; method [`docs/method/review-method-1.1.0.md`](docs/method/review-method-1.1.0.md) (1.0.0 retained; superseded for tool tip by 1.1.1). Pin stays `@v0.5.2`. Not certification.
- **Review method primitives** — additive Report fields (`method_id`, `method_version`, `bundle_digest`, `record_digest`); refuse-oversize `structure:bundle-size-cap`; ContextPack `pack_versions`; published method [`docs/method/review-method-1.0.0.md`](docs/method/review-method-1.0.0.md) + stable-contracts rows; frozen `testdata/comparison-bundle-2026-1/`; `review --since` report differ (NEW / CLEARED / PERSISTING; exit codes unchanged); help admits `--since`. Pin stays `@v0.5.2`. Not certification.
- **Reader review wedge (comms + CLI)** — `curbpack review <dir>` offline document triage (confirmed / unconfirmed / contradicted) on curbpack-native review-packs — not a product verdict. Teaching sample at `site/samples/review-pack/`; site page `site/receiving-submissions/` (“Are you receiving submissions?”). Home / for-reviewers promote artifact trust table + review path. Pin stays `@v0.5.2`. Not certification.
- **Phase 0-slim honesty** — installer fallback no longer prints a failing `go install …/RI-SE/curbpack` line; claim-safe guidance points to RI-SE binary releases / `docs/getting-started/install.md` and notes the Go module path remains `github.com/afelin/curbpack` until wave-2 (strangers: binary only). SDD banner + §8–§10 clarify **`curbpack verify` is not a shipped CLI verb** (future reader wedge: `curbpack review`). Directional evaluator tip-drift note + `scripts/evaluator-behavior-check.sh`. Pin stays `@v0.5.2`. Not certification.
- **Reader wedge (`curbpack review`)** — offline triage of a received curbpack-native `review-pack/` (no git, no network): confirmed / unconfirmed / contradicted on structure, digests, and references (allowlisted URLs recorded never fetched). Pasteable triage note; exit 1 on contradicted. Frozen sample: `testdata/sample-review-pack` + `site/samples/review-pack`. Site: reviewers-first home, receiving-submissions page, trust-table links. Phase 6 scaffold + post-kill-test gates for intake/lint/batch. Document triage only — not a product verdict. Pin stays `@v0.5.2`.
- **Slice A HITL honesty** — structural evidence for human review — not certification and not a CRA-compliant / CE / notified-body claim. GateFailure IR + ContextPack populate optional `agent_id` / `model_hash` / `active_mandate_id` from env; `source` is `self-declared` vs `bridge` when the Coreward sock path is present; missing sock fail-opens (`not_installed` / `unavailable`) and does not fail check; AgentIdentity is not in `state_hash`; no new sock ops. `TestNoVerdictSurface` locks public renderers so compliant / merge-allow are not a Curbpack verdict (`readiness_score` stays on GateFailurePayload). Opt-in `cra-baseline` file gate `docs/incident/art14-path.md` (Art 14 reporting rehearsal vs later handling clock; not house-policy default). **`--diff` always runs `anti_placeholder`** (committed heal stub + unrelated README change still fails `HOUSE-ANTI-PLACEHOLDER` / `CRA-ANTI-PLACEHOLDER` with scaffold body overlap). **`pathway confirm-prose` requires every displayed prose path independent** (not one-of); always runs inward cite-check (repo artifact or allowlisted cite; heal stubs / empty / agent-cache are not grounding). **Existing `cra-baseline` greens go red until `docs/incident/art14-path.md` is real prose.** `--heal` remaining red is intended. `--i-am-human` / `CURBPACK_ALLOW_CONFIRM=1` unchanged. Counsel note: Art 14 reporting vs handling; AI Act Art 50 grace is not blanket. Example workflow: compose Trivy/Gitleaks beside check; never set `CURBPACK_ALLOW_CONFIRM=1` on the Action. Pin stays `@v0.5.2`. Pack catalog frozen (three ids). Trust-surface freeze continues (no Action resolve / SafeJoin / OCC / airlock / sock / pack catalog).
- **Handoff honesty** — one-pager cover sheet (files-to-read front, gate score on the back); `anti_placeholder` fails DefaultScaffoldBody overlap (`--heal` remaining red is intended); drift `docs_changed_since_attest` / `docs_unchanged_since_attest` plus optional security.txt contact signals; medtech formhints guess path `docs/medtech/…`. Proof yes/no stamp copy; share prints `share_stale` first; doctor warns on `CURBPACK_ALLOW_CONFIRM=1`; optional attest `--reviewed-by` in evidence only. Structural evidence for human review — not certification. Pin stays `@v0.5.2`. Trust-surface freeze continues (no Action resolve / SafeJoin / OCC / airlock / sock / pack catalog).
- **Premortem production fixes (PR #57)** — `init` gitignores cache/evidence; Action `heal` default **false** + scaffold≠readiness warning; pathway confirm requires `--i-am-human` / `CURBPACK_ALLOW_CONFIRM=1` (TTY alone refused); `LatestNoteCommit` walks notes (not HEAD-without-note); Action refuses Windows runners + red `REMEDIATION REVIEW` artifacts; claim-safety scans `*.ps1`; redteam **18/18**; maintainer playbook [`docs/getting-started/release-v0.5.2.md`](docs/getting-started/release-v0.5.2.md)
- **validate OCC parent** — when HEAD is unresolved, omit parent SHA (empty string) and continue gate evaluation; never inject `000…0`
- **Cross-OS TAM hardening** — gauntlet Action honesty assert (no `or True`); `doctor --repair` fail-closed after LookPath; marker BOM-safe + custom InstallDir; CI repair smoke without `|| true`; completions for `drift` / `--repair` / `--bundle` / `--reveal`; atomic `.new` cleanup; `share --reveal` empty-message; docs pin sweep `@v0.5.2`

## v0.5.4

First-run honesty — scan/install UX for RI-SE strangers. Action pin stayed `@v0.5.2`.

- **Scan honesty** — Exit 0 invariant early + late; `Scan complete — repository unchanged.`; `Next (optional):` only when findings remain; Satisfied vs Open; badge/`--format markdown` still emit claim line
- **Installer** — print REPO/VERSION/ASSET/URL/INSTALL_DIR before download; refuse non-`RI-SE/curbpack` unless `CURBPACK_REPO_I_UNDERSTAND=1`; friendly 404; safe piped-manifest read; `doctor --repair` footer
- **Tryout** — dual-pin (CLI ≠ Action); stop after scan; no Discussions CTA; PATH recovery
- **Release** — tag `v0.5.4` on RI-SE; `main` advertises after tag-smoke (`CURBPACK_VERSION=v0.5.4`)

## v0.5.3

Ladder 0 scan milestone — install + read-only `curbpack scan` for strangers. Action pin stayed `@v0.5.2`.

- **`curbpack scan`** — read-only diagnosis (no init, no hooks, no score); Art 14 reporting clock; product hint; exit 0 = diagnosis finished (not pass/cert)
- **Install** — `main` scripts download smoke-verified **v0.5.3** binary (manifest ≡ release-gate); Windows amd64 asset published
- **Docs** — stranger Ladder 0, RISE tryout, troubleshooting scan section; Discussions not required for feedback
- **Claim safety** — prepares evidence for human review — not CE / notified-body / certification

## v0.5.2

Cross-OS TAM — distribution + UX + repair (Trust track deferred).

- **Windows exe** — release asset `curbpack_windows_amd64.exe`; CI `windows-latest` + `windows-smoke`
- **install.ps1** — PowerShell installer alongside `install.sh`; fail-closed checksums; `-Repair` = local PATH/alias (same as `doctor --repair`)
- **doctor --repair** — local PATH/alias repair only (no network / no auto-update); fail-closed if LookPath still missing
- **share --reveal** + **`Attach:`** — optional Explorer/Finder reveal; absolute attach paths on every OS
- **platform.OpenFile** — cross-OS open helper for demo/proof surfaces
- **Docs** — dual fence (PowerShell | macOS/Linux) + same ladder; install hub + troubleshooting links; pin `@v0.5.2`
- **Action** — default download pin `v0.5.2`; runners remain **Linux/macOS only** (not Windows runners)
- **Release tag** — cut **after merge** once CI is green and assets publish (do not advertise the pin before the tag exists)

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
