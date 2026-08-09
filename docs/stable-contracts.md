# Stable contracts (nave freeze)

Schema consumers (Action, tutors, agents) may rely on these shapes. Breaking changes require a **major pin bump** + CHANGELOG entry. Additive fields are OK.

Code cites: [`internal/sock/sock.go`](../internal/sock/sock.go) · [`internal/exportx/explain.go`](../internal/exportx/explain.go) · [`internal/ir/`](../internal/ir/).

## Sock ops

Four ops only. Listen banner lists them: `validate_delta`, `get_latest_failure`, `graph_summary`, `explain_packet`.

| Op | Semantics |
|----|-----------|
| `validate_delta` (default if `op` omitted) | Quiet validate; GateFailure-shaped response (`ok`, `failures`, `payload`, `detail`) |
| `get_latest_failure` | Read `.github/cyberready/cache/latest_failure.json` without re-running gates |
| `graph_summary` | Paths-only RKG stats from `policy-graph.json` (builds if missing) |
| `explain_packet` | Sanitized teach packet; body wrapped in `<untrusted_metadata>…</untrusted_metadata>` |

### Fail-open reasons (client / missing server)

| Reason | When |
|--------|------|
| `not_installed` | Client has no `CYBERREADY_SOCK` / CyberReady absent — never block promote |
| `unavailable` | Sock set but connect fails, invalid JSON, unsupported op, or op-level error |

Unsupported `op` → `{ ok: false, reason: "unavailable", detail: "unsupported op: …" }`.

## Explain-packet airlock

Invariants consumers and CI enforce:

- No absolute home paths (`/Users/…`, `/home/…`, `C:\Users\…`)
- No PEM blobs
- `untrusted_metadata` field contains literal `<untrusted_metadata>…</untrusted_metadata>`
- Packet **never** greenlights — tutors must re-run `validate_delta` / `cyberready check` before any “fixed” claim
- Cloud export only when `CYBERREADY_EXPLAIN_ALLOW_CLOUD=1` (default `0`)

## GateFailure / dual-rep IR

Consumers may rely on (`schema_version` = `"1"`):

| Field | Notes |
|-------|--------|
| `schema_version` | IR version for agents |
| `timestamp` | ISO-ish run time |
| `concurrency_control` | OCC parent / state token |
| `statechart_context` | Optional state path |
| `agent_identity` | Optional agent/mandate ids |
| `failures[]` | `gate_id`, `severity`, `type`, `sanitized_description`, `ast_coordinates`, `remediation` |
| `pack_id` | Composed pack id(s) |
| `readiness_score` | Optional numeric readiness |

Sock `Response` also exposes top-level `ok`, `reason`, `detail`, `failures`, `payload`, optional `graph`, optional `explain_packet`.

## Instrument cache path

`.github/cyberready/cache/instrument.json` — additive, best-effort Δ map beside IR cache. Missing/corrupt → treat as absent; never a gate.

## Compatibility rule

- **Breaking** (rename/remove sock op, drop IR field, weaken airlock) → major pin bump + CHANGELOG.
- **Additive** fields / optional ops documentation updates → OK within `@v0.4.x` after freeze review if needed.
- New sock `case` without updating **this file** fails `redteam-pilot` (stable-contracts guard).

See also: [Strategy boundary](strategy-boundary.md) · [Coreward bridge](coreward-bridge.md) · [Security model](security-model.md)
