# CyberReady — Claude Code

**Local pack gates. Humans review. Not conformity assessment.**

Same contract as [AGENTS.md](AGENTS.md). Full platform matrix + memory map: [docs/assistant-loop.md](docs/assistant-loop.md).

## Loop

```bash
cyberready check
# red: cyberready check --heal && cyberready ask .github/cyberready/cache/latest_failure.json --propose
# green (optional share): cyberready export --context-pack
```

Exit code is authoritative. Never claim certification. Pin **`@v0.4.3`**.

Thin MCP (optional): [examples/mcp/](examples/mcp/).
