# Coreward soft-bridge protocol

CyberReady listens on a Unix domain socket (`CYBERREADY_SOCK`, default `/tmp/cyberready.sock`).

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
cyberready sock --path /tmp/cyberready.sock --repo /path/to/product
```
