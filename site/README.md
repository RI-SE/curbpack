# Curbpack site (GitHub Pages)

Static explainer for **https://ri-se.github.io/curbpack/** (credibility home). Optional mirror: https://afelin.github.io/curbpack/

Deploy via `.github/workflows/pages.yml` (Actions → Pages) on **both** remotes after sync. Enable **GitHub Pages → Source: GitHub Actions** on [RI-SE/curbpack](https://github.com/RI-SE/curbpack/settings/pages) if the site 404s — or ask Cursor: **Enable the curbpack site on RI-SE**. See [sync both remotes](../docs/getting-started/sync-both-remotes.md).

Pilot pin: `@v0.5.2` (current instrument-panel honesty cut). Adversarial grade: `scripts/redteam-pilot.sh`. Trust-surface freeze through v0.4.x: see `docs/security-model.md`.

## Contents

Public IA only: home, how-it-works, for-builders, for-reviewers, for-authorities, security, whitepaper, samples, `llms.txt` (agent index).

Home uses a neo-brutalist Tailwind CDN layout (grid, hard borders, ink/paper). Subpages share the same tokens via `assets/site.css` (no Tailwind CDN on subpages).

## Page map

| Page | Audience | Story |
|------|----------|--------|
| `index.html` | Anyone | Primary sentence, curb outlines + local pack→rule map, three ways in, quickstart CTA |
| `how-it-works/` | Anyone | End-to-end sequence: three ways → artifacts → interpret results → human review |
| `for-builders/` | Builders | Install / init / check; three ways in; artifacts; interpret results; daily loop |
| `for-reviewers/` | Buyers / reviewers | Buyer one-pager + trust table; research brief demoted (supplier writer aid) |
| `for-authorities/` | CISO / auditors | Structural evidence for human review; not conformity assessment |
| `samples/onepager.html` | Reviewers / teaching | Buyer one-pager sample; Sources informational ≠ gate input |
| `samples/research-brief.html` | Builders (optional) | Allowlisted research brief sample — never a gate input |
| `whitepaper/` | Deep readers | Capability matrix, evidence flow, curb outlines / pathway, trust / non-claims |
| `security/` | Builders / CISO | Trust surface pointer |
| `llms.txt` | Agents | Machine-readable index |

**Nav/Footer (every public page):** Builders | Reviewers | Authorities | Art 14 (where present) | How it works | **Source** (`https://github.com/afelin/curbpack`, title: canonical module/releases/Action) | **RISE mirror** (`https://github.com/RI-SE/curbpack`). Footer: **Source: afelin/curbpack · RISE mirror: RI-SE/curbpack** + Pages link + RISE funder line. Duplicate the same chrome snippet across static HTML pages (no SSG/partials).

**Metadata rule:** Never put a day count in `<title>`, `og:title`, `og:description`, `<meta description>`, or `og:image` artwork — use the date only (e.g. **11 September 2026**). Social cards and search snippets are cached and never run JS; a countdown baked into metadata or image text freezes and goes wrong silently.

**Post-merge card check:** After deploy, open the live URL logged out on a phone; paste into Slack and LinkedIn to confirm the card renders. Meta tags can be correct in page source while previews stay wrong (CDN/cache lag or missing/broken image URL).

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
