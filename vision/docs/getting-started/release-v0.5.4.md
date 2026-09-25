# Maintainer playbook — cut `v0.5.4` (first-run honesty)

**Fail-closed order:** tag honesty SHA → verify assets → smoke with `CURBPACK_VERSION=v0.5.4` → **then** bump `main` defaults. Do not advertise the binary on `main` until tag-smoke passes.

**Public SoR:** tag and release on **RI-SE only**. Do **not** cut a public `v0.5.4` tag on afelin. Action pin stays **`@v0.5.2`**.

## Anti-patterns (do not)

| Anti-pattern | Why |
|--------------|-----|
| Smoke **after** bump only | Broken binary can be advertised on `main` |
| Recommend `…/v0.5.4/scripts/install.sh` | Tag tree still has `MANIFEST_DEFAULT=v0.5.3` → silent downgrade |
| Matching public tag on afelin | Confuses provenance; strangers use RI-SE |
| HTTP 200 without end-to-end install smoke | Asset present ≠ checksum/install works |
| Leave `buildinfo.Version` at `0.5.2` | Untainted `go run` lies |
| Bump Action `@v0.5.2` | Separate tabletop — out of scope |
| Retag / move `v0.5.4` after bump | Rewrites provenance |

## Ordered steps

### 1. Prep

1. Sync to `corp-origin/main` (RI-SE tip with first-run honesty).
2. Confirm tip has: `Next (optional):`, early + late Exit 0 lines, `Scan complete — repository unchanged.`, install `CURBPACK_REPO_I_UNDERSTAND`, `REPO=` print.
3. Keep this playbook; ship it with the advertise PR (do not move the tag tip for docs alone).

### 2. Tag RI-SE (pre-bump SHA)

```bash
git fetch corp-origin main
SHA=$(git rev-parse corp-origin/main)
git tag -a v0.5.4 "$SHA" -m "v0.5.4 first-run honesty"
git push corp-origin v0.5.4
```

- Tree at tag still has `MANIFEST_DEFAULT=v0.5.3` — **expected**.
- Release workflow ldflags set binary `Version=0.5.4` from the tag name.

### 3. Verify assets

```bash
gh run list --repo RI-SE/curbpack --workflow=release.yml
gh release view v0.5.4 --repo RI-SE/curbpack
# HTTP 200 for every install-manifest.json asset + checksums.txt
```

**Stop** if incomplete — do not bump.

### 4. Smoke **before** bump (required)

```bash
# Prefer scripts/release-smoke-install-scan.sh when present
CURBPACK_VERSION=v0.5.4 \
  curl -fsSL https://raw.githubusercontent.com/RI-SE/curbpack/main/scripts/install.sh | sh
curbpack version   # must be 0.5.4
# temp git repo → curbpack scan → assert honesty strings + porcelain empty
```

Do **not** merge the advertise PR until this passes.

### 5. Advertise on RI-SE `main`

Single PR after Step 4 green:

- `install-manifest.json` / `release-gate.json` → `v0.5.4` + `*_verified: true`
- `install.sh` / `install.ps1` `MANIFEST_DEFAULT` → `v0.5.4`
- `internal/buildinfo.Version` → `0.5.4`
- Docs/site/README install pin **v0.5.3 → v0.5.4** (leave Action `@v0.5.2`)
- CHANGELOG: `## v0.5.4` with first-run honesty; keep Unreleased clean
- rise-tryout dual-pin: CLI **v0.5.4**; Action `@v0.5.2`

Merge when CI green. Strangers use **`…/main/scripts/install.sh`** (not the tag script URL).

### 6. Smoke **main** default

```bash
# no CURBPACK_VERSION — proves advertisement
curl -fsSL https://raw.githubusercontent.com/RI-SE/curbpack/main/scripts/install.sh | sh
curbpack version   # 0.5.4
# same scan asserts
```

### 7. Post-ship

- Scorecard: Next **fixed (shipped)**; 404 **fixed**; PATH **acknowledged**; **do not** tick rise-3 Met.
- Send-verbatim / stranger log: **`…/main/scripts/install.sh`**. Optional: `CURBPACK_VERSION=v0.5.4` for pin-in-time.
- `launch-readiness.md`: record v0.5.4; **A2 ∧ A3 HUMAN**; no invites.
- afelin: parity PR for bump commit only — **no** `v0.5.4` tag on afelin.

## Success criteria

1. RI-SE `v0.5.4` release complete; `curbpack version` → `0.5.4` via ldflags.
2. Tag-smoke (`CURBPACK_VERSION`) passes **before** main bump; main-smoke passes **after**.
3. Manifest ≡ gate ≡ script default ≡ buildinfo `0.5.4`; Action still `@v0.5.2`.
4. No stranger doc recommends `…/v0.5.4/scripts/install.sh` for this cut.
5. Scorecard/launch updated without rise-3 or certification claims.
