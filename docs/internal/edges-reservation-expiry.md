# Reserved `edges` array — product release calendar

> Maintainer note. Structural evidence for human review — not conformity assessment.

## Reservation

[`docs/stable-contracts.md`](../stable-contracts.md) reserves an optional Report `edges` array that is **not implemented**. Do not repurpose the name.

## Expiry

| Item | Rule |
|------|------|
| Name | `edges` (JSON field on review Report) |
| Status | Reserved / unused |
| Expires | **curbpack product release v0.6.0** if still unused |
| Action on expiry | **Delete** the reservation (CONTRIBUTING “delete rather than deprecate”) — do not leave folklore |

## Decision at v0.6.0

- If still unused → remove the reserved row from stable-contracts and any calendar pointer.
- If implemented before then → replace this stub with the shipped contract and bump method docs accordingly.

_Not a product verdict. Not a greenlight to implement `edges` early._
