# Coreward soft-bridge protocol

CyberReady listens on a Unix domain socket. Path resolution:

1. `CYBERREADY_SOCK` if set
2. `$XDG_RUNTIME_DIR/cyberready/cyberready.sock`
3. `$TMPDIR/cyberready-$UID/cyberready.sock`
4. `.cyberready/cyberready.sock` under the working directory

The socket file is mode `0600`. World-writable parent directories are refused. There is **no** default shared `/tmp/cyberready.sock`.

## Request

Newline-delimited or single JSON object:

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
