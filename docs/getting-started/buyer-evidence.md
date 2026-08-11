# Buyer evidence (quiet path)

Ask the supplier for a **buyer one-pager** (supplier evidence summary) and, if needed, the **review pack**—structural gate evidence without GRC SaaS.

Suppliers may Write, Bring, or CI into the same local check; optional research briefs inform drafts only and never gate pass/fail.

What the buyer receives:

- A one-screen HTML snapshot (local gate score on this tree — not certification)
- Optional review-pack folder (JSON + markdown layers)
- Optional ContextPack / buyer-questions checklist for deeper human Q&A
- Attest status: **UNSIGNED — not cryptographically verified** until ssh-agent attest

Not conformity assessment. Not CE marking. Not a notified-body opinion.

## One-breath share recipe

```bash
curbpack check
curbpack export --context-pack      # washed assistant/auditor snapshot
curbpack export --buyer-questions   # human Q&A checklist
curbpack prepare-release            # review-pack / one-pager
# human: curbpack attest            # never auto-attest
```

Thin CLI wrapper (same order; exits non-zero if check is red, still writes ContextPack for the red state):

```bash
curbpack share
# optional: curbpack share --skip-prepare-release
# human review tick: curbpack pathway confirm-share  — see pathway.md
```

Artifacts land under `.github/curbpack/cache/` (`context-pack.json` + `.md`, `buyer-questions.md` + `.json`) and `review-pack/`.

Warm-start before share: [pathway](pathway.md) (`pathway status` → confirms → stop before attest).

## Individual exports

```bash
curbpack check
curbpack export --buyer-questions
# → .github/curbpack/cache/buyer-questions.md (+ .json)
```

Optional shareable map (deps summary, secret-hit count, informational watchlist∩SBOM — not a CVE product):

```bash
curbpack export --lay-of-land
# → .github/curbpack/cache/lay-of-land.md (+ .json)
```

Hand the Markdown checklist / ContextPack to the human reviewer. When drafts are ready, `curbpack prepare-release` then human `curbpack attest`.

Rows carry `assurance_class: structural_draft`. Buyer-questions header includes `attestation_status: none | ssh-agent`.

Curbpack prepares structural evidence for product repos — pair with SCA (e.g. Trivy/OSV) and secret scanners (e.g. Gitleaks) for depth; not a security program or CVE product.

See also: [Voice and terms](../voice-and-terms.md) · [Assistant loop](../assistant-loop.md) · [For authorities](../for-authorities.md) · [Daily loop](daily-loop.md) · [Intent vs Scope](../intent-vs-scope.md) · [Strategy boundary](../strategy-boundary.md) · [Glossary](../glossary-and-audience.md)
