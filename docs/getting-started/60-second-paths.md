# 60-second paths

Curbpack checks your repository against local rule packs and writes a review pack you can hand to a buyer or auditor—on your machine, without claiming certification.

Not conformity assessment. Not CE marking. Not a notified-body opinion.

## Scan-first (fastest)

Install release **`v0.5.4`** once, then scan inside any git repository. `scan` does not initialize Curbpack or write files.

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

On an uninitialized repository, `scan` uses `cra-baseline`. For the first-run tryout, stop after the scan. To continue later, run `curbpack fix --art14`, `curbpack init`, and `curbpack check --score` in that order.

## Choose a working path

Write, Bring, and CI use the same local `check` result.

| Way | What you do |
|-----|-------------|
| **Write → Check** | Use the optional [pathway](pathway.md) to choose packs and prepare grounded drafts with human confirmation, then run `check`. |
| **Bring docs → Check** | Place existing policies at the configured pack paths, or point a custom pack at those paths, then run `check`. Portal PDF ingestion is not supported. |
| **CI** | Run the Action or a local `check`. Pin the Action to **`@v0.5.2`**; Action runners are Linux and macOS. |

Builders site: [Three ways in](../../site/for-builders/). Install hub: [install](install.md) · [troubleshooting](troubleshooting.md). Write depth: [pathway](pathway.md).

## Try the demo

After installation, run `doctor` and the isolated demo. A green demo is not certification. See [install](install.md) for the complete installation options.

```bash
curbpack doctor
curbpack demo                          # sandbox green + one-pager path (no browser)
# curbpack demo --open                 # opt-in: open the one-pager in the OS browser
```

## Use Curbpack in a product repository

```bash
cd my-product
curbpack init                          # house-policy default; --profile cra|medtech
curbpack check                         # or bare: curbpack / curb
curbpack share                         # optional --bundle
# human when ready: curbpack attest → proof/index.html
```

If `check` is red, run `curbpack check --heal`, then `curbpack ask … --propose`, and re-run `check`. After the first green result, `curbpack share` prepares the review pack and buyer one-pager. `curbpack drift` is an optional informational checklist and always exits 0.

## Agent

```bash
curbpack init                          # skill lands at .cursor/skills/curbpack/SKILL.md
curbpack check
curbpack check --form-hints            # propose-only snippets
# optional: curbpack check --form-hints --apply-stub   # write missing stubs only
```

After documentation or dependency edits, an agent must re-run `check`. On red, use heal and propose-only guidance, then re-check. On green, use `share` or `export --context-pack`. The [assistant loop](../assistant-loop.md) defines the complete contract for Cursor, Copilot, Claude, and other assistants.

## CI-only

**Action-only path** (no local install required):

1. Copy [`examples/workflows/curbpack-check.yml`](../../examples/workflows/curbpack-check.yml) → `.github/workflows/curbpack.yml`.
2. Push / open a PR. Pin stays **`@v0.5.2`**. Action = Linux/macOS only. Minimal permissions: `contents: read`, `pull-requests: write`, `security-events: write`.
3. On an uninitialized repository, the Action selects **`house-policy`**. `heal` defaults to **false**; set `heal: true` to write missing stubs. Generated scaffold remains red until replaced with product-specific content. Stubs do not establish readiness, and a gate pass is not certification.

Optional local equivalent: `curbpack init --workflow` writes the same drop-in workflow **only if missing** (never overwrites; not enabled by default `init`).

Local Action-equivalent smoke: temp git repo **without** `.curbpack.json` → `curbpack check --heal` → deterministic exit 1 with anti-placeholder failures after writing stubs.

Maintainer bar: `./scripts/time-to-green.sh` (demo + init→check wall-clock; fail if &gt;10 min).

## Decision-maker

1. Open the supplier’s `review-pack/buyer-onepager.html` (from `prepare-release` or the Action artifact), or the committed sample at `site/samples/onepager.html`.
2. Or open the proof page (`proof/index.html`) with a hash fragment.
3. Review the local gate score, highest-priority gaps, and disclaimer on one screen. No account is required, and the page is not a certificate.

Runs deposit cache + review-pack under `.github/curbpack/`; attest when a human is ready.

## Advanced

Habit after first green: [daily loop](daily-loop.md). Optional share: [buyer evidence](buyer-evidence.md) (`export --lay-of-land` / `--buyer-questions`). Doctor soft-exit tips and binary size notes: README Advanced.

| Flag / path | When |
|-------------|------|
| `curl …/main/scripts/install.sh \| sh` then `curbpack scan` | Read-only first contact; scan defaults to **cra-baseline** |
| `curbpack init --bare` | Minimal scaffold (no hooks/skill/ide) |
| `curbpack init --packs a,b` | Override init default **house-policy** |
| `curbpack init --workflow` | Opt-in drop-in Action `@v0.5.2` workflow if missing |
| `curbpack demo --open` | Opt-in browser for the sandbox one-pager |
| `npx curbpack` (deferred) | npm wrapper not on stranger path until PR5 ships |
