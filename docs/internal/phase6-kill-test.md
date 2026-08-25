# Phase 6 — kill-test scaffold

> Maintainer note. Procedure scaffold only — results TBD. Not conformity assessment. Not certification.

## Goal

Falsify or support product value of offline **document triage** (`curbpack review` on curbpack-native review-packs): a useful mix of **confirmed** / **unconfirmed** / **contradicted** states across real submissions.

**Variance required:** ~100% confirmed **or** ~100% unconfirmed across the public set **falsifies** product value (no discriminative signal). Report **distribution**, never name-and-shame projects.

## Procedure

### 1. Dogfood curbpack-on-itself

1. Run the existing dogfood path: [`.github/workflows/curbpack-dogfood.yml`](../../.github/workflows/curbpack-dogfood.yml) (Action against this repo; local equivalent: build binary → `curbpack check` / share path as documented).
2. If a local curbpack-native **review-pack** directory is present (e.g. after prepare-release / share; often gitignored as `/review-pack/`), run:

   ```bash
   curbpack review <path-to-review-pack>
   ```

3. Record triage counts only (confirmed / unconfirmed / contradicted). Document triage ≠ product verdict.

### 2. Ten public OSS projects (distribution only)

1. Select **ten** public open-source projects that publish **security documentation** (e.g. SECURITY.md, security.txt, disclosure policy — claim-safe selection criteria only).
2. For each, produce or obtain a curbpack-native review-pack via the normal local loop (scan/init/check/share as applicable on a clone) — **on the evaluator’s machine**; do not upload proprietary trees.
3. Run `curbpack review <dir>` on each pack.
4. Aggregate **only** the distribution of confirmed / unconfirmed / contradicted counts (or percentages) across the ten. **Do not** publish a per-project shame table. Internal worksheets may keep ids; public write-ups stay anonymized aggregates.

### 3. Named org case study

A **named** organization case study requires **prior written consent**. Without consent: keep anonymized or omit.

## Results table (placeholder)

| Cohort | n | % confirmed | % unconfirmed | % contradicted | Notes |
|--------|---|-------------|---------------|----------------|-------|
| Self dogfood (this repo `review-pack/`) | 1 | 43% (23) | 57% (30) | 0% (0) | 2026-08-25 local `curbpack review ./review-pack` — state mix present |
| Frozen sample fixture | 1 | 53% (10) | 47% (9) | 0% (0) | `testdata/sample-review-pack` — aha path |
| Public OSS (security docs) | 10 | TBD | TBD | TBD | Cohort list below — aggregate only; no project names in public report |
| Named org (consent) | TBD | TBD | TBD | TBD | Omit until written consent |

**Early signal:** self dogfood + sample are **not** ~100% confirmed or ~100% unconfirmed — discriminative mix exists on curbpack-native packs. Full OSS n=10 still required before opening intake/lint/batch ([post-kill-test-gates.md](post-kill-test-gates.md)).

## Public OSS cohort (internal worksheet — consent-free)

Ten public projects with published security documentation (selection only; results stay aggregated):

1. curl/curl  
2. openssl/openssl  
3. golang/go  
4. kubernetes/kubernetes  
5. torvalds/linux (security docs only — expect heavy; optional substitute: aquasecurity/trivy)  
6. sigstore/cosign  
7. aquasecurity/trivy  
8. github/codeql-action  
9. rustls/rustls  
10. python/cpython  

Procedure per clone: shallow clone → `curbpack init --yes` (or house profile) → `check` / `share` as far as the tree allows → `curbpack review <review-pack>` → record counts only. Never publish a per-project shame table.

## Claim discipline

- Triage is about the **received document**, not legal conformity.
- Never equate kill-test metrics with CE, notified-body, or CRA compliance.
- Pin stays as documented in AGENTS.md until a human approves a bump.
