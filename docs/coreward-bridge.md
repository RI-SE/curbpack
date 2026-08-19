# Coreward soft-bridge protocol

> **Integrators only; adopters do not need this.** Curbpack is fully self-sustaining without Coreward. Public architecture brief: https://afelin.github.io/coreward/ — standardized wording: [coreward-pointer.md](coreward-pointer.md). Authorities/CISO path: [for-authorities.md](for-authorities.md).

**Golden path:** MCP and agents shell out to the `curbpack` CLI. Exit codes and IR are authoritative.

**Optional sock IPC** lives in the example tree only (`examples/mcp/`) — not in the main binary (SDD §14). Build and run:

```bash
go build -o curbpack-sock ./examples/mcp/cmd/curbpack-sock
./curbpack-sock --repo /path/to/product
```

Path resolution when `--path` is omitted:

1. `CURBPACK_SOCK` if set
2. `$XDG_RUNTIME_DIR/curbpack/curbpack.sock`
3. `$TMPDIR/curbpack-$UID/curbpack.sock`
4. `.curbpack/curbpack.sock` under the working directory

The socket file is mode `0600`. World-writable parent directories are refused. There is **no** default shared `/tmp/curbpack.sock`.

## Ops

| Op | Purpose |
|----|---------|
| `validate_delta` (default) | Re-run quiet validate; GateFailure-shaped response |
| `get_latest_failure` | Read `.github/curbpack/cache/latest_failure.json` |
| `graph_summary` | Paths-only RKG stats (`policy-graph.json`) |
| `explain_packet` | Sanitized teach packet (`<untrusted_metadata>…</untrusted_metadata>`) |

Implementation: `examples/mcp/internal/sock/`. MCP client: `examples/mcp/internal/sockclient/` (used when `CURBPACK_SOCK` is set).

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
- Chat must **re-run** `validate_delta` / `curbpack check` before any “fixed” claim.
- Chat never decides gates and never writes attest capsules.
- Prefer Coreward local/private chat. Cloud tutors only if the operator exports an explain-packet and sets `CURBPACK_EXPLAIN_ALLOW_CLOUD=1` (default **0**).
- Missing sock → fail-open (`not_installed` / `unavailable`). Never block promote solely because Curbpack is absent.

```bash
curbpack export --explain-packet
# → .github/curbpack/cache/explain-packet.json (relative paths; secrets/PEM stripped)
```

## Coreward expectations

- Missing `CURBPACK_SOCK` → `{ ok: false, reason: "not_installed" }` (fail-open)
- Sock set but connect fails → `{ ok: false, reason: "unavailable" }` (fail-open)
- Never block promote solely because Curbpack is absent

## Run (example server)

```bash
go build -o curbpack-sock ./examples/mcp/cmd/curbpack-sock
./curbpack-sock --repo /path/to/product
# or explicit private path:
./curbpack-sock --path "$XDG_RUNTIME_DIR/curbpack/curbpack.sock" --repo /path/to/product
```

Lay-of-land and explain-packet exports are teaching/share surfaces only — after any proposed fix, still re-run `validate_delta` / `curbpack check`. Neither export greenlights gates.

See also: [Intent vs Scope](intent-vs-scope.md) · [Strategy boundary](strategy-boundary.md) · [Stable contracts](stable-contracts.md) (airlock freeze).

**Marketing unblock:** live Coreward sock dogfood recorded 2026-08-09 (see Last dogfood). Public contracts remain frozen; do not claim Coreward as part of this OSS product face.

## Next planning round: Coreward

Live Coreward dogfood recorded (see Last dogfood). Remaining checklist for operators:

1. Wire Coreward MCP / Cursor env to `CURBPACK_SOCK` against a product fixture (with `curbpack-sock` running).
2. Run explain-packet → propose-only → `validate_delta` recheck end-to-end from Coreward.
3. Confirm fail-open (`not_installed` / `unavailable`) never blocks promote.
4. ~~Fill “Last dogfood: DATE”~~ — done 2026-08-09 (see below).
5. Marketing unblock for live tutor loop is recorded; still do not co-brand Coreward into this OSS face.

**Last dogfood:** 2026-08-09 — Coreward bridge live sock (curbpack 0.4.3): explain_packet → propose-only → validate_delta still red on incomplete house-policy fixture; get_latest_failure + graph_summary OK; fail-open not_installed without sock. Optional private Coreward sibling — not co-branded.

## Dogfood checklist (explain-packet ↔ Coreward)

Curbpack-side prep. Does **not** replace the Coreward planning round above.

Run once before marketing the tutor loop:

```bash
go build -o bin/curbpack ./cmd/curbpack
go build -o bin/curbpack-sock ./examples/mcp/cmd/curbpack-sock
# red fixture repo $REPO (init --bare --packs house-policy; omit SECURITY.md)
./bin/curbpack check                              # expect non-zero
./bin/curbpack export --explain-packet            # → .github/curbpack/cache/explain-packet.json
go test ./internal/contract/ -run 'Coreward|ExplainPacket' -count=1
SOCK="${XDG_RUNTIME_DIR:-/tmp}/curbpack-dogfood/curbpack.sock"
mkdir -p "$(dirname "$SOCK")"
./bin/curbpack-sock --path "$SOCK" --repo "$REPO" &
export CURBPACK_SOCK="$SOCK"
# IPC: {"op":"explain_packet"} then {"op":"validate_delta"} — validate still red
# MANUAL chat: MCP curbpack_explain_packet → propose only → never claim fixed
# heal / edit → ./bin/curbpack check → green; only then may chat say fixed
```

Checklist:

1. In a product repo: `./bin/curbpack check` (red is fine) then `./bin/curbpack export --explain-packet`.
2. Confirm `.github/curbpack/cache/explain-packet.json` has `<untrusted_metadata>`, no `/Users/`/`/home/`, no PEM blobs (`go test ./internal/contract/ -run Coreward` / `PacketLooksAirlocked`).
3. Coreward: set `CURBPACK_SOCK` in MCP/Cursor env; start `curbpack-sock`; read packet body only into chat (MCP `curbpack_explain_packet` or sock `explain_packet`) — never raw source.
4. After tutor proposes a fix, apply in the editor; **do not** trust the model.
5. Re-check: sock `validate_delta` or `./bin/curbpack check` / MCP `curbpack_validate_delta` — exit/ok is authoritative.
6. Only then may chat say “fixed”. Attest remains human-only.
7. Missing sock → fail-open; never block promote solely because Curbpack is absent.
8. Default `CURBPACK_EXPLAIN_ALLOW_CLOUD=0`; cloud export only with explicit `=1`.
9. In-repo fixture: `internal/contract/explain_coreward_consumer_test.go` + `go test ./examples/mcp/internal/sock/`.
10. Coreward bridge: `vibe-engine-os/src/release-gate/curbpack-bridge.ts` (`consumeExplainPacket` + recheck note). Skill: explain-packet → never claim fixed → `curbpack_validate_delta`.
