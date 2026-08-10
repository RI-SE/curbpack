# CyberReady site (GitHub Pages)

Static explainer for https://afelin.github.io/cyberready/

Deploy via `.github/workflows/pages.yml` (Actions → Pages). Enable **GitHub Pages → Source: GitHub Actions** in repo settings if the site 404s.

Pilot pin: `@v0.4.3` (current instrument-panel honesty cut). Adversarial grade: `scripts/redteam-pilot.sh`. Trust-surface freeze through v0.4.x: see `docs/security-model.md`.

## Contents

Public IA only: home, how-it-works, for-builders, for-reviewers, for-authorities, security, whitepaper, samples, `llms.txt` (agent index).

Home uses a neo-brutalist Tailwind CDN layout (grid, hard borders, ink/paper). Subpages share the same tokens via `assets/site.css` (no Tailwind CDN on subpages).

## Link rule

Internal HTML navigation and asset `href`s use **site-root-relative** `/cyberready/…` paths (not `../` or bare `samples/…`). That matches GitHub project Pages and works with or without trailing slashes on the page URL.

## Ops quarantine

Do **not** deploy or link from Pages:

- `docs/gtm-oss/` (social/launch copy)
- Launch invite checklists / unfixed exploit writeups
- Internal CI runbooks

Claim-safety applies to site HTML copy the same as docs.

## Local preview

Serve under a `/cyberready/` base so root-relative links resolve like production:

```bash
rm -rf /tmp/cr-pages && mkdir -p /tmp/cr-pages && cp -R site /tmp/cr-pages/cyberready
python3 -m http.server -d /tmp/cr-pages 8080
# open http://localhost:8080/cyberready/
```
