# CyberReady+

Regulation-agnostic **evidence CLI**. Packs encode CRA, sector standards, NIS2-style baselines, or your house rules — the binary does not know any industry.

CyberReady prepares review packs for **humans**. It does **not** certify conformity, issue CE marks, or replace a notified body / auditor.

## Why

- One lean Go binary (stdlib-only), offline, no SaaS, no Coreward required
- Policy change = pack JSON (or air-gap `packs import`), not a Go fork
- Daily loop: `cyberready check` → gate cache + Action Report
- Release boundary: CycloneDX 1.5 SBOM, pending OpenVEX, reproducible attest, HPURL verify

## Install

```bash
git clone https://github.com/afelin/cyberready.git
cd cyberready
go build -o bin/cyberready ./cmd/cyberready
```

## Quick start (offline)

```bash
cd /path/to/your/product/repo   # must be a git repo

# Pack-first init (compose regimes)
./bin/cyberready init --packs cra-baseline
# or house-only:
./bin/cyberready init --packs house-policy --hooks
# or stack (CRA + medtech overlay):
./bin/cyberready init --packs cra-baseline,medtech-iec62304

./bin/cyberready check          # validate + thermometer + cache + Action Report
./bin/cyberready check --diff   # skip rules whose paths are untouched by git diff
./bin/cyberready prepare-release
open review-pack/buyer-onepager.html
```

Deprecated: `init --medtech` still works as an alias for `--packs cra-baseline,medtech-iec62304`.

Edit only the files your active packs reference (e.g. `docs/annex-vii/*.md` or `SECURITY.md`), remove placeholders, then re-run `check`.

## Commands

| Command | Purpose |
|---------|---------|
| `init --packs a,b [--hooks]` | `.cyberready.json`, pack-path stubs, optional pre-commit → `check` |
| `check [--diff] [--json]` | Daily muscle memory: validate + cache + Action Report |
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
  "packs": ["cra-baseline", "house-policy"],
  "hooks": true,
  "claim": "Prepares evidence for human review — not a conformity assessment."
}
```

## Packs

Embedded examples (equal citizens):

| Pack | Intent |
|------|--------|
| `cra-baseline` | EU CRA Annex VII–style evidence gates |
| `medtech-iec62304` | IEC 62304–inspired lifecycle docs |
| `house-policy` | Internal: `SECURITY.md`, `security.txt`, banned deps, secret forbids |

Write your own: [docs/write-your-own-pack.md](docs/write-your-own-pack.md).

## Evidence

- **CycloneDX 1.5** JSON from `package-lock.json` / `pnpm-lock.yaml` / `package.json`
- **Pending OpenVEX** drafts from gate findings (status `draft_pending_attest`)
- **Attest** hashes `commit|parent|sbom|vex` — no wall-clock in the state hash
- **HPURL** `proof/index.html` verifies `h=` against `.github/cyberready/evidence/hpurl-pointer.json` client-side

## HPURL

Fragment contract:

```text
#?h=<state_hash>&p=<commit_or_pointer>&s=<signature_or_token>
```

Optional Coreward aliases: `run`, `capsule`, `vows`.

## Claim safety

Do not market gate pass as certification, CE marking, or notified-body approval.

## License

Apache-2.0
