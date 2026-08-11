# Curbpack site (GitHub Pages)

Static explainer for https://afelin.github.io/curbpack/

Deploy via `.github/workflows/pages.yml` (Actions → Pages). Enable **GitHub Pages → Source: GitHub Actions** in repo settings if the site 404s.

Pilot pin: `@v0.5.0` (current instrument-panel honesty cut). Adversarial grade: `scripts/redteam-pilot.sh`. Trust-surface freeze through v0.4.x: see `docs/security-model.md`.

## Contents

Public IA only: home, how-it-works, for-builders, for-reviewers, for-authorities, security, whitepaper, samples, `llms.txt` (agent index).

Home uses a neo-brutalist Tailwind CDN layout (grid, hard borders, ink/paper). Subpages share the same tokens via `assets/site.css` (no Tailwind CDN on subpages).

## Page map

| Page | Audience | Story |
|------|----------|--------|
| `index.html` | Anyone | Primary sentence, plain ladder, **three ways in** chips (Write / Bring / CI), CTA **Pick how you start** |
| `how-it-works/` | Anyone | Same three ways → stages (Write adds draft choice) → local check → review pack → human review |
| `for-builders/` | Builders | Install / init / check; Write HITL line; Bring; CI pin `@v0.5.0`; **Daily loop** (`curb` alias, heal/ask, share, attest/proof) |
| `for-reviewers/` | Buyers / reviewers | Buyer one-pager + trust table; research brief demoted (supplier writer aid) |
| `for-authorities/` | CISO / auditors | Structural evidence for human review; not conformity assessment |
| `samples/onepager.html` | Reviewers / teaching | Buyer one-pager sample; Sources informational ≠ gate input |
| `samples/research-brief.html` | Builders (optional) | Allowlisted research brief sample — never a gate input |
| `whitepaper/` | Deep readers | Intent / loop / trust / non-claims |
| `security/` | Builders / CISO | Trust surface pointer |
| `llms.txt` | Agents | Machine-readable index |

Nav on every public page: Builders | Reviewers | Authorities | How it works. Footer: RISE line + optional Coreward one-liner only.

## Link rule

Internal HTML navigation and asset `href`s use **site-root-relative** `/curbpack/…` paths (not `../` or bare `samples/…`). That matches GitHub project Pages and works with or without trailing slashes on the page URL.

## Ops quarantine

Do **not** deploy or link from Pages:

- `docs/gtm-oss/` (social/launch copy)
- Launch invite checklists / unfixed exploit writeups
- Internal CI runbooks

Claim-safety applies to site HTML copy the same as docs.

## Local preview

Serve under a `/curbpack/` base so root-relative links resolve like production:

```bash
rm -rf /tmp/cr-pages && mkdir -p /tmp/cr-pages && cp -R site /tmp/cr-pages/curbpack
python3 -m http.server -d /tmp/cr-pages 8080
# open http://localhost:8080/curbpack/
```
