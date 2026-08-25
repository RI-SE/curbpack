# Phase 6 — kill-test scaffold

> Maintainer note. Procedure scaffold only — results TBD. Not conformity assessment. Not certification.

## Goal

Falsify or support product value of offline **document triage** (`curbpack review` on curbpack-native review-packs): a useful mix of **confirmed** / **unconfirmed** / **contradicted** states across real submissions — reported as the **cause split**, never vanity summed `% unconfirmed` alone.

**Variance required:** ~100% confirmed **or** ~100% unconfirmed across the public set **falsifies** product value (no discriminative signal). Report **distribution**, never name-and-shame projects.

## Gate before cohort

**Negative (sensitivity) + specificity PASS is required before any cohort / `--batch` kill-test n=10.**

| Control | Pass rule |
|---------|-----------|
| Sensitivity matrix | Broken packs must detect: absent cited path → `unconfirmed`+`genuine`; altered `result_digest` / wrong sbom digest → `contradicted`+`self_disagree` |
| Specificity | Known-good bundle → `UnconfirmedGenuine == 0` **and** `ContradictedCount == 0` exactly |
| Extractor | Dogfood `UnconfirmedExtractor == 0` (non-zero is a classifier regression — fix before cohort) |

P4 red → no cohort, no circular OSS share→review as sole kill-test. See tests in `internal/review`.

## Procedure

### 1. Dogfood curbpack-on-itself (split metrics)

1. Run the existing dogfood path: [`.github/workflows/curbpack-dogfood.yml`](../../.github/workflows/curbpack-dogfood.yml) (Action against this repo; local equivalent: build binary → `curbpack check` / share path as documented).
2. If a local curbpack-native **review-pack** directory is present (e.g. after prepare-release / share; often gitignored as `/review-pack/`), run:

   ```bash
   curbpack review --full <path-to-review-pack>
   ```

3. Record **split** counts: confirmed; unconfirmed by cause (`producer` / `extractor` / `genuine` / `external`); contradicted by cause (`self_disagree` / …). Document triage ≠ product verdict.

### 2. Ten public OSS projects (only after P4 green)

1. Select **ten** public open-source projects that publish **security documentation** (e.g. SECURITY.md, security.txt, disclosure policy — claim-safe selection criteria only).
2. For each, produce or obtain a curbpack-native review-pack via the normal local loop (scan/init/check/share as applicable on a clone) — **on the evaluator’s machine**; do not upload proprietary trees.
3. Prefer **independent docs+code or intake-completeness** pilots when negatives fire and specificity holds — do **not** treat circular OSS share→review as the sole kill-test.
4. Run `curbpack review <dir>` (or `--batch` over prepared dirs) on each pack.
5. Aggregate **only** the distribution of split counts across the ten. **Do not** publish a per-project shame table. Internal worksheets may keep ids; public write-ups stay anonymized aggregates.

### 3. Named org case study

A **named** organization case study requires **prior written consent**. Without consent: keep anonymized or omit.

## Cohort decision (after dogfood + P4)

| Observation | Decision |
|-------------|----------|
| Negatives fire; specificity holds; dogfood genuine low | Detector works; prefer independent docs+code or intake-completeness pilot |
| Sensitivity or specificity fails | No cohort |
| `extractor` non-zero on dogfood | Classifier regression — fix first |

Defer `intake` / `packs lint` per [post-kill-test-gates.md](post-kill-test-gates.md).

## Results table (placeholder)

| Cohort | n | confirmed | unconfirmed split (P/E/G/X) | contradicted | Notes |
|--------|---|-----------|-----------------------------|--------------|-------|
| Self dogfood (this repo `review-pack/`) | 1 | 23 | 0 / 0 / 0 / 0 | 0 | After digest-fingerprint + triage-surface harden: digests confirmed; extractor 0; genuine 0 (no cache-path flood) |
| Frozen sample fixture | 1 | 10 | 7 / 0 / 1 / 1 | 0 | `testdata/sample-review-pack` — aha path; extractor 0; genuine=SECURITY.md cite |
| Public OSS (security docs) | 10 | TBD | TBD | TBD | **Blocked until human records dogfood + decides cohort type** |
| Named org (consent) | TBD | TBD | TBD | TBD | Omit until written consent |

**P4 controls (automated):** sensitivity matrix + specificity known-good — PASS in `internal/review` (`TestSensitivityMatrix`, `TestSpecificityKnownGood`). Extractor on sample = 0.

**Cohort decision (process):** Prefer independent docs+code or intake-completeness pilot once a human records self-dogfood split metrics; do **not** use circular OSS share→review as the sole kill-test. Intake/lint remain deferred.

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

Procedure per clone: shallow clone → `curbpack init --yes` (or house profile) → `check` / `share` as far as the tree allows → `curbpack review <review-pack>` → record **split** counts only. Never publish a per-project shame table.

## Claim discipline

- Triage is about the **received document**, not legal conformity.
- Never equate kill-test metrics with CE, notified-body, or CRA compliance.
- Pin stays as documented in AGENTS.md until a human approves a bump.
