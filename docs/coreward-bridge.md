# Coreward soft-bridge protocol

CyberReady listens on a Unix domain socket. Path resolution:

1. `CYBERREADY_SOCK` if set
2. `$XDG_RUNTIME_DIR/cyberready/cyberready.sock`
3. `$TMPDIR/cyberready-$UID/cyberready.sock`
4. `.cyberready/cyberready.sock` under the working directory

The socket file is mode `0600`. World-writable parent directories are refused. There is **no** default shared `/tmp/cyberready.sock`.

## Ops

| Op | Purpose |
|----|---------|
| `validate_delta` (default) | Re-run quiet validate; GateFailure-shaped response |
| `get_latest_failure` | Read `.github/cyberready/cache/latest_failure.json` |
| `graph_summary` | Paths-only RKG stats (`policy-graph.json`) |
| `explain_packet` | Sanitized teach packet (`<untrusted_metadata>…</untrusted_metadata>`) |

## Request

```json
{"op":"validate_delta","payload":{}}
```

`op` defaults to `validate_delta` if omitted.

## Response (GateFailure-shaped)

```json
{
  "ok": false,
  "detail": "score=40 failures=3",
  "failures": [ { "gate_id": "…", "severity": "high", "…": "…" } ],
  "payload": { "timestamp": "…", "concurrency_control": {}, "failures": [] }
}
```

On success with zero failures: `"ok": true`.

## Chat tutors only (Coreward / Flash / Ollama)

- Chat may **summarize** or draft remediation prose from explain-packets.
- Chat must **re-run** `validate_delta` / `cyberready check` before any “fixed” claim.
- Chat never decides gates and never writes attest capsules.
- Prefer Coreward local/private chat. Cloud tutors only if the operator exports an explain-packet and sets `CYBERREADY_EXPLAIN_ALLOW_CLOUD=1` (default **0**).
- Missing sock → fail-open (`not_installed` / `unavailable`). Never block promote solely because CyberReady is absent.

```bash
cyberready export --explain-packet
# → .github/cyberready/cache/explain-packet.json (relative paths; secrets/PEM stripped)
```

## Coreward expectations

- Missing `CYBERREADY_SOCK` → `{ ok: false, reason: "not_installed" }` (fail-open)
- Sock set but connect fails → `{ ok: false, reason: "unavailable" }` (fail-open)
- Never block promote solely because CyberReady is absent

## Run

```bash
cyberready sock --repo /path/to/product
# or explicit private path:
cyberready sock --path "$XDG_RUNTIME_DIR/cyberready/cyberready.sock" --repo /path/to/product
```

See also: [Intent vs Scope](intent-vs-scope.md) (IP / chat boundary).
