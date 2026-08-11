# Sync both curbpack remotes

Run `./scripts/curb-sync.sh` from the repo root. Do not force-push. If exit 2, explain in plain English and offer: commit WIP, resolve conflict, or authorize GitHub SSO for RI-SE.

Never `git push --force` or `--force-with-lease` to `main` on either remote. Never create `backup/*` on GitHub. Feature work stays on a branch + PR on **afelin**; after merge, run this sync so RI-SE gets it.
