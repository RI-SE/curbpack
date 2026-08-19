# Docs index

## Who should read what

| Reader | Start here |
|--------|------------|
| Builder / adopter | [Install](getting-started/install.md) · [60-second paths](getting-started/60-second-paths.md) · [Troubleshooting](getting-started/troubleshooting.md) · [Pathway](getting-started/pathway.md) · [Sync both remotes](getting-started/sync-both-remotes.md) · [site builders](../site/for-builders/) |
| Buyer / reviewer | [Buyer evidence](getting-started/buyer-evidence.md) · [for-reviewers](../site/for-reviewers/) |
| CISO / authority / auditor | [For authorities](for-authorities.md) · [Intent](intent-vs-scope.md) · [security model](security-model.md) · [promotion firewall](promotion-firewall.md) |
| Pack author / partner / agent | [assistant-loop](assistant-loop.md) · [Software design document](software-design-document.md) · [SDD gap analysis](sdd-gap-analysis.md) · [write-your-own-pack](write-your-own-pack.md) · [design partners](design-partners.md) · skill (`internal/skilldata/SKILL.md`) · [strategy boundary](strategy-boundary.md) |
| Integrator / tutor author | [Stable contracts](stable-contracts.md) · [Coreward bridge](coreward-bridge.md) · [Coreward pointer](coreward-pointer.md) |

Full audience table: [glossary and audience](glossary-and-audience.md). Public sentence voice: [voice and terms](voice-and-terms.md).

RISE / agency liaison: [promotion firewall](promotion-firewall.md) + [NOTICE](../NOTICE) — funder, not certifier.

## Product (adopters)

| Doc | Purpose |
|-----|---------|
| [Voice and terms](voice-and-terms.md) | Locked public sentences + preferred terms |
| [Migration guide](migration-cyberready-to-curbpack.md) | Prior-name cutover; dual-read legacy paths; pin `@v0.5.0` |
| [Glossary and audience](glossary-and-audience.md) | Abbreviations + who reads what |
| [For authorities](for-authorities.md) | NCSC/EU-style, auditor, CISO sign-off brief |
| [Intent vs Scope](intent-vs-scope.md) | What Curbpack is / is not |
| [Strategy boundary](strategy-boundary.md) | Curbpack standalone; claim boundaries |
| [GitHub-readiness gaps](github-readiness-gaps.md) | Stakeholder demand → Done/Polish/Ops/Reject + Evidence paths |
| [Stable contracts](stable-contracts.md) | Explain airlock, GateFailure IR (nave freeze) |
| [Security model](security-model.md) | Trust boundaries, required CI, freeze |
| [Promotion firewall](promotion-firewall.md) | RISE-neutral publish language + MoU checklist |
| [Write your own pack](write-your-own-pack.md) | Pack authoring |
| [Packs update](packs-update.md) | Pack refresh / air-gap |
| [Assistant loop](assistant-loop.md) | Canonical multi-IDE contract + ContextPack + pack chooser |
| [Install](getting-started/install.md) | Cross-OS install (PowerShell \| macOS/Linux); pin `@v0.5.2` |
| [Getting started](getting-started/60-second-paths.md) | First move — three ways in (Write / Bring / CI) |
| [Troubleshooting](getting-started/troubleshooting.md) | PATH, SmartScreen, repair, doctor tips |
| [Pathway (warm-start)](getting-started/pathway.md) | Three ways in, one next ask, dual-draft HITL, research sidecar |
| [Daily loop](getting-started/daily-loop.md) | Habit: Action / check / attest |
| [Sync both remotes](getting-started/sync-both-remotes.md) | One Cursor phrase to keep afelin ↔ RI-SE `main` matching |
| [Buyer evidence](getting-started/buyer-evidence.md) | Share recipe: ContextPack + buyer-questions + prepare-release |
| [Art 14 reporting vs handling](getting-started/art14-reporting-vs-handling.md) | Counsel note: Art 14 reporting clock vs later handling/SPOC; Art 50 grace not blanket |
| [Design partners](design-partners.md) | Partner ask + weekly ritual |
| [Launch readiness](launch-readiness.md) | Internal launch checklist |
| [Coreward pointer](coreward-pointer.md) | Standardized optional-product aside + URL |

## Integrators only

| Doc | Purpose |
|-----|---------|
| [Coreward bridge](coreward-bridge.md) | Optional tutor IPC + dogfood checklist — **adopters do not need this** |

## Ops (not product)

| Path | Purpose |
|------|---------|
| [`gtm-oss/`](gtm-oss/) | **NON-PRODUCT / INTERNAL GTM** — amplify templates only; not for Pages or adopters |

Site quarantine: `.github/workflows/pages.yml` refuses `*gtm*` (and invite/exploit) paths under `site/`.
