# Migration: CyberReady → Curbpack

This repository was renamed **CyberReady** / **CyberReady+** → **Curbpack** in **v0.5.0**. Same local pack gates and human-review loop; new product mark and module path.

> Unrelated to other commercial offerings that use the name “CyberReady.” This note is the only place that collision is mentioned.

## What changed

| Surface | Before | After (v0.5.0+) |
|---------|--------|-----------------|
| Product | CyberReady+ | **Curbpack** (no “+”) |
| Module | `github.com/afelin/cyberready` | `github.com/afelin/curbpack` (Go module; public repo [RI-SE/curbpack](https://github.com/RI-SE/curbpack)) |
| CLI | `cyberready` | **`curbpack`** + short alias **`curb`** |
| Action pin | `afelin/cyberready@v0.4.3` | `RI-SE/curbpack@v0.5.0` |
| Config | `.cyberready.json` | write **`.curbpack.json`** |
| Cache / evidence | `.github/cyberready/` | write **`.github/curbpack/`** |
| Git notes | `refs/notes/cyberready` | write **`refs/notes/curbpack`** |
| Env | `CYBERREADY_*` | prefer **`CURBPACK_*`** |
| Pages | `/cyberready/` | `/curbpack/` |

## Dual-read (compat)

Curbpack **reads** legacy locations so dogfood repos keep working:

- `.cyberready.json` if `.curbpack.json` is absent
- `.github/cyberready/{cache,evidence,graph}/…` if the new tree is absent
- `CYBERREADY_*` when the matching `CURBPACK_*` is unset
- Old git notes under `refs/notes/cyberready` when reading for OCC / parent hash

**Writes** always go to the new paths (`.curbpack.json`, `.github/curbpack/`, `refs/notes/curbpack`). There is no long-lived `cyberready` binary alias.

If you previously attested under the old notes ref, **re-attest** after upgrade so new capsules land on `refs/notes/curbpack`.

## CI / Action

```yaml
- uses: RI-SE/curbpack@v0.5.0
  with:
    heal: true  # opt-in; Action default is false
```

Install (no Go):

```bash
curl -fsSL https://raw.githubusercontent.com/RI-SE/curbpack/main/scripts/install.sh | sh
# installs curbpack + curb into ~/.local/bin by default
curb doctor && curb demo
```

From source:

```bash
go install github.com/afelin/curbpack/cmd/curbpack@v0.5.0
```

## Pedagogy (unchanged gates)

**Curb outlines** are the pathway warm-start entry (Write → Check). Bring / CI skip outlines. Then packs → `curb check` → review pack for a human.

Primary sentence: see [voice and terms](voice-and-terms.md).

## Claim fence

Same substance as before: not conformity assessment, not CE, not notified-body, not RISE endorsement—product name only swapped to Curbpack.
