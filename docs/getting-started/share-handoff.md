# Supplier share handoff

After green gates, suppliers hand buyers a **buyer one-pager** and optionally a **review pack**. Buyers judge evidence using the [trust table on for-reviewers](../../site/for-reviewers/) — not a certification score.

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
# optional: curbpack share --bundle --reveal
# human review tick: curbpack pathway confirm-share  — see pathway.md
```

Artifacts land under `.github/curbpack/cache/` (`context-pack.json` + `.md`, `buyer-questions.md` + `.json`) and `review-pack/`.

Point buyers at the site trust table: [for-reviewers](../../site/for-reviewers/) · [sample one-pager](../../site/samples/onepager.html).

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

Warm-start before share: [pathway](pathway.md) (`pathway status` → confirms → stop before attest).

Curbpack prepares structural evidence for product repos — pair with SCA (e.g. Trivy/OSV) and secret scanners (e.g. Gitleaks) for depth; not a security program or CVE product.

See also: [Buyer evidence](buyer-evidence.md) · [Voice and terms](../voice-and-terms.md) · [Assistant loop](../assistant-loop.md) · [Daily loop](daily-loop.md) · [For builders](../../site/for-builders/)
