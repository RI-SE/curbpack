# Pilot decision log (template)

Capture equivalence and disposition learning **beside** Receipt v0. No registry or graph — first dataset is this table / JSON.

Not conformity assessment. Decisions are human; the receipt is a structural index.

## Entries

| Field | Entry 1 | Entry 2 |
|-------|---------|---------|
| Criterion | | |
| Requested evidence | | |
| Supplied evidence | | |
| Equivalent proposed | | |
| Recipient decision | | |
| Limitation | | |
| Reusable or context-specific | | |

## How to use

1. Run `./scripts/pilot-receipt.sh <request.json>` (or assemble from fixtures).
2. Structurally validate the receipt ([minimum-receipt-fixture](minimum-receipt-fixture.md)).
3. Fill one row per criterion / exception.
4. Optional machine-readable copy: `testdata/receipt/pilot-decision-log.json`.

Claim boundary: do not record “compliant”, “certified”, or “CE” outcomes — use accept / reject / defer / equivalent-accepted for a stated purpose.
