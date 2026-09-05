# Curbpack

> **Source:** [RI-SE/curbpack](https://github.com/RI-SE/curbpack) contains the code, releases, and documentation. Development is supported by RISE as an applied research / competence object; see the [NOTICE](NOTICE). RISE does not certify products that use Curbpack gate results. The GitHub Action remains pinned to **`RI-SE/curbpack@v0.5.2`** until the next human tabletop permits a version bump; see the [release gate](scripts/release-gate.json).

[![ci](https://github.com/RI-SE/curbpack/actions/workflows/ci.yml/badge.svg)](https://github.com/RI-SE/curbpack/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Curbpack checks your repository against local rule packs and writes a review pack you can hand to a buyer or auditor—on your machine, without claiming certification.

> Not conformity assessment. Not CE marking. Not a notified-body opinion.

[Site](https://ri-se.github.io/curbpack/) · [RI-SE/curbpack](https://github.com/RI-SE/curbpack) · [White paper](papers/curbpack-whitepaper.md) · [Voice and terms](docs/voice-and-terms.md) · [For builders](site/for-builders/) · [Art 14 scan](site/art14/) · [Docs index](docs/README.md)

## Release status

The installer currently supplies **v0.5.5** (high-trust launch tip). See the [launch status and audit limitations](docs/launch-status.md) before using results for an audit decision. Action pin stays `@v0.5.2`.

## Start with a read-only scan

[Article 14 incident-reporting obligations](https://eur-lex.europa.eu/eli/reg/2024/2847/oj/eng) apply from **11 September 2026**. Install Curbpack, change to any git repository, and run `scan`. This first step writes no files.

**macOS / Linux**

```bash
curl -fsSL https://raw.githubusercontent.com/RI-SE/curbpack/main/scripts/install.sh | sh
cd /path/to/your/git/repo
curbpack scan
```

**Windows (PowerShell)**

```powershell
irm https://raw.githubusercontent.com/RI-SE/curbpack/main/scripts/install.ps1 | iex
cd C:\path\to\your\git\repo
curbpack scan
```

`scan` defaults to **`cra-baseline`** and prints the Article 14 reporting clock. Exit 0 means diagnosis completed; findings may remain. Use `curbpack check` when you need repository gate pass/fail. See [troubleshooting](docs/getting-started/troubleshooting.md) if the command is unavailable.

## Choose the relevant guide

| You are | Start here |
|---------|------------|
| **Supplier / builder** | [For builders](site/for-builders/) · [Share handoff](docs/getting-started/share-handoff.md) · [Install](docs/getting-started/install.md) |
| **Buyer / reviewer** | [For reviewers](site/for-reviewers/) · [Buyer evidence](docs/getting-started/buyer-evidence.md) · [Sample one-pager](site/samples/onepager.html) |
| **Authority / auditor** | [For authorities](docs/for-authorities.md) · [Site for authorities](site/for-authorities/) |

For the complete system, read the [white paper](papers/curbpack-whitepaper.md) and [how it works](site/how-it-works/). Definitions are in the [glossary and audience guide](docs/glossary-and-audience.md).

## Continue to the full workflow

After installation, the same workflow applies on every supported OS. `curb` is a short alias for `curbpack`.

```bash
curbpack doctor
curbpack demo              # sandbox; optional --open
cd /path/to/your/product   # git repo
curbpack scan              # read-only diagnosis — no init, no hooks, no score
curbpack fix --art14       # one Art 14 rehearsal file (diff preview; human confirm)
curbpack share             # optional --bundle; --reveal opens review-pack in Explorer/Finder
curbpack init              # when ready: house-policy default; --profile cra|medtech
curbpack check --score     # daily loop — exit code is authoritative
# human only when ready:
curbpack attest
# verify: proof/index.html vs hpurl-pointer.json
```

`curbpack ask-my-suppliers` emits the same buyer checklist as `export --buyer-questions`. On red: `curbpack check --heal` then `curbpack ask .github/curbpack/cache/latest_failure.json --propose`, then re-check. Optional drift checklist: `curbpack drift` (exit 0 always). After OS update / PATH loss: `curbpack doctor --repair` (local only — not auto-update; Windows also: `install.ps1 -Repair`).

Write, Bring, and CI all end in the same local `check`. Write can add optional pathway drafts first; Bring and CI proceed directly to checks. Compare the paths in [60-second paths](docs/getting-started/60-second-paths.md) or read the [pathway guide](docs/getting-started/pathway.md).

## What you get

| Artifact | When | What it is |
|----------|------|------------|
| **Gate report** | Every `check` | JSON + markdown findings—structural evidence, not a legal finding |
| **Review pack** | `prepare-release` or `share` | Layered reports for human review |
| **Buyer one-pager** | After green + `share` | Supplier evidence summary HTML you hand to a buyer |
| **Evidence bundle** | `share --bundle` | Offline `review-pack/evidence-bundle.html` with embedded hpurl pointer |
| **Reveal / Attach** | `share --reveal` | Opens review-pack (or bundle) in Explorer/Finder; stdout `Attach: <abs path>` on every OS |
| **Drift checklist** | `curbpack drift` | Multi-signal human checklist (exit 0; not a compliance meter) |
| **Attest capsule** | Human `attest` when ready | Git Notes hash bind—**unsigned ≠ verified** |
| **Proof page** | After attest | Local `proof/index.html` vs evidence pointer—still human judgment |

Optional exports: SARIF, ContextPack, buyer-questions, lay-of-land. Teaching sample: [site/samples/onepager.html](site/samples/onepager.html).

## How to interpret results

| Signal | Meaning |
|--------|---------|
| Exit **0** on **`check`** | Gates passed on this tree—for human review, not certification |
| Exit **0** on **`scan`** | Diagnosis completed (findings may remain); not a gate pass |
| Exit **0** on **`doctor`** | Environment report finished; advisory issues do not mean gate failure |
| Exit **1** | Gate findings remain or operational error (typically `check`) |
| Exit **2** | Usage / environment (unknown command, not a git repo when required) |
| **Unsigned** attest | Capsule present; **not cryptographically verified** |
| **ssh-agent-signed** | Real SSH signature produced |

Gate pass is **not** certification, CE marking, or notified-body approval. Humans decide what to claim. Only **`check`** provides repository gate pass/fail.

## GitHub Action

Action runners are **Linux/macOS only** (local Windows CLI is supported separately).

```yaml
- uses: RI-SE/curbpack@v0.5.2
  with:
    heal: "true" # opt-in; Action default is false (scaffold ≠ readiness)
    comment_on: red
    upload_sarif: "true"
```

Pin **`@v0.5.2`**. Drop-in example: [`examples/workflows/curbpack-check.yml`](examples/workflows/curbpack-check.yml). Pilot deploy: `./scripts/redteam-pilot.sh`.

## Advanced

Binary size (~10 MB, Go CGO=0 `-s -w`), doctor soft-exit tips, and Zig non-goals live here—not on the first screen.

Curbpack prepares structural evidence for product repositories. It does not replace software composition analysis or secret scanning; use dedicated tools such as Trivy, OSV, or Gitleaks for those checks. See the [strategy boundary](docs/strategy-boundary.md).

Confirms are human-only (`--i-am-human` or `CURBPACK_ALLOW_CONFIRM=1`; TTY alone is not enough). Research briefs never gate pass/fail. Assistants: [docs/assistant-loop.md](docs/assistant-loop.md) · thin MCP [examples/mcp/](examples/mcp/).

| Command | Purpose |
|---------|---------|
| *(bare)* | `doctor` if uninitialized, else `check` |
| `demo [--keep] [--open]` | Sandbox check; `--open` opt-in browser |
| `validate [--json]` | Pack gates (dual-rep); prefer `check` daily |
| `check --diff` | Delta mode — **not** release-gate safe |
| `ask [file] --propose` | Explain GateFailure JSON (propose-only) |
| `packs list\|update\|import\|export-graph\|doctor` | Packs, local pack→rule map export (drafting graph via `export-graph`), validity doctor |
| `export --sarif\|--explain-packet\|--watchlist-join\|--buyer-questions\|--lay-of-land\|--context-pack` | Standards / tutor packet / buyer checklist / map / ContextPack |
| `share` | Thin recipe: check → context-pack → buyer-questions → prepare-release |
| `review [--repo] [--json] [--full] [--since] [--verify-chain]` | Offline document triage (received pack or in-repo); `--edges` ingest-only / integrators (`--repo --json` only) |
| `pathway status` | One next ask (human default; `--technical` for phase path) |
| `pathway suggest\|note` | Warm-start seed + session notes — not a gate input |
| `pathway confirm-*` | Human only — `--i-am-human` or `CURBPACK_ALLOW_CONFIRM=1` |
| `research [--fetch]\|--cite-check` | Allowlisted citation packet + human brief — never gates check |
| `completion bash\|zsh\|fish` | Print shell completions |
| `init --bare` | Minimal scaffold (no hooks/skill/ide) |
| `init --packs a,b` | Override default house-policy packs |
| `init --workflow` | Opt-in: write `.github/workflows/curbpack.yml` if missing |

Deep docs: [Intent vs Scope](docs/intent-vs-scope.md) · [Security model](docs/security-model.md) · [Write your own pack](docs/write-your-own-pack.md) · [Migration](docs/migration-cyberready-to-curbpack.md) · [Adopters](ADOPTERS.md) · [Shared Frame](docs/shared-frame.md) (CTAM Mapper seam; residual claim-linking is Mapper-owned) · [Claim discipline](docs/claim-discipline.md)

Claim-safe wording enforced by `scripts/claim-safety.sh`. Preferred public language: [docs/voice-and-terms.md](docs/voice-and-terms.md).
