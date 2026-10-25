# EP-08 — Cases outside the Studio way

**Status:** Draft. Starts when DOC-03 and TST-01 are accepted. Does not block EP-07. Does not edit `cyberready-test-product`.

**Goal:** Every id in `docs/testing/outside.md` has one row in `docs/testing/outside-disposition.md`. No row is a pass.

## Stories

| ID | User goal | Starts when |
| --- | --- | --- |
| [OUT-01](stories/OUT-01-disposition.md) | Dispose every id TST-01 did not carry | DOC-03 and TST-01 are accepted |

## Epic acceptance

Each id in `docs/testing/outside.md` has one row in `docs/testing/outside-disposition.md`. The row status is one of:

- still required, with the DOC-02 id, and no Check name
- simplified away, with the `daniel/ny_sdd/docs/baseline-delta.md` id
- not a curbcheck requirement, with the DOC-02 reason and where the obligation went
- new Studio requirement, with the DOC-02 id that is marked new
- blocked on a Packs v2 field, naming the field and not adding it

The outside-id count and the row count are written on `outside-disposition.md` and are equal. Nothing in this epic is a passing test.

## Out of scope

Implementing a new requirement. Editing the reference product. Editing `daniel/ny_sdd/` except by citation. Rewriting suite procedures.
