# CyberReady+

Standalone Go CLI that prepares **supplier readiness evidence** for human review (EU CRA Annex VII drafts, medtech lifecycle docs, SBOM summaries, buyer one-pager).

It does **not** certify conformity, issue CE marks, or replace a notified body.

## Why

- One binary, offline demo, no SaaS, no Coreward required
- Regulation packs are **embedded JSON** (edit data, not Go)
- `prepare-release` → open HTML/Markdown in any editor
- Optional Git Notes attest + HPURL proof page
- Optional Unix socket for Coreward soft-bridge (`CYBERREADY_SOCK`)

## Install

```bash
# Local (this workspace)
go build -o bin/cyberready ./cmd/cyberready

# Or from GitHub once pushed
git clone https://github.com/afelin/cyberready.git
cd cyberready
go build -o bin/cyberready ./cmd/cyberready
```

### Push to GitHub

Empty public repo: https://github.com/afelin/cyberready

From this directory (outside restricted agent sandboxes):

```bash
git add -A
git commit -m "feat: CyberReady+ standalone CLI (P0–P2)"
git remote add origin https://github.com/afelin/cyberready.git
git branch -M main
git push -u origin main
```

## Quick start (offline)

```bash
cd /path/to/your/product/repo   # must be a git repo
cyberready init --medtech
cyberready packs list
cyberready prepare-release
open review-pack/buyer-onepager.html
cyberready validate
```

Edit `docs/annex-vii/*.md` (and `docs/medtech/*` if enabled), remove placeholders, then re-validate.

## Commands

| Command | Purpose |
|---------|---------|
| `init` | `.cyberready.json`, stubs, `proof/index.html` |
| `validate` | Pack gates → GateFailure JSON + semantic markdown |
| `prepare-release` | `review-pack/` three-layer reports + buyer HTML |
| `packs list\|update\|import` | Embedded packs; update/import stubs |
| `ask [file] [--propose]` | Explain GateFailure JSON (propose-only) |
| `attest` | Git Notes Merkle capsule; SSH-agent best-effort |
| `view` | Show capsule for HEAD |
| `sock` | `validate_delta` Unix server for Coreward |

## HPURL

Static page: `proof/index.html`

Fragment contract:

```text
#?h=<state_hash>&p=<commit_or_pointer>&s=<signature_or_token>
```

Coreward-compatible aliases: `run`, `capsule`, `vows`, optional `space`.

## Packs update / air-gap

See [docs/packs-update.md](docs/packs-update.md).

## Coreward (optional)

```bash
export CYBERREADY_SOCK=/tmp/cyberready.sock
cyberready sock --path "$CYBERREADY_SOCK"
```

Protocol: [docs/coreward-bridge.md](docs/coreward-bridge.md). Missing sock ⇒ fail-open `not_installed`.

Coreward repo bridge: `vibe-engine-os/src/release-gate/cyberready-bridge.ts` now performs real `validate_delta` IPC (still fail-open). Commit that change in the Coreward repo separately when convenient.

## Claim safety

CyberReady **prepares evidence for human review**. Do not market gate pass as certification.

## License

Apache-2.0
