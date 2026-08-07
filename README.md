# CyberReady+

[![ci](https://github.com/afelin/cyberready/actions/workflows/ci.yml/badge.svg)](https://github.com/afelin/cyberready/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![cyberready-check](https://img.shields.io/badge/cyberready-check-2ea44f?logo=github)](https://github.com/afelin/cyberready)

Regulation-agnostic **evidence CLI**. Packs encode CRA, sector standards, or your house rules — the binary does not know any industry.

CyberReady prepares review packs for **humans**. It does **not** certify conformity, issue CE marks, or replace a notified body / auditor.

## Install (no Go)

```bash
curl -fsSL https://raw.githubusercontent.com/afelin/cyberready/main/scripts/install.sh | sh
cyberready doctor && cyberready demo
```

`demo` runs in a **temp git sandbox** — it never mutates your product working tree.

From source (maintainers):

```bash
git clone https://github.com/afelin/cyberready.git
cd cyberready && go build -o bin/cyberready ./cmd/cyberready
```

## 60-second paths

| Who | Path |
|-----|------|
| Human | `install.sh` → `doctor` → `demo` (or `init --packs house-policy` on your repo) |
| Agent | `init --skill --ide` → skill at `.cursor/skills/cyberready` → `check` / `--form-hints` |
| Decision-maker | Open `review-pack/buyer-onepager.html` or Action artifact — one screen, claim-safe |

Details: [docs/getting-started/60-second-paths.md](docs/getting-started/60-second-paths.md) · cold start: [house-policy](docs/getting-started/house-policy-cold-start.md)

## Quick start (your product repo)

```bash
cd /path/to/your/product   # must be a git repo

# Cold start (default): house-policy only
cyberready init --packs house-policy --hooks --skill --ide
cyberready check
cyberready check --form-hints          # deterministic propose-only stubs
# cyberready check --form-hints --apply-stub   # write missing stubs only
cyberready check --heal                     # hints → stub → re-check (max 3; never attest)

# Opt-in regimes
cyberready init --packs cra-baseline
cyberready init --packs cra-baseline,medtech-iec62304
```

Deprecated: `init --medtech` → `--packs cra-baseline,medtech-iec62304`.

## GitHub Action

```yaml
# .github/workflows/cyberready.yml
permissions:
  contents: read
  pull-requests: write
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: afelin/cyberready@main   # pin a tag in production
        with:
          comment_pr: "true"
```

Posts a sticky PR comment (thermometer + top fails + disclaimer) and uploads `buyer-onepager` when present. Example: [examples/workflows/cyberready-check.yml](examples/workflows/cyberready-check.yml).

## Commands

| Command | Purpose |
|---------|---------|
| `doctor` | PATH / git / packs / hooks confidence |
| `demo [--keep]` | Safe sandbox: temp git + house-policy check + one-pager |
| `init [--packs a,b] [--hooks] [--skill] [--ide]` | Config, stubs, hook, Cursor skill, VS Code tasks |
| `check [--diff] [--json] [--form-hints] [--apply-stub] [--heal]` | Daily loop; `--heal` = hints→stub→re-check (max 3) |
| `validate [--delta]` | Pack gates → GateFailure JSON + semantic markdown |
| `prepare-release` | `review-pack/` + CycloneDX/VEX under `.github/cyberready/evidence/` |
| `packs list\|update\|import` | Embedded packs; update/import helpers |
| `ask [file] [--propose]` | Explain GateFailure JSON (propose-only) |
| `attest` | Reproducible Git Notes capsule; binds SBOM/VEX digests |
| `view` | Show capsule for HEAD |
| `sock` | Optional `validate_delta` Unix server for Coreward |

## Config

`.cyberready.json`:

```json
{
  "packs": ["house-policy"],
  "hooks": true,
  "claim": "Prepares evidence for human review — not a conformity assessment."
}
```

## Packs

| Pack | Intent |
|------|--------|
| `house-policy` | Internal: `SECURITY.md`, `security.txt`, banned deps, secret forbids (**cold-start default**) |
| `cra-baseline` | EU CRA Annex VII–style evidence gates |
| `medtech-iec62304` | IEC 62304–inspired lifecycle docs |

Write your own: [docs/write-your-own-pack.md](docs/write-your-own-pack.md).

## Evidence

- **CycloneDX 1.5** JSON from `package-lock.json` / `pnpm-lock.yaml` / `package.json`
- **Pending OpenVEX** drafts from gate findings (`draft_pending_attest`)
- **Attest** hashes `commit|parent|sbom|vex` — no wall-clock in the state hash
- **HPURL** `proof/index.html` verifies `h=` against `.github/cyberready/evidence/hpurl-pointer.json`

## Adoption (OSS flywheel)

- Scoreboard artifact on `main`: `.github/workflows/scoreboard.yml`
- Weekly claim-safe Discussion: `.github/workflows/weekly-discussion.yml`
- Social copy + badge: [docs/gtm-oss/](docs/gtm-oss/)
- Tester issue template: `.github/ISSUE_TEMPLATE/tester_report.yml`

No spam bots / auto-DM. Humans post from templates.

## Claim safety

Do not market gate pass as certification, CE marking, or notified-body approval.
CI enforces this via `scripts/claim-safety.sh` (docs + runtime captures).

## Launch readiness

See [docs/launch-readiness.md](docs/launch-readiness.md) for required checks, heal semantics, Discussions welcome, and Tier-3 human pass before invite wave.

## License

Apache-2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE). Security reports: [SECURITY.md](SECURITY.md).
