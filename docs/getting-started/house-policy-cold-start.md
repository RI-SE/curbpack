# House-policy cold start

For internal IT / engineering teams who want evidence gates **without** EU CRA framing on day one.

```bash
cyberready init --packs house-policy --hooks --skill --ide
cyberready check
```

What you get:

| Asset | Purpose |
|-------|---------|
| `SECURITY.md` + `.well-known/security.txt` stubs | Coordinated disclosure drafts |
| Optional pre-commit → `cyberready check` | Habit loop |
| Cursor skill + VS Code tasks | Agent / F1 entry points |
| Banned-dep + anti-placeholder gates | Deterministic hygiene |

Add CRA or medtech later:

```bash
# edit .cyberready.json packs array, or re-init in a fresh branch:
cyberready init --packs cra-baseline,house-policy
```

Claim safety: gate pass prepares evidence for human review — not certification.
