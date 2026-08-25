# Docs index

## Who should read what

| Reader | Start here |
|--------|------------|
| Builder / adopter | [Install](getting-started/install.md) · [Share handoff](getting-started/share-handoff.md) · [60-second paths](getting-started/60-second-paths.md) · [Troubleshooting](getting-started/troubleshooting.md) · [RISE tryout](getting-started/rise-tryout.md) · [Pathway](getting-started/pathway.md) · [Repo ops hardening](getting-started/repo-ops-hardening.md) · [site builders](../site/for-builders/) |
| Buyer / reviewer | [Buyer evidence](getting-started/buyer-evidence.md) · [for-reviewers](../site/for-reviewers/) |
| CISO / authority / auditor | [For authorities](for-authorities.md) · [Intent](intent-vs-scope.md) · [security model](security-model.md) · [promotion firewall](promotion-firewall.md) |
| Pack author / partner / agent | [assistant-loop](assistant-loop.md) · [Software design document](software-design-document.md) · [SDD gap analysis](internal/sdd-gap-analysis.md) · [write-your-own-pack](write-your-own-pack.md) · [design partners](design-partners.md) · skill (`internal/skilldata/SKILL.md`) · [strategy boundary](strategy-boundary.md) |
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
| [Stable contracts](stable-contracts.md) | Explain airlock, GateFailure IR (nave freeze) |
| [Security model](security-model.md) | Trust boundaries, required CI, freeze |
| [Promotion firewall](promotion-firewall.md) | RISE-neutral publish language + MoU checklist |
| [Write your own pack](write-your-own-pack.md) | Pack authoring |
| [Packs update](packs-update.md) | Pack refresh / air-gap |
| [Assistant loop](assistant-loop.md) | Canonical multi-IDE contract + ContextPack + pack chooser |
| [Install](getting-started/install.md) | Cross-OS install (PowerShell \| macOS/Linux); install pin `v0.5.4`, Action `@v0.5.2`; release gate [`scripts/release-gate.json`](../scripts/release-gate.json) |
| [RISE tryout](getting-started/rise-tryout.md) | Thin RISE first-run entry (install → cd → scan); feedback on canonical repo |
| [First-run cohort scorecard](getting-started/first-run-cohort-scorecard.md) | 3→10→20→100 aggregates only (no PII); internal rows stay at RISE |
| [RISE pilot offer](getting-started/rise-pilot-offer.md) | One-sentence Neutral Evidence Profile Pilot frame |
| [Pilot scorecard](getting-started/pilot-scorecard.md) | Manual transaction / adoption scorecard |
| [Minimum receipt fixture](getting-started/minimum-receipt-fixture.md) | Receipt v0 thin index + structural validate |
| [Pilot decision log](getting-started/pilot-decision-log.md) | Equivalence / disposition learning log |
| [Getting started](getting-started/60-second-paths.md) | First move — three ways in (Write / Bring / CI) |
| [Troubleshooting](getting-started/troubleshooting.md) | PATH, SmartScreen, repair, doctor tips |
| [Pathway (warm-start)](getting-started/pathway.md) | Three ways in, one next ask, dual-draft HITL, research sidecar |
| [Daily loop](getting-started/daily-loop.md) | Habit: Action / check / attest |
| [Sync both remotes (deprecated)](getting-started/sync-both-remotes.md) | Historical — RI-SE/curbpack is now single source |
| [Buyer evidence](getting-started/buyer-evidence.md) | Buyer journey: one-pager → trust table → what not to assume |
| [Share handoff](getting-started/share-handoff.md) | Supplier share/export/attest recipe |
| [ENISA CRA mapping (preliminary)](mappings/enisa-cra-mapping.md) | Informational SME maturity ↔ pack map — **not domain-verified**; not ENISA endorsement |
| [Art 14 reporting vs handling](getting-started/art14-reporting-vs-handling.md) | Counsel note: Art 14 reporting clock vs later handling/SPOC; Art 50 grace not blanket |
| [Design partners](design-partners.md) | Partner ask + weekly ritual |
| [Coreward pointer](coreward-pointer.md) | Standardized optional-product aside + URL |

## Internal (maintainers)

| Doc | Purpose |
|-----|---------|
| [Fork policy](internal/fork-policy.md) | RI-SE-first; no parity/mirror PRs |
| [Launch readiness](internal/launch-readiness.md) | Internal launch checklist |
| [GitHub-readiness gaps](internal/github-readiness-gaps.md) | Stakeholder demand → Done/Polish/Ops/Reject + Evidence paths |
| [SDD gap analysis](internal/sdd-gap-analysis.md) | Repository baseline vs software design document |
| [v0.6 hardening checklist](internal/v0.6-hardening-checklist.md) | Pre–pin-bump guardrail evidence |

## Integrators only

| Doc | Purpose |
|-----|---------|
| [Coreward bridge](coreward-bridge.md) | Optional tutor IPC + dogfood checklist — **adopters do not need this** |

## Ops (not product)

| Path | Purpose |
|------|---------|
| [`gtm-oss/`](gtm-oss/) | **NON-PRODUCT / INTERNAL GTM** — amplify templates only; not for Pages or adopters |

Site quarantine: `.github/workflows/pages.yml` refuses `*gtm*` (and invite/exploit) paths under `site/`.
