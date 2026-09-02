# Reserved `edges` array — product release calendar

> Maintainer note. Structural evidence for human review — not conformity assessment.

## Reservation

[`docs/stable-contracts.md`](../stable-contracts.md) reserves an optional Report `edges` array. Schema is **frozen** in Shared Frame §6 TO (0b **DECIDED**). Curbpack **ingest** is implemented: `review --repo --json --edges <file>` (no synthesis). CTAM owns export. Do not invent §6 TO fields.

## Expiry

| Item | Rule |
|------|------|
| Name | `edges` (JSON field on review Report) |
| Status | Schema frozen + curbpack ingest shipped; **end-to-end** CTAM round-trip still unused |
| Expires | **curbpack product release v0.6.0** if still unused end-to-end |
| Action on expiry | **Delete** the reservation (CONTRIBUTING “delete rather than deprecate”) — do not leave folklore |

## Decision at v0.6.0

- If still unused end-to-end → remove the reserved row from stable-contracts and any calendar pointer.
- If a partner round-trip lands before then → keep the shipped contract; update this calendar accordingly.

_Not a product verdict. Not a greenlight to invent §6 TO fields._
