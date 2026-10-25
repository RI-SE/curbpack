# EP-05 — Packs v2 copies of the test Packs

**Status:** Done. Does not edit the reference product.

**Goal:** `python3 -m checks --packs docs/reference/test-packs` loads Pack ids `cra-baseline`, `house-policy`, and `medtech-iec62304`.

## Stories

| ID | User goal | Starts when |
| --- | --- | --- |
| [PK2-01](stories/PK2-01-transform-test-packs.md) | Transform those three Packs from the old format into Packs v2 | Done |

TST-01 and REF-01 stay blocked until PK2-01 is accepted. Accepting PK2-01 does not allow an edit under `cyberready-test-product`. REF-01 also waits for TST-01.

## Epic acceptance

- The only new tree is `docs/reference/test-packs/`: `cra-baseline/`, `house-policy/`, `medtech-iec62304/`, `claims/`, and `SOURCE.txt`.
- Each `packs` directory is `pack.json` plus Requirement files, as `docs/reference/packs2.md` specifies. Claim files are under `docs/reference/test-packs/claims/`, not inside a Pack directory.
- Unknown schema or a missing `pack.json` fails the story. This epic writes no `signed` block and no key. `SOURCE.txt` records that `signed` was not written. A Check `fail` because a product file is absent does not fail the transformation.

## Out of scope

`docs/testing/`, `daniel/ny_sdd/`, application code, and `cyberready-test-product`.
