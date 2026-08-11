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

## If Cursor says Paused

- Dirty files → “Commit my work” or “Discard my local changes” then sync again
- Login → open the GitHub/SSO link Cursor shows, then sync again
- Conflict → “Resolve the sync conflict for me” (Cursor merges; you only approve)

## Guardrails (Cursor follows these)

- Never force-push to `main` on either remote
- Feature work: new branch + PR on afelin; after merge, sync so RI-SE gets it
- Colleague work: they use RI-SE; you only **Sync both curbpack remotes**
