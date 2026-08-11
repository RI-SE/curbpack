# Curbpack

[![ci](https://github.com/afelin/curbpack/actions/workflows/ci.yml/badge.svg)](https://github.com/afelin/curbpack/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Curbpack checks your repository against local rule packs and writes a review pack you can hand to a buyer or auditor—on your machine, without claiming certification.

Not conformity assessment. Not CE marking. Not a notified-body opinion.

[Site](https://ri-se.github.io/curbpack/) · [Mirror](https://afelin.github.io/curbpack/) · [Voice and terms](docs/voice-and-terms.md) · [Migration](docs/migration-cyberready-to-curbpack.md) · [First move](docs/getting-started/60-second-paths.md) · [Intent vs Scope](docs/intent-vs-scope.md) · [For authorities](docs/for-authorities.md) · [Glossary](docs/glossary-and-audience.md) · [White paper](papers/curbpack-whitepaper.md) · [Security model](docs/security-model.md) · [Adopters](ADOPTERS.md)

## Who should read what

| Reader | Start |
|--------|--------|
| Builder | Three ways in — [60-second paths](docs/getting-started/60-second-paths.md) · [pathway](docs/getting-started/pathway.md) · [sync both remotes](docs/getting-started/sync-both-remotes.md) · [site builders](site/for-builders/) |
| Buyer / reviewer | Buyer one-pager + trust table — [Buyer evidence](docs/getting-started/buyer-evidence.md) · [for-reviewers](site/for-reviewers/) |
| CISO / authority / auditor | What artifacts mean — [For authorities](docs/for-authorities.md) · [site Authorities](site/for-authorities/) |
| Abbreviations / audience map | [Glossary and audience](docs/glossary-and-audience.md) |
| Full docs index | [docs/README.md](docs/README.md) |

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/afelin/curbpack/main/scripts/install.sh | sh
curbpack doctor
curbpack demo
```

`install.sh` installs `curbpack` and the short alias `curb`, and verifies release `checksums.txt` (sha256, fail-closed). macOS/Linux only. `demo` prints a one-pager path — it does **not** open a browser unless you pass `--open`. Sample without demo: [site/samples/onepager.html](site/samples/onepager.html).

From source: `go build -o bin/curbpack ./cmd/curbpack`

## Init + check

```bash
cd /path/to/your/product   # git repo
curbpack init            # house-policy + hooks + skill + ide (use --bare for minimal)
curbpack check           # daily loop — never opens a one-pager
curbpack prepare-release # review-pack/ when you need artifacts
curbpack attest          # human sign-off; unsigned ≠ verified
```

## Claim safety

Gate pass is **not** certification, CE marking, or notified-body approval. CI enforces claim-safe language via `scripts/claim-safety.sh`. Preferred public wording: [docs/voice-and-terms.md](docs/voice-and-terms.md).

## GitHub Action

```yaml
- uses: afelin/curbpack@v0.5.0
  with:
    heal: "true"
    comment_on: red
    upload_sarif: "true"
```

Pin **`@v0.5.0`** (tag + release checksums). Empty `version` builds from this module when `go` is present, otherwise downloads **v0.5.0** (never floating `latest`). Prefer SARIF/annotations over long PR comments. Drop-in example: [`examples/workflows/curbpack-check.yml`](examples/workflows/curbpack-check.yml).

**Pilot deploy:** run `./scripts/redteam-pilot.sh` before promoting a pin.

## Advanced

Binary size (~10 MB, Go CGO=0 `-s -w`), doctor soft-exit tips, and Zig non-goals live here—not on the first screen. Quiet habit after `check`: see [daily loop](docs/getting-started/daily-loop.md).

**Three ways in:** Write (optional [pathway](docs/getting-started/pathway.md) + dual drafts + cite-check), Bring existing docs onto pack paths, or CI alone — all end in the same local `check`. Confirms are human-only (TTY or `--i-am-human`). Research briefs never gate pass/fail. First moves: [60-second paths](docs/getting-started/60-second-paths.md).

**Compose, do not conquer:** Curbpack prepares structural evidence for product repos. Pair with SCA (e.g. Trivy/OSV) and secret scanners (e.g. Gitleaks) for depth — not a security program; watchlist = look-here, not a CVE product. Boundary: [strategy boundary](docs/strategy-boundary.md).

| Command | Purpose |
|---------|---------|
| *(bare)* | `doctor` if uninitialized, else `check` |
| `demo [--keep] [--open]` | Sandbox check; `--open` opt-in browser |
| `validate [--json]` | Pack gates (dual-rep); prefer `check` daily |
| `check --diff` | Delta mode — **not** release-gate safe |
| `ask [file] --propose` | Explain GateFailure JSON (propose-only) |
| `packs list\|update\|import\|export-graph\|doctor` | Packs, graph export, validity doctor |
| `export --sarif\|--explain-packet\|--watchlist-join\|--buyer-questions\|--lay-of-land\|--context-pack` | Standards / tutor packet / buyer checklist / map / ContextPack |
| `share` | Thin recipe: check → context-pack → buyer-questions → prepare-release |
| `pathway status` | One next ask (human default; `--technical` for phase path) |
| `pathway suggest\|note` | Warm-start seed + session notes ([pathway](docs/getting-started/pathway.md)) — not a gate input |
| `pathway confirm-*` | Human only — TTY or `--i-am-human` / `CURBPACK_ALLOW_CONFIRM=1` |
| `research [--fetch]\|--cite-check` | Allowlisted citation packet + human brief — never gates check |
| `completion bash\|zsh\|fish` | Print shell completions (`eval "$(curbpack completion bash)"`) |
| `sock` | Optional Unix IPC for integrators (continues if unused) |
| `init --bare` | Minimal scaffold (no hooks/skill/ide) |
| `init --packs a,b` | Override default house-policy packs |
| `init --workflow` | Opt-in: write `.github/workflows/curbpack.yml` if missing |

Exit codes: **0** pass · **1** gates/error · **2** usage/env.

Assistants (Cursor, Copilot, Claude, …): [docs/assistant-loop.md](docs/assistant-loop.md) · thin MCP [examples/mcp/](examples/mcp/).

Deep docs: [Intent vs Scope](docs/intent-vs-scope.md) · [For authorities](docs/for-authorities.md) · [Glossary](docs/glossary-and-audience.md) · [Pathway](docs/getting-started/pathway.md) · [Daily loop](docs/getting-started/daily-loop.md) · [Buyer evidence](docs/getting-started/buyer-evidence.md) · [Design partners](docs/design-partners.md) · [Write your own pack](docs/write-your-own-pack.md) · [Docs index](docs/README.md).

> **Optional, separate product:** Coreward is a private tutor/enforce client that may consume Curbpack explain-packets over an optional Unix socket. Curbpack is fully self-sustaining without it — adopters do not need Coreward. Brief architecture note (public Pages, not the private repo): https://afelin.github.io/coreward/
