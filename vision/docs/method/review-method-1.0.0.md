# Curbpack review method 1.0.0

**Dated / frozen:** 2026-08-26  
**Method id:** `curbpack-review-method`  
**Method version:** `1.0.0` (must equal `review.MethodVersion` in code)

Offline structural check of a received curbpack-native review-pack. Writes nothing, calls no network, and produces byte-identical digests on any machine for the same bundle bytes (when under the digest ceiling).

**Not a product verdict. Not conformity assessment. Not CE marking. Not a notified-body opinion.**

## 1. Scope

This method reports on the **document** (structure, digest self-consistency, reference resolvability). It does **not** determine product fitness, legal conformity, or accreditation status.

## 2. Inputs

Required layers (must be present, non-empty, non-symlink):

- `01-gate-failures.json`
- `02-action-report.md`
- `03-executive-summary.md`
- `buyer-onepager.html`

Optional structure layers (absence is unconfirmed/producer, not contradicted): SBOM/VEX/SARIF/watchlist join, `context-pack.json`, `buyer-questions.md`.

`context-pack.json` is **not** a reference/triage surface.

## 3. Classification

States: `confirmed` | `unconfirmed` | `contradicted`.

Causes:

- Unconfirmed: `producer` | `extractor` | `genuine` | `external`
- Contradicted: `self_disagree`

## 4. Reference resolution

A reference is a claim the triage surfaces make about the system under review: a pack claim id, a path-shaped artifact pointer, or an external URL.

**Markup, booleans, JSON keys, versions, and truncated hashes are not references.**

Default triage surfaces: `02-action-report.md`, `03-executive-summary.md`, `buyer-questions.md`, `buyer-onepager.html`. External URLs are recorded and never fetched.

## 5. Digests

Placement inside `Run`: after airlock → tally → sortFindings, **immediately before** emit. If a refuse-oversize finding is appended, tally + sortFindings run again before `record_digest`.

### `bundle_digest`

sha256 over sorted relative slash paths; each path is length-prefixed, then the length-prefixed sha256 of the **full** file contents (streamed; not subject to the per-file parse read cap). Symlinks and out-of-jail paths are excluded (they already produce structure findings).

**Refuse-oversize ceiling (64 MiB total):** if Lstat size sum or streamed bytes would exceed the ceiling → contradicted finding `structure:bundle-size-cap`, `bundle_digest` left **empty**. Never truncate. Never emit a partial hash. Digest absent means oversize refuse (or compute failure), not “empty bundle.”

### `record_digest`

sha256 of the canonical JSON `Report` with `record_digest` and `bundle_root` set to empty strings. `bundle_root` is directory-name dependent (same bytes under differently named folders must compare equal). Full digests appear in `--json` only; terse/`--full` markdown show an 8-hex prefix.

Order: compute **`bundle_digest` first**, then `record_digest` (record covers counters, ordered findings, and the bundle digest value or empty).

## 6. Exit codes

- `0` — no contradicted findings in the current report
- `1` — any contradicted finding (or `--batch` child unreadable/contradicted)
- `2` — usage/env (including unreadable / oversized / schema-mismatched `--since` prior)

`--since` never changes the exit condition for NEW findings.

## 7. Governance — packs vs check kinds

**Packs are infinitely malleable. The nine check kinds are frozen.**

The nine: `annex_file`, `file_present`, `anti_placeholder`, `npm_dep_ban`, `manifest_dep_ban`, `text_forbid`, `import_reach`, `fresh`, `owned`.

A tenth check kind breaks comparison digests across binary versions. Express new needs as pack data, not new check kinds.

## 8. Comparison scheme

Frozen input: `testdata/comparison-bundle-2026-1/`. Expected `record_digest` is published beside this document. Divergence means a different tool version, a modified tool, or altered input — never “operator variation.”
