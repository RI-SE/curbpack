# Maintainer playbook — cut `v0.5.2` after PR #57

**Do not advertise pin `@v0.5.2` as live until release assets exist** (including `curbpack_windows_amd64.exe` and `checksums.txt`). Merge alone is not enough.

Ordered steps (humans only — agents stop before merge/tag/release):

1. **Merge PR #57** to `main` with a **merge commit** (not squash-only if you need a single merge SHA for the tag).
2. **Immediately** push annotated tag `v0.5.2` on that merge SHA:
   ```bash
   git fetch origin main
   git tag -a v0.5.2 <merge-sha> -m "v0.5.2 Cross-OS TAM"
   git push origin v0.5.2
   ```
3. **Wait** for `.github/workflows/release.yml` to publish **all** assets, including `curbpack_windows_amd64.exe` and `checksums.txt`.
4. **Verify** asset list matches the install manifest:
   ```bash
   gh release view v0.5.2
   # compare names to scripts/install-manifest.json
   ```
5. **Smoke** installers against the tag (no workspace binary fallback):
   ```bash
   # macOS/Linux — isolated PATH
   curl -fsSL https://raw.githubusercontent.com/afelin/curbpack/v0.5.2/scripts/install.sh | sh
   # Windows PowerShell — same pin
   # irm …/v0.5.2/scripts/install.ps1 | iex
   curbpack doctor && curbpack demo
   ```
6. **Sync both** curbpack remotes via `./scripts/curb-sync.sh` only (never force-push). Phrase: “sync both curbpack remotes” — see [sync-both-remotes](sync-both-remotes.md).
7. **Optional:** if https://ri-se.github.io/curbpack/ 404s, enable RI-SE Pages (GitHub Actions source) per [sync-both-remotes](sync-both-remotes.md#if-the-ri-se-site-404s-again).

## Warn

- Pin copy in README/Action examples may already say `@v0.5.2` on the branch — that is **aspirational until step 4 passes**.
- Do **not** run curb-sync or cut the tag from a feature tip before merge.
- Do **not** treat chat green as a release gate; re-check locally after install smoke.
