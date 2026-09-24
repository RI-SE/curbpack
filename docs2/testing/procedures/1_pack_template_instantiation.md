# 1. Pack inputs

This file defines the `PF-*` dimension of the
[controlled test prerequisites](README.md).

On the reference product, a PF-id names one exact prepared input. After
`setup.sh` has prepared the R-state, select it with:

```sh
cd "$REFERENCE_PRODUCT_ROOT"
./external_test/curbpack/mutate_pack.sh PF-xx
```

`PF-xx` is the only argument. The script copies finished files from
`external_test/curbpack/pf-fixtures/PF-xx/` onto this disposable checkout.
It does not clone, select a revision, create a branch, stage, or commit.
It does not export `CURBPACK_PACKS_DIR`. `verification-run.sh` already
points that variable at `external_test/curbpack/packs`. If a case needs
`--packs`, it keeps that argument.

Default committed packs are PF-01. Call `mutate_pack.sh` when the case
names a different PF, or when a previous PF on the same checkout must be
replaced. Each PF restores its documented input regardless of the previous
selection.

Pack-template instantiation onto a third repository is **not yet
specified**. Do not invent commands, fields or instantiation steps for
that path. Applying the same suites to another target repository is part
of the verification model but is NOT CURRENTLY EXECUTABLE until a
documented, repeatable pack-instantiation mechanism exists.

How to start a verification run is [Prepare a verification run](README.md#prepare-a-verification-run).

<a id="pf-01"></a>

## PF-01

Glucose Log carries frozen pack *copies* and claim maps under
`external_test/curbpack/packs/` (`house-policy`, `cra-baseline`,
`medtech-iec62304`). Same pack ids as embed, so:

```bash
export CURBPACK_PACKS_DIR=/path/to/cyberready-test-product/external_test/curbpack/packs
curbpack check
```

That is the reference-product pack set. It is not instantiation onto a
third repository and not a pack-template product.

`.curbpack.json` on Glucose Log still lists `house-policy` and
`medtech-iec62304` (CRA via `extends`).

Used by: Curbpack, CTAM

CTAM-owned pack inputs live in the product `external_test/ctam/` tree and
are defined in CTAM `docs/testing/procedures.md`. Do not add those ids here.

## Pack input registry

`PF ID | prepared input | source files → destination | testcase(s)`

| PF ID | Prepared input | Source files → destination | Testcase(s) |
|---|---|---|---|
| PF-01 | Reference pack baseline: `house-policy`, `cra-baseline`, `medtech-iec62304` | `pf-fixtures/PF-01/{house-policy,cra-baseline,medtech-iec62304}/*` and `SOURCE.txt` → `external_test/curbpack/packs/` | Default for EV-001 and other PF-01 cases; PK-001 via EV-001 |
| PF-02 | Second representative instantiated product pack | — | NOT YET SPECIFIED. Reserved. Do not reuse this id. |
| PF-03 | Unknown check type (`llm_judge`) | `pf-fixtures/PF-03/unknown-check/pack.json` → `packs/unknown-check/pack.json` | PK-004 |
| PF-04 | Invalid regular expression | `pf-fixtures/PF-04/bad-regex/pack.json` → `packs/bad-regex/pack.json` | PK-005 |
| PF-05 | Relative path traversal | `pf-fixtures/PF-05/path-traversal/pack.json` → `packs/path-traversal/pack.json` | FS-001 |
| PF-06 | PF-01 with one trailing space on `house-policy/pack.json` | `pf-fixtures/PF-06/house-policy/pack.json` → `packs/house-policy/pack.json` | PV-006 |
| PF-07 | `fresh-owned-test` | `pf-fixtures/PF-07/fresh-owned-test/pack.json` → `packs/fresh-owned-test/pack.json` | EV-007-G, EV-007-H |
| PF-08 | EV-008 pack, ALPHA before BETA | `pf-fixtures/PF-08/ev-008-rule-order-a/pack.json` → `packs/ev-008-rule-order-a/pack.json` | EV-008-A pack A |
| PF-09 | EV-008 pack, BETA before ALPHA | `pf-fixtures/PF-09/ev-008-rule-order-b/pack.json` → `packs/ev-008-rule-order-b/pack.json` | EV-008-A pack B |
| PF-10 | Review Pack with `expected_parent_commit_sha` set to 40 `b` characters | `pf-fixtures/PF-10/*` → `external_test/curbpack/review-pack-input/` | RP-003 |
| PF-11 | Review Pack with the `HOUSE-SECURITY-MD` line removed from the executive summary | `pf-fixtures/PF-11/*` → `review-pack-input/` | RP-004 |
| PF-12 | Review Pack with truncated `01-gate-failures.json` (`{` and a newline) | `pf-fixtures/PF-12/*` → `review-pack-input/` | RP-005 |
| PF-13 | Malformed `house-policy` JSON (comma after `"version"` removed; otherwise PF-01 `house-policy` bytes) | `pf-fixtures/PF-13/house-policy/pack.json` → `packs/house-policy/pack.json` | PK-002-A |
| PF-14 | Truncated `house-policy` JSON (first 120 bytes of the PF-01 `house-policy` file) | `pf-fixtures/PF-14/house-policy/pack.json` → `packs/house-policy/pack.json` | PK-002-B |
| PF-15 | PF-01 `house-policy` with an identical duplicated `HOUSE-SECURITY-MD` rule | `pf-fixtures/PF-15/house-policy/pack.json` → `packs/house-policy/pack.json` | PK-003-A |
| PF-16 | PF-01 `house-policy` with conflicting `HOUSE-SECURITY-MD` definitions, original then `docs/pk003-absent.md` | `pf-fixtures/PF-16/house-policy/pack.json` → `packs/house-policy/pack.json` | PK-003-B |
| PF-17 | Same conflicting definitions as PF-16, order reversed | `pf-fixtures/PF-17/house-policy/pack.json` → `packs/house-policy/pack.json` | PK-003-C |

Valid controls: PF-01 is the valid `house-policy` control for PF-13–PF-17.
PF-13 differs by one missing comma (invalid JSON, not a prefix). PF-14 is
that same file cut to 120 bytes. PF-15 duplicates one rule object. PF-16
and PF-17 keep both conflicting objects and only change order.

No PF is assigned for conflicting versions of the same pack identity.
There is no documented version-selection syntax. Observed `extends`
later-wins behaviour is not a PASS criterion.

RP-004's catalogue title mentions a stale digest. The prepared input is
only the removed-finding summary (PF-11). Do not invent a digest fixture.

## When templates land

Replace the not-yet-specified third-repository procedure with documented
instantiate-and-adapt steps only after that mechanism exists. Do not copy
Glucose Log files into a customer repository as a substitute for templates.
