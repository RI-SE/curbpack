# House-policy cold start

For internal IT / engineering teams who want evidence gates **without** EU CRA framing on day one.

```bash
curbpack init
curbpack check
```

`init` defaults (one line):

| Default | What you get |
|---------|----------------|
| Pack | `house-policy` |
| Hooks | pre-commit → `curbpack check` |
| Skill | `.cursor/skills/curbpack/SKILL.md` |
| IDE | VS Code / Cursor tasks |

Use `--bare` to skip hooks/skill/ide. Override packs with `--packs` only when you need CRA/medtech on day one.

Add CRA or medtech later:

```bash
# edit .curbpack.json packs array, or re-init in a fresh branch:
curbpack init --packs cra-baseline,house-policy
```

Claim safety: gate pass prepares evidence for human review — not certification.

Warm-start (enum seed → HITL ticks): [pathway](pathway.md) — `curbpack pathway status`.
