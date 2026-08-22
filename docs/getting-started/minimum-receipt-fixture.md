# Minimum receipt fixture (Receipt v0)

Receipt v0 is a **thin index** over artefacts Curbpack already produces (`check`, `export` / `share`, fingerprints). It is not a second evidence system and not a new CLI verb.

Not conformity assessment. Structural evidence for human review only.

## Schema (`curbpack-receipt:0`)

| Field | Required | Notes |
|-------|----------|--------|
| `schema` | yes | `"curbpack-receipt:0"` |
| `claim` | yes | Claim-safe boundary sentence |
| `request_id` | yes | Matches pilot request |
| `profile` | yes | `{ "pack_id", "digest" }` — digest when locally known |
| `repository` | yes | `{ "commit" }` HEAD at assembly |
| `artefacts` | yes | `[{ "path", "sha256" }]` relative paths + hashes |
| `assertions` | yes | Labelled structural statements (no certification verbs) |
| `exceptions` | yes | Array (may be empty) |
| `limitations` | yes | Array (may be empty) |
| `evaluator` | yes | `{ "id": "curbpack-native", "version", "method": "deterministic" }` |
| `generated_at` | yes | RFC3339 UTC |

## Structural verification (narrow)

Local checks only:

1. Schema id and required fields present.
2. Internal refs: `request_id` matches request fixture when provided; artefact paths exist when verifying in-repo.
3. Digests: recompute `sha256` for artefacts that are **locally available**; skip remote-only subjects.

Cannot verify a repository or profile that is not available to the verifier.

## Fixtures

| Path | Role |
|------|------|
| `testdata/receipt/pilot-request.json` | Buyer request |
| `testdata/receipt/pilot-response-a.json` | Supplier A response sketch |
| `testdata/receipt/pilot-response-b.json` | Supplier B response sketch |
| `testdata/receipt/pilot-disposition.json` | Human disposition stub |
| `testdata/receipt/pilot-decision-log.json` | Optional decision-log example |

## Pilot entrypoint

```bash
./scripts/pilot-receipt.sh testdata/receipt/pilot-request.json
# optional: CURBPACK_BIN=./bin/curbpack OUT_DIR=/tmp/receipt-out ./scripts/pilot-receipt.sh …
```

Orchestrates: `check` → `export --context-pack` (and/or `share`) → fingerprint artefacts → assemble `receipt.json` → structural validate. Fails clearly on missing tools, red check (unless `ALLOW_RED=1`), or validation errors.

Helpers: `scripts/lib/receipt_v0.py` (`assemble` / `validate`).
