# CyberReady thin MCP (example)

Stdio MCP server that **shells out** to PATH `cyberready` (or `CYBERREADY_BIN`). Optional `CYBERREADY_SOCK` for `explain_packet` / `validate_delta` only — **no new sock ops**.

Structural evidence for human review — **not** a conformity assessment or certification. CLI exit codes remain source of truth.

## Build

```bash
go build -o cyberready-mcp ./examples/mcp
# or from repo root while developing:
go run ./examples/mcp
```

Requires `cyberready` on `PATH` (fail-open message if missing — never blocks promote).

## Tools

| MCP tool | Backing |
|----------|---------|
| `cyberready_check` | `cyberready check` (`heal` / `packs` args) |
| `cyberready_context_pack` | `export --context-pack` |
| `cyberready_ask_propose` | `ask … --propose` |
| `cyberready_explain_packet` | `export --explain-packet` or sock `explain_packet` |
| `cyberready_validate_delta` | sock `validate_delta` or `validate --json` |

## Claude Desktop

Add to `claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/`):

```json
{
  "mcpServers": {
    "cyberready": {
      "command": "/absolute/path/to/cyberready-mcp",
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
    "cyberready": {
      "command": "/absolute/path/to/cyberready-mcp"
    }
  }
}
```

## VS Code / Copilot MCP

```json
{
  "servers": {
    "cyberready": {
      "type": "stdio",
      "command": "/absolute/path/to/cyberready-mcp"
    }
  }
}
```

## Agent rules

1. Treat tool output + CLI exit as authoritative; never invent gate greens.
2. After proposed edits, re-run `cyberready_check`.
3. Never claim CE / notified-body / certification.
4. Prefer ContextPack over guessing which cache files to open.
5. **No** pathway confirm / attest MCP tools — humans run `cyberready pathway confirm-*` and `cyberready attest` in a terminal. Agents may call CLI `pathway status|suggest` only. Optional CLI `cyberready research` / `--cite-check` is read/propose-only — never a confirm stamp.

See [docs/assistant-loop.md](../../docs/assistant-loop.md) and [pathway](../../docs/getting-started/pathway.md).
