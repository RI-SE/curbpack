# OUT-01 — One row per id the suite did not carry

**Epic:** [EP-08 Cases outside the Studio way](../EPIC.md)

**Starts when:** DOC-03 and TST-01 are accepted, and `docs/testing/outside.md` exists. REF-01 does not wait on this story. Do not edit `docs/testing/README.md` beyond the one link line below, and do not edit it in parallel with another story.

**As a developer**, I want every id TST-01 left outside the suite to have one disposition, so a gap is not a pass and a new obligation does not reuse an old `MUST-*`.

## Read

- `docs/testing/outside.md`
- `daniel/ny_sdd/docs/REQUIREMENTS.md` and `daniel/ny_sdd/docs/baseline-delta.md`
- `/Users/DanielFl/Documents/aProjects/aslak/curbpack/docs/testing/requirements_traceability.md`
- `/Users/DanielFl/Documents/aProjects/aslak/ctam/docs/testing/procedures.md`

## Write only

`docs/testing/outside-disposition.md`, and one line in `docs/testing/README.md`:

`Outside cases: docs/testing/outside-disposition.md`

Do not rewrite suite procedures. Do not edit `daniel/ny_sdd/`. Do not edit the reference product. Do not edit application code.

## Accept when

- The row key is the id from `docs/testing/outside.md`. Every such id appears once.
- The disposition is one of the five statuses in the epic. A Packs v2 field is the blocked status. Name the field. Do not add it.
- `R8`, `R9`, `PF-18`, and `PF-19` are each either absent from `outside.md` because TST-01 carried them, or present here.
- No row says Pass.
- The outside-id count and the row count are written on `outside-disposition.md` and are equal.

## Definition of done

Those two counts are equal. The README contains that one link line and no other edit from this story. The diff of this story in `cyberready-test-product` is empty.

## Stop if

The honest status is "this case requires a Packs v2 field". Use the blocked status, name the field, and stop. Do not add the field.
