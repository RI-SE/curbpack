# For authorities, auditors, and CISOs

**Local pack gates. Humans review. Not conformity assessment.**

Sign-off oriented brief for NCSC/EU-style authorities, internal auditors, and CISOs who need to know what CyberReady is — without reading integrator notes or any optional sibling product.

Abbreviations: see [glossary and audience](glossary-and-audience.md) (CE, CRA, SBOM, SARIF, GRC, HPURL, RKG, IR, VEX, notified body, conformity assessment, RISE, NCSC).

## What CyberReady is

- A **local-first command-line tool** that evaluates **packs** (JSON rule sets) against a git repository on the supplier’s machine.
- A producer of **structural evidence** (JSON + markdown + optional HTML one-pager) for **human review**.
- An **instrument panel / evidence habit** for product repos — pair with SCA and secret scanners for depth; not a full security program.

## What CyberReady is not

- **Not** conformity assessment, CE marking, or notified-body approval.
- **Not** a certificate that green gates equal legal market access or CRA conformity.
- **Not** a GRC SaaS, cloud policy brain, or LLM-as-judge.
- **Not** an official NCSC/FRA/agency product or endorsement vehicle.
- **Not** dependent on any private tutor product to operate.

Gate pass means: deterministic pack rules did not fail on the files present — a human still judges risk, annex drafts, and legal posture.

## Evidence artifact catalog (trust levels)

| Artifact | How produced | Trust level (honest) |
|----------|--------------|----------------------|
| Gate JSON / action report (`check`, `validate`) | Local deterministic pack evaluation | **Structural evidence** — reproducible on the same tree; not a legal finding |
| SARIF export | `export --sarif` / Action upload | Same findings in IDE/CI format; still pack gates, not certification |
| Buyer-questions checklist | `export --buyer-questions` | Human Q&A aid; rows carry `assurance_class: structural_draft` |
| Lay-of-land / instrument map | `export --lay-of-land` | Shareable map (deps summary, secret-hit count, informational watchlist∩SBOM) — **not** a CVE product |
| Review pack + buyer one-pager | `prepare-release` | Procurement snapshot; **not** a certificate of conformity |
| CycloneDX SBOM (best-effort) | From common lockfiles when present | Inventory draft; completeness depends on lockfiles |
| OpenVEX draft | Bound at attest time when applicable | Draft exploitability notes — not a vulnerability program |
| HPURL pointer | Local `state_hash` fragment | Client-side hash compare only — not remote notarization |
| Git Notes attest capsule | Human `attest` | **ssh-agent-signed** = cryptographic signature present; **unsigned** = present but **not** cryptographically verified |
| RKG (`policy-graph.json`) | `packs export-graph` | Local teaching/navigation graph — not a legal oracle |
| Explain-packet | `export --explain-packet` | Sanitized tutor surface; **never** greenlights gates |

**Unsigned ≠ verified.** Green readiness % is a local gate score, not a certification score.

## Institute neutrality

Development may be institute-supported (see [`NOTICE`](../NOTICE)). **RISE is a funder / applied-research supporter — not this product’s certifier.** Public language must stay claim-safe: never “RISE-approved,” “NCSC-approved,” or agency-endorsed product claims.

Full MoU / co-promotion boundary: [promotion firewall](promotion-firewall.md).

## Air-gap / offline

- Daily `check` needs **no** remote policy brain.
- Packs ship **embedded**; refresh via air-gap `packs import`, or network update only with an explicit sha256 pin.
- Install / Action downloads verify release `checksums.txt` (sha256, fail-closed).
- Optional tutors (any chat) receive only sanitized explain-packets; raw source is not the default export path.

## Claim-safe boundaries (sign-off language)

Safe to say:

- “Prepares structural evidence for human review.”
- “Local pack gates; humans retain judgment.”
- “Not a conformity assessment / not CE / not notified-body.”

Unsafe / forbidden as product claims:

- That CyberReady certified the product, completed conformity assessment, or issued CE marking.
- That gate green equals CRA-compliant, NIS2-compliant, or market-ready by law.
- That RISE, NCSC, FRA, or any agency endorses or approves the tool as official guidance.

CI enforces wording via `scripts/claim-safety.sh`. This page is **not** certification theater and does not replace legal counsel or a notified body.

## Suggested reviewer path

1. Read this page + [Intent vs Scope](intent-vs-scope.md).
2. Ask the supplier for buyer-questions / one-pager + attest status.
3. Optionally deep-read [security model](security-model.md) and the [white paper](../papers/cyberready-whitepaper.md).
4. Do **not** require [coreward-bridge.md](coreward-bridge.md) — that file is for integrators only.

Site mirror: [for-authorities on Pages](../site/for-authorities/).

---

> **Optional, separate product:** Coreward is a private tutor/enforce client that may consume CyberReady explain-packets over an optional Unix socket. CyberReady is fully self-sustaining without it — adopters do not need Coreward. Brief architecture note (public Pages, not the private repo): https://afelin.github.io/coreward/

(Wording source: [coreward-pointer.md](coreward-pointer.md).)
