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

## Share bundle

`curbpack share --bundle` writes `review-pack/evidence-bundle.html` with `<!-- curbpack-bundle-schema:1 -->`, optional REMEDIATION banner on red gates, and embedded hpurl pointer JSON for offline verify.

See also: [Strategy boundary](strategy-boundary.md) · [Coreward bridge](coreward-bridge.md) · [Security model](security-model.md)
