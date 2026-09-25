# 0. Repository Content States

This file defines the `R-*` dimension of the
[controlled test prerequisites](README.md).

## What This Is

Many test suites run Curbpack against a Git repository and check whether the
selected pack rules produce the expected result. Positive and negative tests
use [Glucose Log](https://github.com/RI-SE/cyberready-test-product) as the
**reference test product**. The repository contains product-specific pack
copies, claim descriptions and scripts for preparing known repository states.

This document describes the named repository states **R1–R7** that are used
when running the actual test cases. An R-id names the complete prepared
repository state a testcase needs. That includes:

- repository content;
- required file presence, absence, or modification;
- the Git repository state needed as the starting condition; and
- initialization, staging, committing, checkout, or cleaning required to
  establish that state.

R is not “reference-product state” in general, and it is not defined by
which script happens to prepare it. Every R-state is prepared on the same
disposable checkout:

```sh
"$CURBPACK_ROOT/tmp/cyberready-test-product"
"$REFERENCE_PRODUCT_ROOT"
```

No R-state may create or use a separate repository such as `tmp/R4` or
`tmp/R5`.

The scripts that create those states are stored in the test product under
[`external_test/curbpack/`](https://github.com/RI-SE/cyberready-test-product/tree/main/external_test/curbpack).

The files in that directory have distinct purposes:

- `states/<ID>.sh` prepares or verifies one state on
  `"$REFERENCE_PRODUCT_ROOT"`;
- `setup.sh` applies the selected R-state to that already-checked-out
  frozen revision; it does not select a commit, branch, tag, pin, or other
  revision. `SUT` defaults to `curbpack`. A missing script file is an error;
- `mutate_pack.sh` installs one named PF from `pf-fixtures/` onto this
  checkout; it does not prepare an R-state;
- `reset.sh` is present in the product directory and is not part of the
  normal case sequence; and
- `states.md` is the product-side script registry. It must not redefine
  what an R-id means; this document remains normative.

CTAM-owned states live in the product `external_test/ctam/` tree and are
defined in CTAM `docs/testing/procedures.md`. Do not add those ids here.

This document and those files must be updated together. A test case refers to
an R-id instead of repeating the repository mutation. The case consumes and
verifies the prepared state. It does not reproduce the internal operations of
the R script.

## How They Are Used

Each independent case follows the same sequence:

```text
source tmp/verification-run.sh
    -> frozen Curbpack commit and binary verified
    -> disposable reference product deleted and cloned again
    -> exactly $REFERENCE_PRODUCT_COMMIT checked out

cd "$REFERENCE_PRODUCT_ROOT"
./external_test/curbpack/setup.sh <R-ID> --commit
    -> complete reusable starting repository state established

./external_test/curbpack/mutate_pack.sh <PF-ID>
    -> when the case names a PF other than the committed PF-01 set

verify/apply EC
    -> any additional execution condition established

execute test and record
    -> leave the repository and evidence for inspection
```

Sourcing `tmp/verification-run.sh` is the destructive restore. It deletes
`"$CURBPACK_ROOT/tmp/cyberready-test-product"` and clones it again at
exactly `"$REFERENCE_PRODUCT_COMMIT"`. It does not use `git reset` or
`git clean` on the previous checkout, and it does not keep local branches
from that clone.

Do not destroy the checkout at the end of a case. If the case fails, finds
a fault, or crashes, that checkout is what you inspect. The next case
starts by sourcing `tmp/verification-run.sh` again.

After sourcing, run `setup.sh` from `"$REFERENCE_PRODUCT_ROOT"`:

```bash
cd "$REFERENCE_PRODUCT_ROOT"
./external_test/curbpack/setup.sh --list
./external_test/curbpack/setup.sh R1 --commit
./external_test/curbpack/setup.sh R2 --commit
```

`setup.sh <R-id> [--commit]` applies the selected R-state to the checkout
that `tmp/verification-run.sh` just recreated, then runs `states/<R-id>.sh`.
`--commit` then records the prepared tree. It is not a revision argument.
Do not pass a commit, branch, tag, pin, or other revision to `setup.sh`.
The frozen revision was already selected for the verification run.

`./setup.sh R2` leaves a dirty tree; `./setup.sh R2 --commit` records the
same content. That is still R2. A new R-id is for a different reusable
starting state, not for a one-off dirty-tree edit. A one-off stimulus stays
in the testcase.

Do not run `reset.sh` between normal test cases.

The clone itself is created when the verification run starts
([Prepare a verification run](README.md#prepare-a-verification-run)), at
`<curbpack>/tmp/cyberready-test-product`. Each independent case then
deletes and recreates that same path.

R4 and R5 use this same path and the same `setup.sh` invocation. See
[R4](#r4) and [R5](#r5).

## Which States Exist Now

| ID | State | Used by |
|---|---|---|
| **R1** | Starting Glucose Log product content — no extra mutation | Curbpack, CTAM |
| **R2** | R1 with `SECURITY.md` removed (absent, not empty) | Curbpack |
| **R3** | R1 with heading `## Classification Rationale` removed | Curbpack |
| **R4** | demo-app content; token-only honesty-eval `SECURITY.md`; `package.json` identifying `acme-widget` | Curbpack |
| **R5** | demo-app content; thin rule-satisfying honesty-eval `SECURITY.md`; original demo-app `package.json` | Curbpack |
| **R6** | R1 plus stale `docs/review-log.md` / `docs/owned-policy.md` committed as Owner dated 2022-01-01 | Curbpack |
| **R7** | R1 plus `docs/review-log.md` / `docs/owned-policy.md` committed as Wrong Author dated 2026-09-13 | Curbpack |

`./external_test/curbpack/setup.sh --list` prints R1–R7 from
`states/*.sh` in the selected tree. Do not reuse an R-id for a different
condition. To add a Curbpack R-state: this document, `states.md`,
`states/<ID>.sh`, then the test case — together. `setup.sh` fails if the
script file is missing. Do not create unrecorded mutations during a test
run.

The `Used by` marker names the product that consumes the state. It does
not list individual stories or testcases.

<a id="r1"></a>

## R1 — Starting Glucose Log Product Content

The frozen Glucose Log commit (`$REFERENCE_PRODUCT_COMMIT`) without
additional content mutations.

At the audited reference-product snapshot, the following files are present:

- `SECURITY.md`;
- `.well-known/security.txt`;
- `docs/annex-vii/risk_assessment.md`;
- `docs/annex-vii/support_period.md`;
- `docs/annex-vii/user_manual_security.md`;
- `docs/incident/art14-path.md`;
- `docs/medtech/software_safety_class.md`;
- `docs/medtech/soup_list.md`;
- `docs/medtech/problem_resolution.md`; and
- `package.json`.

`docs/medtech/software_safety_class.md` contains the heading
`## Classification Rationale`. The dependency maps in `package.json` are empty
and contain no banned axios pin.

`states/R1.sh` prints this description when applying R1, then verifies the
listed files, the heading, the `package.json` conditions, and that the
working tree has no additional content mutation relative to the selected
starting ref. Keep that printed text in sync with this section. The
testcase verifies that this prepared state is present. It does not repeat
those script checks as a way of constructing R1.

Used by: Curbpack, CTAM

<a id="r2"></a>

## R2 — Missing Required File

R1 with `SECURITY.md` removed. The file is absent, not empty. Other R1 files
remain unchanged.

`states/R2.sh` prints this description when applying R2, then verifies that
`SECURITY.md` is absent (not empty) and that the other R1 files, heading, and
`package.json` conditions remain. Keep that printed text in sync with this
section. The testcase verifies that `SECURITY.md` is absent. It does not
remove the file itself.

Used by: Curbpack

<a id="r3"></a>

## R3 — Missing Required Section

R1 with the heading `## Classification Rationale` removed from
`docs/medtech/software_safety_class.md`. The file remains present and its other
content remains unchanged.

`states/R3.sh` prints this description when applying R3, then verifies that the
heading is gone, the file remains, `SECURITY.md` remains, and no other path
changed. Keep that printed text in sync with this section. The testcase
verifies that the heading is gone. It does not edit the file itself.

Used by: Curbpack

<a id="r4"></a>

## R4 — Token-Only House-Policy Tree

demo-app content with the token-only honesty-eval `SECURITY.md` and
`package.json` identifying `acme-widget`. Other retained demo-app content
is as verified by product `states/R4.sh`. The `acme-widget` name is
required: `anti_placeholder` scaffold overlap uses the `package.json`
name as the repo token, and the token-only fixture contains `acme-widget`.

This state is prepared on `"$REFERENCE_PRODUCT_ROOT"` by:

```sh
cd "$REFERENCE_PRODUCT_ROOT"
./external_test/curbpack/setup.sh R4 --commit
```

It is not a separate repository.

`states/R4.sh` prints this description when applying R4, then verifies the
token-only `SECURITY.md`, the `acme-widget` package name, and the retained
demo-app files. Keep that printed text in sync with this section. The
testcase verifies that this prepared state is present. It does not run
`git init`, `git add`, or `git commit`.

Used by: Curbpack

<a id="r5"></a>

## R5 — Thin Rule-Satisfying House-Policy Tree

demo-app content with the thin rule-satisfying honesty-eval `SECURITY.md`
and the original demo-app `package.json`. Other retained demo-app content
is as verified by product `states/R5.sh`.

This state is prepared on `"$REFERENCE_PRODUCT_ROOT"` by:

```sh
cd "$REFERENCE_PRODUCT_ROOT"
./external_test/curbpack/setup.sh R5 --commit
```

It is not a separate repository.

`states/R5.sh` prints this description when applying R5, then verifies the
thin real `SECURITY.md`, the original demo-app `package.json`, and the
retained demo-app files. Keep that printed text in sync with this section.
The testcase verifies that this prepared state is present. It does not run
`git init`, `git add`, or `git commit`.

Used by: Curbpack

<a id="r6"></a>

## R6 — Stale Fresh/Owned Fixture Docs

R1 plus `docs/review-log.md` and `docs/owned-policy.md` committed as
`Owner <owner@example.com>` with author/committer date
`2022-01-01T00:00:00Z`. The authored commit is part of the reusable
repository state required by the `fresh` check.

This state is prepared on `"$REFERENCE_PRODUCT_ROOT"` by:

```sh
cd "$REFERENCE_PRODUCT_ROOT"
./external_test/curbpack/setup.sh R6 --commit
```

`states/R6.sh` creates the two docs and commits them with that author and
date. Keep the printed text in sync with this section. The testcase
verifies the prepared files and clean tree. It does not run `git add` or
`git commit`.

Used by: Curbpack

<a id="r7"></a>

## R7 — Wrong-Author Fresh/Owned Fixture Docs

R1 plus `docs/review-log.md` and `docs/owned-policy.md` committed as
`Wrong Author <wrong@example.com>` with author/committer date
`2026-09-13T12:00:00Z`. The authored commit is part of the reusable
repository state required by the `owned` check.

This state is prepared on `"$REFERENCE_PRODUCT_ROOT"` by:

```sh
cd "$REFERENCE_PRODUCT_ROOT"
./external_test/curbpack/setup.sh R7 --commit
```

`states/R7.sh` creates the two docs and commits them with that author and
date. Keep the printed text in sync with this section. The testcase
verifies the prepared files and clean tree. It does not run `git add` or
`git commit`.

Used by: Curbpack

<a id="ec-01"></a>

## EC-01

EC-01 is recorded commit / clean working tree. It is not a new R-state.
The registry remains in [Execution
configurations](README.md#execution-configurations).

R preparation establishes the reusable starting repository state.
`setup.sh <R-id> --commit` records that prepared tree. The testcase then
verifies `git status --porcelain` is empty. It does not run `git init`,
`git add`, or `git commit` to construct the R-state.

An additional EC condition, such as a deliberate dirty-tree edit or
detached HEAD, is applied after that base R-state when the case names it.
