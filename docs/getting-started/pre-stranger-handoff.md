# Pre-stranger handoff (human-only)

> **Historical (2026-08).** Dual-remote sync removed; canonical repo is [RI-SE/curbpack](https://github.com/RI-SE/curbpack). PR links below reference the former afelin fork.

Engineering stops here. Agents must not merge, tag, disable Pages, or run stranger outreach.

<!-- curbpack-release:start -->
CLI release **v0.5.5** published **2026-09-05** ([release](https://github.com/RI-SE/curbpack/releases/tag/v0.5.5)); advertised on `main` **2026-09-05** ([advertise PR](https://github.com/RI-SE/curbpack/pull/51)).
<!-- curbpack-release:end -->

Current qualification and platform evidence: [launch status](../launch-status.md) and [release record](../../scripts/release-gate.json). A2/A3 remain human gates; this checklist does not authorize invitations.

## Historical merge checklist (2026-08)

The branch and checked boxes below describe the former fork. They are not current RI-SE merge instructions.

**Branch:** `feat/pr4-funnel` → [PR #73](https://github.com/afelin/curbpack/pull/73)
**Stranger path:** `curl …/main/scripts/install.sh | sh` (downloads **v0.5.5**) then `curbpack scan`  
(Do **not** use `…/v0.5.5/scripts/install.sh` — tag tree baked older `MANIFEST_DEFAULT`.)
**Action pin:** stays **`@v0.5.2`** until human tabletop approves bump ([AGENTS.md](../../AGENTS.md))

---

## Checklist — maintainer

### 1. Merge train

- [x] Confirm PR #73 CI green on latest push (`gh pr checks 73`)
- [x] Merge [PR #73](https://github.com/afelin/curbpack/pull/73) → `main` (merge commit preferred if tagging from merge SHA)
- [x] Confirm `main` CI green (required: `test (ubuntu-latest)`, `test (macos-latest)`, `smoke`, `gauntlet`, `redteam-pilot`)
- [x] ~~Run `./scripts/curb-sync.sh`~~ (deprecated — RI-SE is now canonical)
- [x] RI-SE merged; afelin catch-up optional (see [fork-policy](../internal/fork-policy.md))

**Historical hold:** [PR #75](https://github.com/afelin/curbpack/pull/75) (`do-not-merge` staging). **ENISA:** preliminary mapping on `main` (not domain-verified) — see [docs/mappings/enisa-cra-mapping.md](../mappings/enisa-cra-mapping.md).

### 2. Tag v0.5.3

- [x] Annotated tag `v0.5.3` on merge SHA → push → [`.github/workflows/release.yml`](../../.github/workflows/release.yml) publishes assets + `checksums.txt`
- [x] `gh release view v0.5.3` — asset list matches [`scripts/install-manifest.json`](../../scripts/install-manifest.json)
- [x] Optional: bump `default_version` in `install-manifest.json` to `v0.5.3` in a follow-up commit on `main` (after tag smoke)

### 3. Current three-OS install + scan evidence

Clean env — no workspace binary on PATH.

| OS | Install | Command | Pass |
|----|---------|---------|------|
| macOS | `main` installer, explicitly requesting `v0.5.5` | `curbpack version` and `curbpack scan` | Recorded agent smoke on 2026-09-05: version 0.5.5, scan exit 0, clean porcelain. See [release record](../../scripts/release-gate.json). |
| Linux | `main` installer, explicitly requesting `v0.5.5` | same commands | Released-version installation smoke **not recorded**. Asset availability and source CI do not substitute for this test. |
| Windows | `main` PowerShell installer, explicitly requesting `v0.5.5` | same commands | Released-version installation smoke **not recorded**. Asset availability and source CI do not substitute for this test. |

Optional regression: `curbpack doctor && curbpack demo` on each OS.

Record results: first-run feedback issue, Teams note, ADOPTERS draft PR, or internal log (Discussions not enabled).

### 4. Ops housekeeping

- [x] **Disable afelin GitHub Pages** — single canonical site: https://ri-se.github.io/curbpack/ ([historical checklist](https://github.com/RI-SE/curbpack/blob/17a18ed5395d635758424873113c7ef106409e17/docs/getting-started/pre-stranger-handoff.md#L50) recorded API DELETE 2026-08-25 and GET → 404; not re-verified here; this operational date is independent of release publication)
- [ ] **Card test:** logged-out phone → Slack + LinkedIn; paste https://ri-se.github.io/curbpack/ ; LinkedIn Post Inspector if stale cache
- [x] Confirm [`.github/workflows/pages.yml`](../../.github/workflows/pages.yml) daily countdown cron (`0 6 * * *` UTC)
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

Collect per stranger: OS, install method, repo type, run 1 + run 2 stdout, Exit 0 + Scan complete visible? Was `Next (optional):` clear when findings remained? blockers.

Log template: [stranger-validation-log.md](./stranger-validation-log.md).

---

## Stacked scope (PR #73)

| Layer | Contents |
|-------|----------|
| Funnel | First-user bugs, honest Art 14 badge, CRA-ART14-PATH gate, site/README hero, scan CI smoke |
| Wave A | SDD v1.0 adoption, §14 removals, MCP sock → [`examples/mcp/`](../../examples/mcp/) sidecar |
| Copy (this commit) | install.sh + scan @ v0.5.3; troubleshooting scan section; gauntlet scan smoke for v0.5.3+ |

**Historical decision:** former-fork PR #75 was held. npm publish deferred (PR5).

---

## Historical engineering verification (former branch)

- `go test ./...`
- `./scripts/claim-safety.sh`

After merge + tag, re-run smoke matrix above before stranger outreach.
