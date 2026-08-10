# Buyer evidence (quiet path)

Ask the supplier for a **buyer one-pager** (supplier evidence summary) and, if needed, the **review pack**—structural gate evidence without GRC SaaS.

What the buyer receives:

- A one-screen HTML snapshot (local gate score on this tree — not certification)
- Optional review-pack folder (JSON + markdown layers)
- Optional ContextPack / buyer-questions checklist for deeper human Q&A
- Attest status: **UNSIGNED — not cryptographically verified** until ssh-agent attest

Not conformity assessment. Not CE marking. Not a notified-body opinion.

## One-breath share recipe

```bash
cyberready check
cyberready export --context-pack      # washed assistant/auditor snapshot
cyberready export --buyer-questions   # human Q&A checklist
cyberready prepare-release            # review-pack / one-pager
# human: cyberready attest            # never auto-attest
```

Thin CLI wrapper (same order; exits non-zero if check is red, still writes ContextPack for the red state):

```bash
cyberready share
# optional: cyberready share --skip-prepare-release
```

Artifacts land under `.github/cyberready/cache/` (`context-pack.json` + `.md`, `buyer-questions.md` + `.json`) and `review-pack/`.

## Individual exports

```bash
cyberready check
cyberready export --buyer-questions
# → .github/cyberready/cache/buyer-questions.md (+ .json)
```

Optional shareable map (deps summary, secret-hit count, informational watchlist∩SBOM — not a CVE product):

```bash
cyberready export --lay-of-land
# → .github/cyberready/cache/lay-of-land.md (+ .json)
```

Hand the Markdown checklist / ContextPack to the human reviewer. When drafts are ready, `cyberready prepare-release` then human `cyberready attest`.

Rows carry `assurance_class: structural_draft`. Buyer-questions header includes `attestation_status: none | ssh-agent`.

CyberReady prepares structural evidence for product repos — pair with SCA (e.g. Trivy/OSV) and secret scanners (e.g. Gitleaks) for depth; not a security program or CVE product.

See also: [Voice and terms](../voice-and-terms.md) · [Assistant loop](../assistant-loop.md) · [For authorities](../for-authorities.md) · [Daily loop](daily-loop.md) · [Intent vs Scope](../intent-vs-scope.md) · [Strategy boundary](../strategy-boundary.md) · [Glossary](../glossary-and-audience.md)
