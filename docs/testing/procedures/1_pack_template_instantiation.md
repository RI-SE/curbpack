# 1. Pack inputs

A PF-id is one prepared pack input. On the reference product the selector is:

```sh
./external_test/curbpack/mutate_pack.sh <PF-id>
```

That script copies `external_test/curbpack/pf-fixtures/<PF-id>/` onto the checkout. This file does not replace that script. This suite does not edit it.

The Studio runner does not read `CURBPACK_PACKS_DIR` or `.curbpack.json`. For PF-01 it loads pack ids from `--packs docs/reference/test-packs` and the `packs` array in `curbpack.json`.

PF-18 and PF-19 are not in this file. Their product effects stay in `ctam/docs/testing/procedures.md`. Both ids are in [outside.md](../outside.md).

## PF-01

Pack ids `house-policy`, `cra-baseline`, and `medtech-iec62304`.

The carried cases use this id. The files are `docs/reference/test-packs/<pack-id>/pack.json` and the requirement files next to it. Claim files for the seven carried cases are copied into the temporary repo's `claims/` directory. They are not inside the pack directory.

## PF-02

Reserved. Not specified. `mutate_pack.sh PF-02` is refused. Not a carried case.

## PF-03

Unknown check type `llm_judge`, copied to `packs/unknown-check/pack.json`. Not a carried case.

## PF-04

Invalid regular expression, copied to `packs/bad-regex/pack.json`. Not a carried case.

## PF-05

Relative path traversal, copied to `packs/path-traversal/pack.json`. Not a carried case.

## PF-06

PF-01 with one trailing space on `house-policy/pack.json`. Not a carried case.

## PF-07

Pack `fresh-owned-test`. Not a carried case.

## PF-08

EV-008 pack, ALPHA before BETA. `pf-fixtures/PF-08/ev-008-rule-order-a/pack.json` is copied to `packs/ev-008-rule-order-a/pack.json`. Not a carried case.

## PF-09

EV-008 pack, BETA before ALPHA. `pf-fixtures/PF-09/ev-008-rule-order-b/pack.json` is copied to `packs/ev-008-rule-order-b/pack.json`. Not a carried case.

## PF-10

Review Pack whose `expected_parent_commit_sha` is 40 `b` characters, under `external_test/curbpack/review-pack-input/`. Not a carried case.

## PF-11

Review Pack with the `HOUSE-SECURITY-MD` line removed from the executive summary. Not a carried case.

## PF-12

Review Pack with truncated `01-gate-failures.json`: `{` and a newline. Not a carried case.

## PF-13

Malformed `house-policy` JSON: the comma after `"version"` removed. Not a carried case.

## PF-14

Truncated `house-policy` JSON: the first 120 bytes of the PF-01 `house-policy` file. Not a carried case.

## PF-15

PF-01 `house-policy` with an identical duplicated `HOUSE-SECURITY-MD` rule. Not a carried case.

## PF-16

Conflicting `HOUSE-SECURITY-MD` definitions, original then `docs/pk003-absent.md`. Not a carried case.

## PF-17

The same conflicting definitions as PF-16, order reversed. Not a carried case.

PF-01 is the valid `house-policy` control for PF-13 through PF-17. No PF is assigned for conflicting versions of the same pack identity.
