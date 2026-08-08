# Write your own pack

CyberReady evaluates **declared policy packs**. The engine has no CRA/FDA/SOC2 branches — only generic check kinds.

## Pack shape

```json
{
  "id": "acme-secure-coding",
  "name": "Acme Secure Coding Std",
  "version": "0.1.0",
  "description": "House rules for Acme eng — informational, not a certification.",
  "extends": "house-policy",
  "jurisdiction": "internal",
  "validity": { "effective_from": "2026-01-01", "effective_to": "2027-12-31" },
  "citations": [
    { "framework": "Acme", "instrument": "Secure Coding Std", "article": "§3" }
  ],
  "rules": [
    {
      "id": "ACME-SECURITY-MD",
      "severity": "high",
      "type": "POLICY_VIOLATION",
      "check": "file_present",
      "path": "SECURITY.md",
      "min_bytes": 80,
      "min_words": 20,
      "require_headers": ["# Security"],
      "description": "SECURITY.md missing or too thin.",
      "remediation": "Add reporting + response sections.",
      "expected": "SECURITY.md meets structural thresholds.",
      "citations": [
        { "framework": "Acme", "instrument": "Secure Coding Std", "article": "§3.1" }
      ]
    }
  ]
}
```

### Composition (RKG overlays)

- `extends`: base pack id (loaded first; cycles refused)
- `overlays`: optional ordered pack ids applied after the base
- `overlay`: optional RFC 7386 merge-patch object applied to the pack JSON
- Rules are **unioned by `id`** — later packs win
- `medtech-iec62304` is a real overlay: `"extends": "cra-baseline"`

```bash
cyberready init --packs medtech-iec62304   # composes CRA + medtech rules
cyberready packs export-graph              # writes .github/cyberready/graph/policy-graph.json
cyberready packs doctor                    # expired / superseded / pin skew
```

## Supported `check` values

| Check | Fields | Behavior |
|-------|--------|----------|
| `file_present` / `annex_file` | `path`, `min_bytes`, `min_words`, `require_headers` | File exists, size/words/headers |
| `anti_placeholder` | `paths` | Reject TODO / lorem / `[insert …]` |
| `manifest_dep_ban` / `npm_dep_ban` | `package`, `banned_versions` | Ban pins in `package.json` |
| `text_forbid` | `paths`, `pattern` | Regex forbid (e.g. secret-like strings) |
| `import_reach` | — | Optional AST reachability (MVP) |

## Load paths

1. **Embedded** in the binary (`internal/packs/data/<id>/pack.json`)
2. **Override dir:** `CYBERREADY_PACKS_DIR=/path` with `<id>/pack.json`
3. **Air-gap:** `cyberready packs import ./bundle-dir`

## Activate

```bash
cyberready init --packs acme-secure-coding
# or edit .cyberready.json:
# { "packs": ["acme-secure-coding"] }
cyberready check
```

`init` scaffolds **only** paths referenced by composed pack rules (includes `extends` bases).

## Schema validation

Packs are validated on load (id/name/version/rules, supported checks, path jail, citation date windows). Invalid packs fail fast — they never silently skip. `Compose` rejects unknown `extends` cycles.

## Claim safety

Packs prepare evidence for human review. Passing gates is not certification for any regulation or internal audit regime.
