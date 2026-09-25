# Minimum receipt fixture (Receipt v0)

Receipt v0 is a **thin index** over artefacts Curbpack already produces (`check`, `export` / `share`, fingerprints). It is not a second evidence system and not a new CLI verb.

Not conformity assessment. Structural evidence for human review only.

## Two shapes (not competing protocols)

| Schema | Role |
|--------|------|
| `curbpack-pilot-request:0` | Workshop **buyer input** — stated purpose + criteria |
| `curbpack-pilot-response:0` | Workshop **supplier response sketch** — what a supplier might return |
| `curbpack-receipt:0` | **Generated artefact index** from `./scripts/pilot-receipt.sh` |

**Mapping:** request → (optional dual) responses → human disposition / decision-log → receipt. The request and response fixtures are workshop sketches for the RI-SE pilot conversation. The receipt is the machine-assembled index over local `check` / `export` / `share` artefacts for one repository run. They share claim-safe language and `request_id` linkage; they are **not** alternate encodings of the same protocol.

## Schema (`curbpack-receipt:0`)

| Field | Required | Notes |
|-------|----------|--------|
| `schema` | yes | `"curbpack-receipt:0"` |
| `claim` | yes | Claim-safe boundary sentence |
| `request_id` | yes | Matches pilot request |
| `profile` | yes | `{ "pack_id", "digest" }` — digest is **pack/profile bytes** only (see below) |
| `repository` | yes | `{ "commit" }` HEAD at assembly |
| `artefacts` | yes | `[{ "path", "sha256" }]` relative paths + hashes (ContextPack lives here) |
| `assertions` | yes | Labelled structural statements (no certification verbs) |
| `exceptions` | yes | Array (may be empty) |
| `limitations` | yes | Array (may be empty) |
| `evaluator` | yes | `{ "id": "curbpack-native", "version", "method": "deterministic" }` |
| `generated_at` | yes | RFC3339 UTC |

### `profile.digest` (pack bytes only)

- **Identifies** resolved pack/profile bytes when deterministically available: `packs/<id>/pack.json`, else `internal/packs/data/<id>/pack.json` (or `CURBPACK_PACKS_DIR/<id>/pack.json`).
- **Never** a ContextPack / other run-export hash — those belong only under `artefacts[]`.
- If pack bytes cannot be hashed: `"digest": null` and `"digest_status": "unavailable"`. Do not substitute an export hash. Validate does not require a pack digest when `digest_status` is `unavailable`.

## Structural verification (narrow)

Local checks only:

1. Schema id and required fields present.
2. Internal refs: `request_id` matches request fixture when provided; artefact paths exist when verifying in-repo.
3. Digests: recompute `sha256` for artefacts that are **locally available**; when `profile.digest` is set, recompute against pack.json (not ContextPack). Skip remote-only subjects. Pack digest not required when `digest_status` is `unavailable`.

Cannot verify a repository or profile that is not available to the verifier.

## Fixtures

| Path | Schema | Role |
|------|--------|------|
| `testdata/receipt/pilot-request.json` | `curbpack-pilot-request:0` | Buyer / workshop input |
| `testdata/receipt/pilot-response-a.json` | `curbpack-pilot-response:0` | Supplier A response sketch |
| `testdata/receipt/pilot-response-b.json` | `curbpack-pilot-response:0` | Supplier B response sketch |
| `testdata/receipt/pilot-disposition.json` | (disposition stub) | Human disposition |
| `testdata/receipt/pilot-decision-log.json` | `curbpack-pilot-decision-log:0` | Optional decision-log example |

Generated receipt (not a committed fixture): `.github/curbpack/cache/pilot-receipt/receipt.json` from `pilot-receipt.sh` — schema `curbpack-receipt:0`.

## Pilot entrypoint

```bash
./scripts/pilot-receipt.sh testdata/receipt/pilot-request.json
# optional: CURBPACK_BIN=./bin/curbpack OUT_DIR=/tmp/receipt-out ALLOW_RED=1 ./scripts/pilot-receipt.sh …
```

Orchestrates: `check` → `export --context-pack` (and/or `share`) → fingerprint artefacts → assemble `receipt.json` → structural validate. Fails clearly on missing tools, red check (unless `ALLOW_RED=1`), or validation errors.

Helpers: `scripts/lib/receipt_v0.py` (`assemble` / `validate` / `resolve-pack-digest`).
