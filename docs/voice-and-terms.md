# Voice and terms

**Canonical public language for Curbpack.** Site pages, README, white paper, and stakeholder docs cite this file. Abbreviations: [glossary and audience](glossary-and-audience.md). MoU / deny list: [promotion firewall](promotion-firewall.md). Wording is enforced by [`scripts/claim-safety.sh`](../scripts/claim-safety.sh).

## Primary sentence

Use on home, README, and white paper §1:

> Curbpack checks your repository against local rule packs and writes a review pack you can hand to a buyer or auditor—on your machine, without claiming certification.

## Fence line

Second, never first. One fence block per page; link elsewhere instead of repeating:

> Not conformity assessment. Not CE marking. Not a notified-body opinion.

## RISE line

Footer / authorities / NOTICE-aligned. Never endorsement:

> Development supported by RISE Research Institutes of Sweden as an applied research / competence object. RISE does not certify products that use Curbpack gate results.

## Preferred public terms

| Prefer | Say once, then reuse | Do not lead with |
|--------|----------------------|------------------|
| **Curb outlines** | first pathway warm-start step (sketch *what* you are curbing—enums, house-first, sector; not the law) | “pathway to regulation”, compliance journey as product |
| **curb** / **curbpack** | CLI (`curb check`, `curbpack share`) | long-lived legacy binary names |
| **pack** | rule pack you run / review pack you hand off | “policy brain”, “compliance engine” |
| **curb check** | local gate pass/fail on this tree | “instrument panel”, “Δ readiness”, TTFV |
| review pack | evidence for human review | “compliance package”, “certificate pack” |
| buyer one-pager | supplier evidence summary | “readiness scoreboard”, “cert score” |
| structural evidence | documentation and dependency checks | “compliance evidence”, “CRA proof” |
| human review / human judgment | attest when ready | “audit complete”, “sign-off as compliant” |
| unsigned ≠ verified | ssh-agent signed | “verified compliant” |
| house-policy (default) | CRA-shaped pack only when opted in | Never claim “CRA compliant” or “EU CRA Baseline” as a product claim |
| **Three ways in** (Write / Bring / CI) | Write starts with curb outlines; Bring/CI skip outlines; same local check | “Pick a door”; implying only two paths |
| research brief | allowlisted Sources (informational; never gates check) | regulation chat KB / open-web RAG as SoR |
| cite-check | refuses uncited Claims before confirm-prose | inventing regulation text |
| dual-draft + Recommended A\|B | human pick; record last_draft_pick | auto-apply / auto-attest |
| confirm (TTY or `--i-am-human`) | human-owned ticks | agent auto-confirm |

**Mnemonic:** *Curb outlines → packs → check → hand off.*

## Stakeholder first sentences

| Audience | First sentence |
|----------|----------------|
| **Builder** | Install, init, and check—green gates in your repo in under ten minutes. |
| **Buyer / reviewer** | Ask the supplier for a buyer one-pager and, if needed, the review pack—then use the trust table. |
| **CISO / authority** | Curbpack prepares structural evidence for human review; it does not perform conformity assessment. |
| **Anyone (home / README)** | Use the primary sentence above. |

## Agency-aligned register

On authorities pages, use EU-familiar nouns: *structural evidence*, *human review*, *conformity assessment*, *notified body*, *CE marking*, *Cyber Resilience Act (CRA)*. Never imply Curbpack performs conformity assessment. Frame packs as **checklists shaped like regulatory annex drafts**, not law.

## Builder register

Short verbs: install, init, check, prepare-release, attest, share, pathway status (curb outlines), research. Prefer **Pick how you start** / **Three ways in** over “Pick a door.” No soft-exit / Zig / TTFV on the first screen. Pin `@v0.5.0` under Install / Builders—not in the hero.

## Writing rules

1. One fence block per page; link to this file or [for-authorities](for-authorities.md) for depth.
2. Expand abbreviations on first use on every public page (CE, CRA, SBOM, SARIF, …).
3. No superlatives (“best”, “enterprise-grade”, “revolutionary”).
4. No unexplained insider tokens on home/builders: TTFV, HPURL, RKG, IR, airlock, covenant, Δ.
5. Coreward is a one-line optional footer pointer only ([coreward-pointer](coreward-pointer.md)).
6. Do not publish `docs/gtm-oss/` on Pages.
7. Product mark is **Curbpack** (no “+”). Avoid CurbPack camelCase.

## Safe / unsafe phrases

Lifted and tightened from the [promotion firewall](promotion-firewall.md):

**Safe**

- “Prepares structural evidence for human review.”
- “Development supported by RISE as an applied research / competence object.”
- “Not a conformity assessment” / “Not CE / not notified-body.”
- “Local pack gates; humans retain judgment.”
- “Unsigned ≠ cryptographically verified.”
- Awareness links to public NCSC/FRA materials **without** endorsement claims.

**Unsafe (never as product claims)**

- Never claim “RISE-approved”, “RISE-certified”, or “agency-endorsed”
- Never claim “NCSC-approved”, “FRA-approved”, or official agency guidance product
- Never claim CE certification theater, completed conformity assessment, or notified-body approval
- Never claim gate green equals legal conformity, CRA-compliant, or market access by law

## Cold-reader bar

A stranger should answer from the public home alone, in under two minutes:

1. What is it?
2. What do I run?
3. What do I get?
4. What must I not claim?

See also: [glossary](glossary-and-audience.md) · [intent vs scope](intent-vs-scope.md) · [for-authorities](for-authorities.md) · [migration from Curbpack](migration-curbpack-to-curbpack.md) · [launch readiness](launch-readiness.md)
