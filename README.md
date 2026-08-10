# CyberReady+

[![ci](https://github.com/afelin/cyberready/actions/workflows/ci.yml/badge.svg)](https://github.com/afelin/cyberready/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**Local pack gates. Humans review. Not conformity assessment.**

[Site](https://afelin.github.io/cyberready/) · [**First move**](docs/getting-started/60-second-paths.md) · [Intent vs Scope](docs/intent-vs-scope.md) · [White paper](papers/cyberready-whitepaper.md) · [Security model](docs/security-model.md) · [Adopters](ADOPTERS.md)

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/afelin/cyberready/main/scripts/install.sh | sh
cyberready doctor && cyberready demo
```

TTFV ladder (pin **`@v0.4.3`**): `install.sh` → `doctor` → `demo`. Gate pass is evidence for humans — **not** certification. Doctor uses soft-exit diagnostics (tips, not a redesigned hard gate). Release binary is ~10 MB (Go CGO=0 `-s -w`) — accepted; sub-MB Zig is out of scope.

`install.sh` verifies release `checksums.txt` (sha256, fail-closed). macOS/Linux only. `demo` prints a one-pager path — it does **not** open a browser unless you pass `--open`. Sample without demo: [site/samples/onepager.html](site/samples/onepager.html).

From source: `go build -o bin/cyberready ./cmd/cyberready`

## Init + check

```bash
cd /path/to/your/product   # git repo
cyberready init            # house-policy + hooks + skill + ide (use --bare for minimal)
cyberready check           # daily loop — never opens a one-pager
cyberready prepare-release # review-pack/ when you need artifacts
cyberready attest          # human sign-off; unsigned ≠ verified
```

Runs deposit cache + review-pack; attest when human-ready.
## GitHub Action

```yaml
- uses: afelin/cyberready@v0.4.3
  with:
    heal: "true"
    comment_on: red
    upload_sarif: "true"
```

Pin **`@v0.4.3`** (tag + release checksums). Empty `version` builds from this module when `go` is present, otherwise downloads **v0.4.3** (never floating `latest`). Prefer SARIF/annotations over long PR comments. Drop-in example: [`examples/workflows/cyberready-check.yml`](examples/workflows/cyberready-check.yml).

**Pilot deploy:** run `./scripts/redteam-pilot.sh` before promoting a pin.

**First move:** pick one path above (safe try / product repo / CI). Full recipes: [60-second paths](docs/getting-started/60-second-paths.md).

## Claim safety

Gate pass is **not** certification, CE marking, or notified-body approval. CI enforces claim-safe language via `scripts/claim-safety.sh`.

## Advanced

Quiet habit: after `check`, dim Δ readiness / deps / secret-hits lines plus the instrument covenant — see [daily loop](docs/getting-started/daily-loop.md).

**Compose, do not conquer:** CyberReady is an instrument panel / evidence habit for product repos. Pair with SCA (e.g. Trivy/OSV) and secret scanners (e.g. Gitleaks) for depth — not a security program; watchlist = look-here, not a CVE product. Boundary: [strategy boundary](docs/strategy-boundary.md).

| Command | Purpose |
|---------|---------|
| *(bare)* | `doctor` if uninitialized, else `check` |
| `demo [--keep] [--open]` | Sandbox check; `--open` opt-in browser |
| `validate [--json]` | Pack gates (dual-rep); prefer `check` daily |
| `check --diff` | Delta mode — **not** release-gate safe |
| `ask [file] --propose` | Explain GateFailure JSON (propose-only) |
| `packs list\|update\|import\|export-graph\|doctor` | Packs, RKG export, validity doctor |
| `export --sarif\|--explain-packet\|--watchlist-join\|--buyer-questions\|--lay-of-land` | Standards / airlock / buyer checklist / instrument map |
| `sock` | Optional private Unix IPC (Coreward) |
| `init --bare` | Minimal scaffold (no hooks/skill/ide) |
| `init --packs a,b` | Override default house-policy packs |
| `init --workflow` | Opt-in: write `.github/workflows/cyberready.yml` if missing |

Exit codes: **0** pass · **1** gates/error · **2** usage/env.

Deep docs: [Intent vs Scope](docs/intent-vs-scope.md) · [Daily loop](docs/getting-started/daily-loop.md) · [Buyer evidence](docs/getting-started/buyer-evidence.md) · [Design partners](docs/design-partners.md) · [Write your own pack](docs/write-your-own-pack.md) · [Coreward bridge](docs/coreward-bridge.md) · [Docs index](docs/README.md).
