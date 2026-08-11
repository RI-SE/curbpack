# Sync both curbpack remotes

Keep **afelin** and **RI-SE** `main` matching. You never run git — say one phrase to Cursor.

## When to say it

- Start of a Cursor session
- After your colleague says they merged on RI-SE
- After Cursor merged your PR on afelin and you want RI-SE updated

## Exact phrase

> Sync both curbpack remotes

## Success looks like

> Both remotes match (`abc1234`)

## Public site (credibility home)

Primary public URL (org project Pages; hostname is lowercase `ri-se`):

- **https://ri-se.github.io/curbpack/**
- Optional mirror: https://afelin.github.io/curbpack/

Hosting under RI-SE is for credibility. RISE remains a **funder / applied-research supporter**, not a product certifier — same fence as [voice and terms](../voice-and-terms.md).

Project Pages use base path `/curbpack/` (repo name). Site HTML already uses `/curbpack/…` hrefs on both remotes. Deploy source: **GitHub Actions** via `.github/workflows/pages.yml`.

### If the RI-SE site 404s again

Say:

> Enable the curbpack site on RI-SE

Or click:

1. Open [RI-SE/curbpack → Settings → Pages](https://github.com/RI-SE/curbpack/settings/pages)
2. Under **Build and deployment → Source**, choose **GitHub Actions**
3. Ask Cursor: **Sync both curbpack remotes**, then [Actions → github-pages](https://github.com/RI-SE/curbpack/actions/workflows/pages.yml) → **Run workflow**

(Cursor needs an org-accepted OAuth token with admin; fine-grained PATs with long lifetime are often blocked by RI-SE org policy.)

## If Cursor says Paused

- Dirty files → “Commit my work” or “Discard my local changes” then sync again
- Login → open the GitHub/SSO link Cursor shows, then sync again
- Conflict → “Resolve the sync conflict for me” (Cursor merges; you only approve)
- Site still 404 after enable → “Deploy the curbpack Pages workflow on RI-SE”

## Guardrails (Cursor follows these)

- Never force-push to `main` on either remote
- Feature work: new branch + PR on afelin; after merge, sync so RI-SE gets it
- Colleague work: they use RI-SE; you only **Sync both curbpack remotes**
- Prefer linking **https://ri-se.github.io/curbpack/** as the primary public site; keep afelin as optional mirror
