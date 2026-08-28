# Stable contracts (nave freeze)

Schema consumers (Action, tutors, agents) may rely on these shapes. Breaking changes require a **major pin bump** + CHANGELOG entry. Additive fields are OK.

Code cites: [`internal/exportx/explain.go`](../internal/exportx/explain.go) · [`internal/ir/`](../internal/ir/).

## Install marker + repair (local-only)

| Contract | Rule |
|----------|------|
| Marker schema | `curbpack-install-marker:1` |
| Marker path (Unix) | `~/.local/share/curbpack/install-marker.json` (or `$XDG_DATA_HOME/curbpack/…`) |
| Marker path (Windows) | `%LOCALAPPDATA%\Programs\Curbpack\install-marker.json` |
| `doctor --repair` | Re-asserts install dir on PATH + refreshes `curb` alias; **no network**; exit **2** if binary missing (print install command) |
| `install.ps1 -Repair` | Same semantics as `doctor --repair` on Windows |
| Auto-update | **Forbidden** — repair never downloads; reinstall uses pinned install script |

Install SoR: [getting-started/install.md](getting-started/install.md). Manifest: [`scripts/install-manifest.json`](../scripts/install-manifest.json).

## Explain-packet airlock

Invariants consumers and CI enforce:

- No absolute home paths (`/Users/…`, `/home/…`, `C:\Users\…`)
- No PEM blobs
- `untrusted_metadata` field contains literal `<untrusted_metadata>…</untrusted_metadata>`
- Packet **never** greenlights — tutors must re-run `curbpack check` before any “fixed” claim
- Cloud export only when `CURBPACK_EXPLAIN_ALLOW_CLOUD=1` (default `0`)

## GateFailure / dual-rep IR

Consumers may rely on (`schema_version` = `"1"`):

| Field | Notes |
|-------|--------|
| `schema_version` | IR version for agents |
| `timestamp` | ISO-ish run time |
| `concurrency_control` | OCC parent / state token |
| `statechart_context` | Parent path + pack-eval regions (see below) |
| `agent_identity` | Optional agent/mandate ids. Additive: `source` (`self-declared` \| `bridge`) and fail-open `reason` (`not_installed` \| `unavailable`). Not in `state_hash`. |
| `failures[]` | `gate_id`, `severity`, `type`, `sanitized_description`, `ast_coordinates`, `remediation` |
| `pack_id` | Composed pack id(s) |
| `readiness_score` | Optional numeric readiness |

### `statechart_context` semantics (clarified, additive)

- `active_parent_state_path` — when `.github/curbpack/cache/pathway-seed.json` exists, the path is `Root / Pathway / {phase}` (shared pathway vocabulary). Without a seed, the legacy path `Root / ActiveVerification / PackEval` remains.
- `failed_orthogonal_regions` — pack-eval / rule regions only (unchanged). Pathway ticks are parent path, not fake pack regions.
- Pathway seed is **not** a check pass/fail input; exit code still comes from gate failures only.

## Instrument cache path

`.github/curbpack/cache/instrument.json` — additive, best-effort Δ map beside IR cache. Missing/corrupt → treat as absent; never a gate.

## Compatibility rule

- **Breaking** (drop IR field, weaken airlock) → major pin bump + CHANGELOG.
- **Additive** fields / optional ops documentation updates → OK within `@v0.5.x` after freeze review if needed.

## Drift report (`curbpack drift`)

Informational only — **exit code always 0**. No boolean `aligned` / `no_drift` / `pass` / `green`.

| Field | Notes |
|-------|--------|
| `schema` | `curbpack-drift-report:1` (additive signal IDs only — no bump) |
| `signals[]` | `{ id, detail }` per signal (see [evidence-drift](getting-started/evidence-drift.md)) |
| `suggested_actions[]` | Optional human hint strings |

New signal IDs (`docs_unchanged_since_attest`, `docs_changed_since_attest`, optional `contact_expires_past` / `contact_missing`) are additive rows. No boolean `aligned` / `no_drift` / `pass` / `green`. Cache-only fingerprint compare for `share_stale` — never runs `validate.Run` in the default path.

## Optional sock IPC (example only)

The main `curbpack` binary does **not** ship a `sock` verb (SDD §14). Integrators who need Unix IPC build the example server:

- Server: `examples/mcp/cmd/curbpack-sock` → `examples/mcp/internal/sock/`
- MCP client fallback: `examples/mcp/internal/sockclient/` when `CURBPACK_SOCK` is set
- Golden path for agents and MCP: shell out to `curbpack` CLI

Frozen ops (unchanged): `validate_delta`, `get_latest_failure`, `graph_summary`, `explain_packet`. See [coreward-bridge.md](coreward-bridge.md).

## Share bundle

`curbpack share --bundle` writes `review-pack/evidence-bundle.html` with `<!-- curbpack-bundle-schema:1 -->`, optional REMEDIATION banner on red gates, and embedded hpurl pointer JSON for offline verify.

## Review report (`curbpack review`)

Offline document triage of a received curbpack-native review-pack **or** a repository tree (`review --repo`). **Not** a product verdict or conformity assessment. No current MCP / `exportx` consumer — CLI-local assessor surface; treat JSON as the product contract for future intake.

| Contract | Rule |
|----------|------|
| Schema | `curbpack-review-report:2` (`--json`) |
| Classifier | `classifier_version` string (current tip: `refclass:2`) — golden list; changes that move the reference denominator **hard-invalidate** accepted Mapper links |
| States | `confirmed` \| `unconfirmed` \| `contradicted` only |
| Additive `cause` | Unconfirmed: `producer` \| `extractor` \| `genuine` \| `external`. Contradicted: `self_disagree` (digest/structure contradictions) |
| Counters | Split unconfirmed/contradicted-by-cause fields; `dropped_count` (+ `dropped` under `--full`) |
| Digests | Producer emits payload/file digests; bind disagreements appear as sibling `*_bind` keys — reader contradicts, never silently prefers bind |
| `subject_commit` | Producer commit the bundle/repo claims (`subject_commit`, omitempty). Bundle: from gate payload; repo: CLI git read (review never calls git). |
| `subject_state_hash` | Producer `state_hash` when present in bundle `hpurl-pointer.json` (`subject_state_hash`, omitempty). |
| `parent_record_digest` | When `--since <prior.json>` is set: prior report's `record_digest`, written **before** child `record_digest` (hashed in). Empty when no `--since`. |
| `review --verify-chain` | Exclusive mode: `curbpack review --verify-chain <parent.json> <child.json>`. Exit **0** when `child.parent_record_digest == parent.record_digest` (both non-empty); exit **1** on empty digests or mismatch; usage → **2**. No `--repo`/`--batch`/`--since`/`--packs`/`--json`/`--full`. |
| Airlock | Redact-then-emit home-path/PEM in findings (`detail`, `id`, `source`, `dropped`), then fail closed via `PacketLooksAirlocked` |
| Exit | `1` if any contradicted (or `--batch` child unreadable/contradicted); usage → `2`. `--batch --full` / `--batch --json` / `--repo --batch` → usage |
| Method | `method_id` = `curbpack-review-method`; tip `method_version` = **1.3.0** ([`docs/method/review-method-1.3.0.md`](method/review-method-1.3.0.md)); must equal `review.MethodVersion` |
| `bundle_digest` | sha256 over sorted relative slash paths, each length-prefixed, each followed by the length-prefixed sha256 of the **full** file contents (streamed; not subject to the per-file parse cap). Symlinks and out-of-jail paths excluded. **Refuse-oversize ceiling** (64 MiB total): when Lstat size sum or streamed bytes would exceed the ceiling → contradicted `structure:bundle-size-cap`, `bundle_digest` left **empty** — never truncate, never partial hash |
| `structure:digest-incomplete` | When any digest-path file is unreadable or skipped during streaming → contradicted finding, `bundle_digest` left **empty** (refused, never truncated) — same refuse-closed class as `structure:bundle-size-cap` |
| `digest_scope` | Always emitted: `bundle` (full walked tree) or `closure` (surfaces read + resolved path targets). **Never compare digests across scopes** |
| `record_digest` | sha256 over the canonical JSON record with `record_digest` **and `bundle_root`** empty. Digests are computed **after** airlock → tally → sortFindings (and after any size-cap finding re-tally/sort), immediately before emit. `bundle_root` is excluded because it is directory-name dependent |
| `Finding.ID` | **Stable contract.** Shapes: `reference:path:<p>`, `reference:url:<short>`, `reference:claim:<rule-id>`, `structure:<file>`, `digest:<key>`. Consumers may key on these; changes require a pin bump |
| `source` | Document the reference was extracted from; present on reference edges; omitted (`omitempty`) on non-edges. Not baked into `Finding.ID` |
| `ReferencesOnly` | When true: skip pack structure/load/digest checks; walk with fixed ignore list (`.git/`, cache+evidence+graph helpers + legacy, `review-pack/`, `node_modules`/`vendor`/`dist`/`build`/`target`/`.venv`); emit `digest_scope=closure`; missing governed surfaces → `structure:surface-absent:<path>`. No `.gitignore` parser |
| `edges` | Schema **frozen** (Shared Frame §6 TO, **0b DECIDED**). **Writer not implemented** (W7). Human-approved export only. v0.6.0 expiry unchanged. CTAM: [seam doc](https://github.com/RI-SE/ctam/blob/main/docs/integration/curbpack-seam.md). |
| `triage_surfaces` | Sorted list of surfaces actually used for reference extraction (from `ResolveTriageSurfaces`). Always populated — same comparability class as `digest_scope` |
| `surfaces_digest` | sha256 over sorted length-prefixed surface path bytes. Always populated |

## Buyer questions / holding report (settlement)

| Contract | Rule |
|----------|------|
| `BuyerQuestion.settlement` | `settles` \| `indicative` (render axis). `answered` remains structural pass/fail. |
| Three-state render | Answered + `settles` → **Yes**; answered + `indicative` → **Present, not settled** — never **Yes** on indicative. |
| `answers_suppressed` | When true (e.g. `--diff` / skipped rules), consumers **refuse the import** — do not treat every `answered: false` as failure. |
| `export --holding-report` | Requires `--since <prior-report.json>`. **Refuses** section 1 when `answers_suppressed`. Never renders **Yes** on indicative settlement rows. Emits `parent_record_digest` when chained. |

See also: [Strategy boundary](strategy-boundary.md) · [Coreward bridge](coreward-bridge.md) · [Security model](security-model.md) · [Phase 6 kill-test](internal/phase6-kill-test.md) · [Review method 1.3.0](method/review-method-1.3.0.md) · [Shared Frame](shared-frame.md) · [Substantial-modification screening (delivered)](internal/substantial-modification-screening.md)
