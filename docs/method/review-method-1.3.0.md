# Curbpack review method 1.3.0

**Dated / frozen:** 2026-08-27  
**Method id:** `curbpack-review-method`  
**Method version:** `1.3.0` (must equal `review.MethodVersion` in code)

Offline structural check of a received curbpack-native review-pack **or** a repository document tree (`ReferencesOnly`). Writes nothing, calls no network, and produces byte-identical digests on any machine for the same assessed bytes (when under the digest ceiling).

**Not a product verdict. Not conformity assessment. Not CE marking. Not a notified-body opinion.**

Retains [`review-method-1.2.0.md`](review-method-1.2.0.md), [`review-method-1.1.1.md`](review-method-1.1.1.md), [`review-method-1.1.0.md`](review-method-1.1.0.md), and [`review-method-1.0.0.md`](review-method-1.0.0.md) for historical comparison records.

**1.3.0 delta:** `parent_record_digest` (set from `--since` prior before `record_digest`); citation currency fields on pack citations + packs doctor unverified/stale (exit 0); classifier may be `refclass:2` on the same release train.

## 1. Scope

This method reports on the **document** (structure, digest self-consistency, reference resolvability). It does **not** determine product fitness, legal conformity, or accreditation status.

An **edge** exists only when a reference target was found (or explicitly classified as external/unresolved). There is **no similarity, fuzzy match, threshold, or confidence score** on an edge. Outcomes remain `confirmed` / `unconfirmed` / `contradicted` only.

## 2. Inputs

### Bundle mode (default)

Required layers (must be present, non-empty, non-symlink):

- `01-gate-failures.json`
- `02-action-report.md`
- `03-executive-summary.md`
- `buyer-onepager.html`

Optional structure layers (absence is unconfirmed/producer, not contradicted): SBOM/VEX/SARIF/watchlist join, `context-pack.json`, `buyer-questions.md`, `hpurl-pointer.json` (optional; supplies `subject_state_hash` when present).

`context-pack.json` is **not** a reference/triage surface.

### Repository mode (`ReferencesOnly`)

Caller supplies triage surfaces (CLI: governed documentation targets from composed packs; optional `--packs` override; cold default without `.curbpack.json` is `house-policy`). Pack-layer structure/load/digest checks are skipped. Missing governed surfaces emit `structure:surface-absent:<path>` (unconfirmed/producer).

CLI supplies `subject_commit` from git HEAD. `subject_state_hash` is empty unless share copied `.github/curbpack/evidence/hpurl-pointer.json` into `review-pack/`.

**Fixed ignore list** (no `.gitignore` parser) — directories skipped via `filepath.SkipDir`:

- `.git/`
- cache / evidence / graph dirs (write-new and legacy path helpers)
- `review-pack/`
- `node_modules/`, `vendor/`, `dist/`, `build/`, `target/`, `.venv/`

## 3. Classification

States: `confirmed` | `unconfirmed` | `contradicted`.

Causes:

- Unconfirmed: `producer` | `extractor` | `genuine` | `external`
- Contradicted: `self_disagree`

Reference edges carry `source` (the document the reference was extracted from). Non-edge findings omit `source`.

## 4. Reference resolution

A reference is a claim the triage surfaces make about the system under review: a pack claim id, a path-shaped artifact pointer, or an external URL.

**Markup, booleans, JSON keys, versions, and truncated hashes are not references.**

Default triage surfaces (bundle): `02-action-report.md`, `03-executive-summary.md`, `buyer-questions.md`, `buyer-onepager.html`. External URLs are recorded and never fetched.

Repo-mode Detail wording uses `in-repo …` / `path not found in repo:` prefixes; bundle-mode wording remains `in-bundle …` / `repo-shaped path not in bundle:`. Wording alone does not bump this method version.

## 5. Subject chaining (1.3.0)

Every report may carry additive producer anchors (empty when absent):

| Field | Bundle mode | Repo mode |
|-------|-------------|-----------|
| `subject_commit` | `01-gate-failures.json` → `concurrency_control.expected_parent_commit_sha` | CLI `gitutil.HeadSHA` → `Options.SubjectCommit` |
| `subject_state_hash` | `hpurl-pointer.json` → `state_hash` when present in bundle root | `review-pack/hpurl-pointer.json` after share; empty when absent |

`internal/review` never calls git. HPURL fragments (`#?h=&p=&s=`) render on CLI stderr only — not stored on `Report`.

## 6. Digests

Placement inside `Run`: after airlock → tally → sortFindings, **immediately before** emit. If a refuse-oversize finding is appended, tally + sortFindings run again before `record_digest`.

`digest_scope` is always recorded: `bundle` | `closure`. **Never compare digests across scopes.**

`triage_surfaces` (sorted) and `surfaces_digest` are always recorded from `ResolveTriageSurfaces` — same comparability class as `digest_scope`. Two `--packs` runs are not comparable unless these fields match.

One digest algorithm for both scopes: sorted length-prefixed relative paths, each followed by the length-prefixed sha256 of full file contents (streamed via a single pass per file). Scope differs only by which paths are included (`bundle` walk vs `closure` union). If any digest path is unreadable or skipped, emit contradicted `structure:digest-incomplete` and leave `bundle_digest` empty — never silently omit paths.

### `bundle_digest` when `digest_scope=bundle`

sha256 over sorted relative slash paths; each path is length-prefixed, then the length-prefixed sha256 of the **full** file contents (streamed; not subject to the per-file parse read cap). Symlinks and out-of-jail paths are excluded.

### `bundle_digest` when `digest_scope=closure`

sha256 over the sorted union of (a) surface documents actually read and (b) repo-relative paths that path-references resolved to. URLs and claim ids contribute nothing. Unresolved path references contribute nothing — so a file appearing later changes the closure.

### `surfaces_digest`

sha256 over sorted length-prefixed surface path strings (same length-prefix encoding as other method digests).

**Refuse-oversize ceiling (64 MiB total):** unchanged from 1.0.0 — contradicted `structure:bundle-size-cap`, empty digest, never truncate.

### `record_digest`

sha256 of the canonical JSON `Report` with `record_digest` and `bundle_root` set to empty strings.

### `parent_record_digest` (1.3.0)

When the caller supplies a prior report (`--since`), the engine copies the prior `record_digest` into `parent_record_digest` **before** computing the child `record_digest` (so the parent is inside the hashed JSON). Empty when no prior is supplied.

**Verify chain (CLI):** `curbpack review --verify-chain <parent.json> <child.json>` exits 0 iff both reports' `record_digest` values match independently recomputed digests and `child.parent_record_digest` equals the recomputed parent digest (all non-empty); exit 1 on empty, claim/recompute mismatch, or chain break.

## 7. Exit codes

- `0` — no contradicted findings in the current report (or `--verify-chain` match)
- `1` — any contradicted finding (or `--batch` child unreadable/contradicted; or `--verify-chain` break)
- `2` — usage/env (including unreadable / oversized / schema-mismatched `--since` prior)

`--since` never changes the exit condition for NEW findings. Cross-`method_version` comparison prints a recorded warn and still diffs.

## 8. Governance — packs vs check kinds

**Packs are infinitely malleable. The nine check kinds are frozen.**

The nine: `annex_file`, `file_present`, `anti_placeholder`, `npm_dep_ban`, `manifest_dep_ban`, `text_forbid`, `import_reach`, `fresh`, `owned`.

## 9. Comparison scheme

Frozen input: `testdata/comparison-bundle-2026-1/`. Expected `record_digest` is published beside this document. Divergence means a different tool version, a modified tool, or altered input — never “operator variation.”
