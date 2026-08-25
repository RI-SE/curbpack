# Pre-stranger handoff (human-only)

> **Historical (2026-08).** Dual-remote sync removed; canonical repo is [RI-SE/curbpack](https://github.com/RI-SE/curbpack). PR links below reference the former afelin fork.

Engineering stops here. Agents must not merge, tag, disable Pages, or run stranger outreach.

**v0.5.3 shipped (2026-08-25):** [RI-SE release](https://github.com/RI-SE/curbpack/releases/tag/v0.5.3) at tag `f74cc96`. Install+scan smoke **agent-verified**. Remaining before invites: **A2** (OG/social) + **A3** Tier-3 human note (first-run feedback / Teams / ADOPTERS — Discussions not enabled) — do not send invites yet.

**Branch:** `feat/pr4-funnel` → [PR #73](https://github.com/RI-SE/curbpack/pull/73)  
**Stranger path:** `curl …/main/scripts/install.sh | sh` (downloads **v0.5.3**) then `curbpack scan`  
**Action pin:** stays **`@v0.5.2`** until human tabletop approves bump ([AGENTS.md](../../AGENTS.md))

---

## Checklist — maintainer

### 1. Merge train

- [x] Confirm PR #73 CI green on latest push (`gh pr checks 73`)
- [x] Merge [PR #73](https://github.com/RI-SE/curbpack/pull/73) → `main` (merge commit preferred if tagging from merge SHA)
- [x] Confirm `main` CI green (required: `test (ubuntu-latest)`, `test (macos-latest)`, `smoke`, `gauntlet`, `redteam-pilot`)
- [x] ~~Run `./scripts/curb-sync.sh`~~ (deprecated — RI-SE is now canonical)
- [x] Verify RI-SE `main` parity with afelin

**Do not merge:** [PR #75](https://github.com/RI-SE/curbpack/pull/75) (`do-not-merge` staging). **ENISA:** preliminary mapping on `main` (not domain-verified) — see [docs/mappings/enisa-cra-mapping.md](../mappings/enisa-cra-mapping.md).

### 2. Tag v0.5.3

- [x] Annotated tag `v0.5.3` on merge SHA → push → [`.github/workflows/release.yml`](../../.github/workflows/release.yml) publishes assets + `checksums.txt`
- [x] `gh release view v0.5.3` — asset list matches [`scripts/install-manifest.json`](../../scripts/install-manifest.json)
- [x] Optional: bump `default_version` in `install-manifest.json` to `v0.5.3` in a follow-up commit on `main` (after tag smoke)

### 3. Three-OS install + scan smoke matrix

Clean env — no workspace binary on PATH.

| OS | Install | Command | Pass |
|----|---------|---------|------|
| macOS | `curl -fsSL https://raw.githubusercontent.com/RI-SE/curbpack/main/scripts/install.sh \| sh` | `curbpack scan` in any git repo | **Done (2026-08-20):** v0.5.3 binary via install; exit 0; Art 14 + `Next:`; porcelain empty. Until manifest bump on main, bare curl installs v0.5.2 — bump merged post-tag. |
| Linux | same | same | same |
| Windows | `irm https://raw.githubusercontent.com/RI-SE/curbpack/main/scripts/install.ps1 \| iex` | `curbpack scan` | same |

Optional regression: `curbpack doctor && curbpack demo` on each OS.

Record results: first-run feedback issue, Teams note, ADOPTERS draft PR, or internal log (Discussions not enabled).

### 4. Ops housekeeping

- [ ] **Disable afelin GitHub Pages** — single canonical site: https://ri-se.github.io/curbpack/
  - **GitHub UI (CLI cannot disable source):** Repo **RI-SE/curbpack** → **Settings** → **Pages** → under **Build and deployment**, set **Source** to **None** (or delete the Pages workflow deployment if your org requires workflow-only). Confirm https://afelin.github.io/curbpack/ stops updating or returns 404.
  - API check (2026-08-20): `gh api repos/RI-SE/curbpack/pages` → `html_url`: https://afelin.github.io/curbpack/ (still active).
- [ ] **Card test:** logged-out phone → Slack + LinkedIn; paste https://ri-se.github.io/curbpack/ ; LinkedIn Post Inspector if stale cache
- [ ] Confirm [`.github/workflows/pages.yml`](../../.github/workflows/pages.yml) daily countdown cron (`0 6 * * *` UTC)
- [ ] RI-SE About/mirror wording still correct

### 5. Stranger program kit (after smoke green)

Send verbatim:

```bash
curl -fsSL https://raw.githubusercontent.com/RI-SE/curbpack/main/scripts/install.sh | sh
cd /path/to/your/git/repo
curbpack scan
```

Windows: `install.ps1` equivalent.

**Gate:** 3 external repos × 2 successful `scan` runs each → log in spreadsheet or ADOPTERS draft PR → unlock Wave B (`verify` spike first per SDD).

Collect per stranger: OS, install method, repo type, run 1 + run 2 stdout, Was `Next:` / `Next (optional):` clear? (both OK on v0.5.3 vs unreleased), blockers.

Log template: [stranger-validation-log.md](./stranger-validation-log.md).

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
