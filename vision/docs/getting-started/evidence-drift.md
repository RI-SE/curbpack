# Evidence drift (human checklist)

`curbpack drift` is a **multi-signal human checklist** — not a compliance meter. Exit code is **always 0** (informational). There is no boolean `aligned`, `no_drift`, `pass`, or `green` summary.

Golden path context: `install → doctor → init → check → share [--bundle] → (human) attest → proof verify`. Run drift when you wonder whether evidence still matches the tree.

## How last attest is found

Resolution order (shared with buyer one-pager / export):

1. `.github/curbpack/evidence/hpurl-pointer.json` → verify Git Notes on that commit
2. Fallback: `git log -1 --notes=curbpack` (then legacy `cyberready` notes)

If nothing found → signal `attest_none` (not an error).

## Signal IDs

### Attest vs HEAD

| Signal ID | When | Human hint |
|-----------|------|------------|
| `attest_none` | No bind found | Run human `attest` when ready |
| `attest_commit_behind` | Bind commit ≠ HEAD | Code moved since bind — re-check, re-share, human re-attest |
| `attest_commit_current` | Bind commit = HEAD | Informational only — not “no drift” |

### Gate cache (cache-only; no validate.Run)

| Signal ID | When |
|-----------|------|
| `check_cache_missing` | No `latest_result.json` / `latest_failure.json` |
| `check_commit_stale` | Cache `concurrency_control.expected_parent_commit_sha` ≠ HEAD |
| `check_cache_present` | Cache exists and OCC parent matches HEAD |

### Share fingerprint (cache-only)

| Signal ID | When |
|-----------|------|
| `share_no_review_pack` | `review-pack/buyer-onepager.html` missing |
| `share_stale` | On-disk `<!-- curbpack-onepager-fp:… -->` ≠ expected from cache+bind |
| `share_current` | Fingerprints match |
| `share_cache_missing` | No cache JSON — run `check` or `share` |

### Other (informational)

| Signal ID | When |
|-----------|------|
| `state_hash_mismatch` | Bind `state_hash` ≠ `ComputeStateHash(HEAD, …)` — never sole “aligned” indicator |
| `state_hash_current` | Bind hash matches HEAD compute |
| `working_tree_clean` | No uncommitted changes |
| `working_tree_dirty` | Uncommitted changes present |
| `working_tree_unknown` | Git status failed — fail-safe |

### Pack docs vs attest bind

Paths come from composed pack rules (`Path` / `Paths` on `annex_file` / `file_present` / `anti_placeholder`) — the same set as `pathway confirm-prose`. Compared with `git diff --name-only <bind> HEAD -- <paths>`. Detail lists at most ~12 paths. Not emitted when there is no bind.

| Signal ID | When | Human hint |
|-----------|------|------------|
| `docs_unchanged_since_attest` | Pack paths did not move since bind | Informational only — not “no drift” |
| `docs_changed_since_attest` | One or more pack paths moved | Re-check, re-share, human re-attest |

### security.txt (optional; not a gate)

Emitted only when `.well-known/security.txt` exists. Never a check pass/fail.

| Signal ID | When |
|-----------|------|
| `contact_expires_past` | `Expires:` parses and is in the past |
| `contact_missing` | No non-empty `Contact:` line |

## Output

- Default: human table of signal rows + optional `suggested_actions[]`
- `--json`: `schema: curbpack-drift-report:1`, `signals[]`, `suggested_actions[]`

After `curbpack check`, when a bind exists behind HEAD, one dim line may appear (same cap as accumulation whispers).

See also: [Stable contracts](../stable-contracts.md) · [Daily loop](daily-loop.md) · [Buyer evidence](buyer-evidence.md)
