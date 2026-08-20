# Pre-stranger handoff (human-only)

Engineering stops here. Agents must not merge, tag, disable Pages, or run stranger outreach.

**Branch:** `feat/pr4-funnel` → [PR #73](https://github.com/afelin/curbpack/pull/73)  
**Stranger path after tag:** `curl …/v0.5.3/scripts/install.sh | sh` then `curbpack scan`  
**Action pin:** stays **`@v0.5.2`** until human tabletop approves bump ([AGENTS.md](../../AGENTS.md))

---

## Checklist — maintainer

### 1. Merge train

- [ ] Confirm PR #73 CI green on latest push (`gh pr checks 73`)
- [ ] Merge [PR #73](https://github.com/afelin/curbpack/pull/73) → `main` (merge commit preferred if tagging from merge SHA)
- [ ] Confirm `main` CI green (required: `test (ubuntu-latest)`, `test (macos-latest)`, `smoke`, `gauntlet`, `redteam-pilot`)
- [ ] Run `./scripts/curb-sync.sh` — sync afelin → RI-SE mirror
- [ ] Verify RI-SE `main` parity with afelin

**Do not merge:** [PR #75](https://github.com/afelin/curbpack/pull/75) (`do-not-merge` staging). **Do not merge:** PR #6 ENISA until domain reader ships.

### 2. Tag v0.5.3

- [ ] Annotated tag `v0.5.3` on merge SHA → push → [`.github/workflows/release.yml`](../../.github/workflows/release.yml) publishes assets + `checksums.txt`
- [ ] `gh release view v0.5.3` — asset list matches [`scripts/install-manifest.json`](../../scripts/install-manifest.json)
- [ ] Optional: bump `default_version` in `install-manifest.json` to `v0.5.3` in a follow-up commit on `main` (after tag smoke)

### 3. Three-OS install + scan smoke matrix

Clean env — no workspace binary on PATH.

| OS | Install | Command | Pass |
|----|---------|---------|------|
| macOS | `curl -fsSL https://raw.githubusercontent.com/afelin/curbpack/v0.5.3/scripts/install.sh \| sh` | `curbpack scan` in any git repo | exit 0; Art 14 clock + `Next:`; `git status --porcelain` empty |
| Linux | same | same | same |
| Windows | `irm https://raw.githubusercontent.com/afelin/curbpack/v0.5.3/scripts/install.ps1 \| iex` | `curbpack scan` | same |

Optional regression: `curbpack doctor && curbpack demo` on each OS.

Record results: Discussion comment or internal log.

### 4. Ops housekeeping

- [ ] **Disable afelin GitHub Pages** — single canonical site: https://ri-se.github.io/curbpack/
- [ ] **Card test:** logged-out phone → Slack + LinkedIn; paste https://ri-se.github.io/curbpack/ ; LinkedIn Post Inspector if stale cache
- [ ] Confirm [`.github/workflows/pages.yml`](../../.github/workflows/pages.yml) daily countdown cron (`0 6 * * *` UTC)
- [ ] RI-SE About/mirror wording still correct

### 5. Stranger program kit (after smoke green)

Send verbatim:

```bash
curl -fsSL https://raw.githubusercontent.com/afelin/curbpack/v0.5.3/scripts/install.sh | sh
cd /path/to/your/git/repo
curbpack scan
```

Windows: `install.ps1` equivalent.

**Gate:** 3 external repos × 2 successful `scan` runs each → log in spreadsheet or ADOPTERS draft PR → unlock Wave B (`verify` spike first per SDD).

Collect per stranger: OS, install method, repo type, run 1 + run 2 stdout, Was `Next:` clear?, blockers.

---

## Stacked scope (PR #73)

| Layer | Contents |
|-------|----------|
| Funnel | First-user bugs, honest Art 14 badge, CRA-ART14-PATH gate, site/README hero, scan CI smoke |
| Wave A | SDD v1.0 adoption, §14 removals, MCP sock → [`examples/mcp/`](../../examples/mcp/) sidecar |
| Copy (this commit) | install.sh + scan @ v0.5.3; troubleshooting scan section; gauntlet scan smoke for v0.5.3+ |

**Explicit:** PR #75 never merges. npm publish deferred (PR5).

---

## Engineering verification (already run on branch)

- `go test ./...`
- `./scripts/claim-safety.sh`

After merge + tag, re-run smoke matrix above before stranger outreach.
