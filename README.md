# CyberReady+

[![ci](https://github.com/afelin/cyberready/actions/workflows/ci.yml/badge.svg)](https://github.com/afelin/cyberready/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**CyberReady+** — local evidence CLI. Packs encode policy. Humans review. Not a certificate of conformity.

[Site](https://afelin.github.io/cyberready/) · [White paper](papers/cyberready-whitepaper.md) · [Security model](docs/security-model.md)

## Install (no Go)

```bash
curl -fsSL https://raw.githubusercontent.com/afelin/cyberready/main/scripts/install.sh | sh
cyberready doctor && cyberready demo
```

`install.sh` verifies release `checksums.txt` (sha256, fail-closed). macOS/Linux only. `demo` runs in a temp sandbox and **prints** the one-pager path — it does **not** open a browser unless you pass `--open`. For a static sample without running demo: [site/samples/onepager.html](site/samples/onepager.html).

From source: `go build -o bin/cyberready ./cmd/cyberready`

## Quick start

```bash
cd /path/to/your/product   # git repo
cyberready init --packs house-policy --hooks --skill --ide
cyberready check           # daily loop — never opens a one-pager
cyberready prepare-release # review-pack/ when you need artifacts
cyberready attest          # human sign-off; unsigned ≠ verified
```

## GitHub Action

```yaml
- uses: afelin/cyberready@v0.3.1
  with:
    version: v0.3.1
    heal: "true"
    comment_on: red
    upload_sarif: "true"
```

Pin **`@v0.3.1`** (tag + release checksums). For paranoid consumers, also pin the commit SHA of that tag. Release downloads in the Action verify checksums like `install.sh`. Prefer SARIF/annotations over long PR comments.

**Pilot deploy:** run `./scripts/redteam-pilot.sh` before promoting a pin. Trust-surface code (Action resolve, SafeJoin, attest OCC, claim-safety) is under a **30-day feature freeze** after `v0.3.1` — bugfixes only.

## Commands

| Command | Purpose |
|---------|---------|
| *(bare)* | `doctor` if uninitialized, else `check` |
| `demo [--keep] [--open]` | Sandbox check; `--open` opt-in browser |
| `check` / `validate` | Pack gates (exit 0/1/2) |
| `prepare-release` | Review pack + evidence |
| `attest` / `view` | Git Notes capsule |
| `packs list\|update\|import` | Embedded packs; network update needs sha256 pin |
| `sock` | Optional private Unix validate_delta server |

Exit codes: **0** pass · **1** gates/error · **2** usage/env.

## Claim safety

Gate pass is **not** certification, CE marking, or notified-body approval. CI enforces claim-safe language via `scripts/claim-safety.sh`.

Deep docs (manuals, launch, GTM): under `docs/` — not required for first install.
