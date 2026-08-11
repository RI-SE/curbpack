# 60-second paths

CyberReady checks your repository against local rule packs and writes a review pack you can hand to a buyer or auditor—on your machine, without claiming certification.

Not conformity assessment. Not CE marking. Not a notified-body opinion.

Cold-start default pack: **`house-policy`**. CRA / medtech are opt-in later via `--packs` (Advanced). Pick **exactly one** first move for your audience.

## Three ways in

Same local `check` for all three — Write adds optional draft choice first; Bring and CI go straight to check.

| Way | What you do |
|-----|-------------|
| **Write→Check** | Optional [pathway](pathway.md) interview that suggests checklists → confirm packs (TTY or `--i-am-human`) → optional research brief → two drafts + Recommended A\|B → you pick → cite-check (refuses uncited Claims) → `check`. |
| **Bring-docs→Check** | Place existing policies on pack paths (or point a custom pack JSON at your paths), then `check`. No portal PDF ingest. |
| **CI** | Action-only (or local `check` alone). Pin **`@v0.4.3`**. |

Builders site: [Three ways in](../../site/for-builders/). Write depth: [pathway](pathway.md).

## Human — safe try

Under ten minutes (pin **`@v0.4.3`**): `install.sh` → `doctor` → `demo`. Gate green ≠ certification.

```bash
curl -fsSL https://raw.githubusercontent.com/afelin/cyberready/main/scripts/install.sh | sh
cyberready doctor
cyberready demo                          # sandbox green + one-pager path (no browser)
# cyberready demo --open                 # opt-in: open the one-pager in the OS browser
```

## Human — product repo

```bash
cd my-product
cyberready init                          # house-policy + hooks + skill + ide
cyberready check                         # or bare: cyberready
```

## Agent

```bash
cyberready init                          # skill lands at .cursor/skills/cyberready/SKILL.md
cyberready check
cyberready check --form-hints            # propose-only snippets
# optional: cyberready check --form-hints --apply-stub   # write missing stubs only
```

Agent rule: after doc/dep edits, re-run `check`. Prefer `export --context-pack`. Never claim certification. Full contract: [assistant-loop](../assistant-loop.md) (Cursor / Copilot / Claude / others).

## CI-only

**Action-only path** (no local install required):

1. Copy [`examples/workflows/cyberready-check.yml`](../../examples/workflows/cyberready-check.yml) → `.github/workflows/cyberready.yml`.
2. Push / open a PR. Pin stays **`@v0.4.3`**. Minimal permissions: `contents: read`, `pull-requests: write`, `security-events: write`.
3. Expect: uninitialized repos resolve **`house-policy`**; with `heal: true`, missing stubs are written; green sticky once, or red with heal stubs + top-3 ask pointer — still felt value. Claim-safe: gate pass ≠ certification.

Optional local equivalent: `cyberready init --workflow` writes the same drop-in workflow **only if missing** (never overwrites; not enabled by default `init`).

Local Action-equivalent smoke: temp git repo **without** `.cyberready.json` → `cyberready check --heal` → exit 0 (or deterministic red after stubs if content gates remain).

Maintainer bar: `./scripts/time-to-green.sh` (demo + init→check wall-clock; fail if &gt;10 min).

## Decision-maker

1. Open the supplier’s `review-pack/buyer-onepager.html` (from `prepare-release` or the Action artifact), or the committed sample at `site/samples/onepager.html`.
2. Or open the proof page (`proof/index.html`) with a hash fragment.
3. One screen: local gate score, top gaps, disclaimer — no account required. Not a certificate.

Runs deposit cache + review-pack under `.github/cyberready/`; attest when a human is ready.

## Advanced

Habit after first green: [daily loop](daily-loop.md). Optional share: [buyer evidence](buyer-evidence.md) (`export --lay-of-land` / `--buyer-questions`). Doctor soft-exit tips and binary size notes: README Advanced.

| Flag / path | When |
|-------------|------|
| `cyberready init --bare` | Minimal scaffold (no hooks/skill/ide) |
| `cyberready init --packs a,b` | Override default house-policy |
| `cyberready init --workflow` | Opt-in drop-in Action `@v0.4.3` workflow if missing |
| `cyberready demo --open` | Opt-in browser for the sandbox one-pager |
