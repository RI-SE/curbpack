# DOC-02 — Keep the requirement list

**Epic:** [EP-04 Studio documentation truth](../EPIC.md)

**Status:** Done. The list, the ids, and the moved requirement text are in `daniel/ny_sdd/docs/REQUIREMENTS.md`.

**Starts when:** DOC-01 is accepted.

**As a developer**, I want the requirement list from the moved `docs/REQUIREMENTS.md` kept, with every matrix id and its substance, so a test case can still cite it.

## Read

`daniel/ny_sdd/docs/REQUIREMENTS.md` from DOC-01. `/Users/DanielFl/Documents/aProjects/aslak/curbpack/docs/testing/requirements_traceability.md`, every row.

## Write only

`daniel/ny_sdd/docs/REQUIREMENTS.md`.

## Accept when

- Every requirement id in the matrix is a requirement in that file, including an id the moved text omitted. The id is unchanged.
- The substance of the moved requirement stays with that id. A later story may say the behavior was simplified or missed. This story does not delete the requirement.
- Next to the list, the matrix row count and the count of requirements whose id came from the matrix are equal. A new id does not reuse a `MUST-*` id and is outside that count.
- The file does not say a requirement passed because a test once existed.

## Definition of done

The two counts are equal. The commit contains only `daniel/ny_sdd/docs/REQUIREMENTS.md`.

## Stop if

Keeping the substance would require a Packs v2 field `docs/reference/packs2.md` does not define. Leave the requirement in place and stop that id. Do not add the field.
