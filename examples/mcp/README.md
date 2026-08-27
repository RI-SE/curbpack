# Curbpack MCP

**Production binary:** [`cmd/curbpack-mcp`](../../cmd/curbpack-mcp) — library-backed stdio MCP (`resolve_references`, `check_citation_currency`, `record_digest`). Read-only; no confirm/attest/doc generation; no listening socket; must not link `net/http`.

```bash
go build -o curbpack-mcp ./cmd/curbpack-mcp
```

This `examples/mcp` tree remains a **legacy shell-out / optional sock** reference. Prefer `cmd/curbpack-mcp` for agent resolution. Trust boundary = local repo — never expose to third parties. See [security model](../../docs/security-model.md).

---

# Legacy thin MCP (example shell-out)

Stdio MCP server that **shells out** to PATH `curbpack` (or `CURBPACK_BIN`). **CLI-only by default** — optional sock when `CURBPACK_SOCK` is set and a sidecar is running.

Structural evidence for human review — **not** a conformity assessment or certification. CLI exit codes remain source of truth.

**Sock (optional, Unix):** removed from the main binary per SDD §14. Reference server: [`cmd/curbpack-sock`](cmd/curbpack-sock/main.go) + [`internal/sock`](internal/sock/sock.go). Client dial: [`internal/sockclient`](internal/sockclient/client.go). MCP may use sock for `explain_packet` / `validate_delta` when `CURBPACK_SOCK` is set; otherwise CLI.

## Build

```bash
go build -o curbpack-mcp-legacy ./examples/mcp
go build -o curbpack-sock ./examples/mcp/cmd/curbpack-sock   # optional sidecar (Unix)
go run ./examples/mcp
```

Requires `curbpack` on `PATH` (fail-open message if missing — never blocks promote).

### Optional sock sidecar (Unix integrators)

```bash
go build -o curbpack-sock ./examples/mcp/cmd/curbpack-sock
./curbpack-sock --repo /path/to/product
export CURBPACK_SOCK="$XDG_RUNTIME_DIR/curbpack/curbpack.sock"   # or --path
```

## Tools

| MCP tool | Backing |
|----------|---------|
| `curbpack_check` | `curbpack check` (`heal` / `packs` args) |
| `curbpack_context_pack` | `export --context-pack` |
| `curbpack_ask_propose` | `ask … --propose` |
| `curbpack_explain_packet` | sock `explain_packet` if `CURBPACK_SOCK` set, else `export --explain-packet` |
| `curbpack_validate_delta` | sock `validate_delta` if set, else `validate --json` |

## Claude Desktop

Add to `claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/`):

```json
{
  "mcpServers": {
    "curbpack": {
      "command": "/absolute/path/to/curbpack-mcp",
      "env": {
        "PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin"
      }
    }
  }
}
```

## Cursor

Cursor MCP settings (`.cursor/mcp.json` or UI):

```json
{
  "mcpServers": {
    "curbpack": {
      "command": "/absolute/path/to/curbpack-mcp"
    }
  }
}
```

## VS Code / Copilot MCP

```json
{
  "servers": {
    "curbpack": {
      "type": "stdio",
      "command": "/absolute/path/to/curbpack-mcp"
    }
  }
}
```

## Agent rules

1. Treat tool output + CLI exit as authoritative; never invent gate greens.
2. After proposed edits, re-run `curbpack_check`.
3. Never claim CE / notified-body / certification.
4. Prefer ContextPack over guessing which cache files to open.
5. **No** pathway confirm / attest MCP tools — humans run `curbpack pathway confirm-*` and `curbpack attest` in a terminal. Agents may call CLI `pathway status|suggest` only. Optional CLI `curbpack research` / `--cite-check` is read/propose-only — never a confirm stamp.

See [docs/assistant-loop.md](../../docs/assistant-loop.md) and [pathway](../../docs/getting-started/pathway.md).
