# PK2-01 — Transform the three test Packs

**Epic:** [EP-05 Packs v2 copies of the test Packs](../EPIC.md)

**Status:** Done.

**Starts when:** now. This story does not wait on DOC-01 or DOC-02. TST-01 and REF-01 wait on this story. This story does not edit the reference product.

**As a tester**, I want the three Packs in `docs/reference/test-packs` in Packs v2 form, so Studio's checker can load those ids.

## Read

- `docs/reference/test-packs/cra-baseline`
- `docs/reference/test-packs/house-policy`
- `docs/reference/test-packs/medtech-iec62304`
- `docs/reference/packs2.md`. Claims are product-repo files, not files inside the Pack directory.

## Write only

`docs/reference/test-packs/cra-baseline/`, `docs/reference/test-packs/house-policy/`, `docs/reference/test-packs/medtech-iec62304/`, `docs/reference/test-packs/claims/`, and `docs/reference/test-packs/SOURCE.txt`.

Each Pack directory contains `pack.json` and Requirement files. Each source Claim becomes one JSON file under `claims/` with `checks[]` entries of `{check, args}`. Do not put a Claim file inside a Pack directory. Do not write a `signed` block. `.walkthrough-test/` is not this directory.

## Proof

Create a temporary product repo. Its `curbpack.json` lists the three ids. Copy `docs/reference/test-packs/claims/` into that repo's `claims/`. Run:

```sh
python3 -m checks --repo <temp> --packs docs/reference/test-packs --out <temp>/.curbpack/run-result.json
```

The `--out` file contains exactly three `packs[]` entries, ids `cra-baseline`, `house-policy`, and `medtech-iec62304`, each with `id`, `version`, and `digest`. Unknown schema or a missing `pack.json` fails the story. A Check `fail` because a product file is absent is written into `SOURCE.txt` and does not fail the transformation. Delete the temporary repo. Do not commit it.

## Accept when

`SOURCE.txt` records the Curbpack commit, the count of source Pack ids, Requirement ids, and Claim ids, the count present after transformation, and one absence row per missing id with the reason. Present plus absence equals source. It also records that no `signed` block was written.

## Definition of done

The proof command produces those three `packs[]` entries. Commits for this story contain only paths under `docs/reference/test-packs/`.

## Stop if

A source field has no Packs v2 home. Do not invent the field. Add an absence row and stop that object.
