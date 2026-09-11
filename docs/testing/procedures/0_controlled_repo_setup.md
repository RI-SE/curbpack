# 0. Repository content states

This file defines the `R-*` dimension of the
[controlled test prerequisites](README.md).

## What this is

Many test suites run Curbpack against a Git repository and check whether the
selected pack rules produce the expected result. Positive and negative tests
use [Glucose Log](https://github.com/RI-SE/cyberready-test-product) as the
**reference test product**. The repository contains product-specific pack
copies, claim descriptions and scripts for preparing known repository states.

This document describes the named repository states **R1–R5** that are used
when running the actual test cases. R is a controlled target-repository
content state, not “reference-product state” in general. An R-state is not
defined by which repository implementation happens to prepare it. R1–R3
target the disposable frozen reference product. R4 and R5 target
disposable repositories under Curbpack `tmp/`. A state defines which files
and content must be present or absent before a test case runs. The scripts
that create those states are stored in the test product under
[`external_test/curbpack/`](https://github.com/RI-SE/cyberready-test-product/tree/main/external_test/curbpack).

The files in that directory have distinct purposes:

- `states.list` lists the valid R-state identifiers;
- `states/<ID>.sh` prepares or verifies one state;
- `setup.sh` applies the selected R-state; it does not restore the frozen
  baseline;
- `reset.sh` is present in the product directory and is not part of the
  normal case sequence; and
- `states.md` is the product-side script registry. It must not redefine
  what an R-id means; this document remains normative.

This document and those files must be updated together. A test case refers to
an R-id instead of repeating the repository mutation.

## How they are used

Each independent case follows the same sequence:

```text
source verification-run environment
    -> frozen product baseline restored

prepare R-state
    -> requested controlled repository-content state established

verify/apply EC
    -> execution preconditions established

execute test
```

Do not tear down afterwards. If the case fails, finds a fault, or
crashes, the checkout is what you inspect. Idempotence comes from the
**next** sourced verification-run environment: that restore hard-resets
and cleans the disposable product checkout to `$REFERENCE_PRODUCT_COMMIT`.
Local `test_*` branch refs remain in the Git database. The last case may
commit, branch, or crash; the next source wipes the working tree. Leave the
checkout and outputs until the next case needs the repository.

`./setup.sh R2` leaves a dirty tree; `./setup.sh R2 --commit` records the
same content on a local `test_*` branch. That is still R2. A new R-id is for
different content, not for Git cleanliness.

Some cases need the mutated tree as a commit. Pass `--commit`: setup creates a
local branch `test_<user>_<YYYYMMDD>_<unique>`, prints the name, and leaves it.
Do not push it. Do not merge it into `main`. The next sourced restore does not
delete that branch. Delete it by hand when finished
(`git branch --list 'test_*'`; `git branch -D <name>`).

The clone itself is created once per verification run
([Prepare a verification run](README.md#prepare-a-verification-run)), typically
`<curbpack>/tmp/cyberready-test-product`.

After sourcing the verification-run configuration, the disposable product
checkout is already at the clean frozen baseline. Run `setup.sh` from that
checkout (`$REFERENCE_PRODUCT_ROOT/external_test/curbpack/`). It applies
the selected R-state only. It does not restore the baseline. Do not run
`reset.sh` between normal test cases.

```bash
./setup.sh --list
./setup.sh R1
./setup.sh R2 --commit
```

`setup.sh <R-id> [--commit]` applies the selected R-state to the already
restored frozen baseline, then runs `states/<R-id>.sh`. `--commit` then
records the mutated tree on a local `test_*` branch.

R4 and R5 are product scripts. They do not mutate the Glucose Log checkout.
After sourcing the verification-run environment, run
`"$REFERENCE_PRODUCT_ROOT/external_test/curbpack/states/R4.sh"` or
`"$REFERENCE_PRODUCT_ROOT/external_test/curbpack/states/R5.sh"`. Each
script may delete and recreate only its own target
(`$CURBPACK_ROOT/tmp/R4` or `$CURBPACK_ROOT/tmp/R5`). They read Curbpack
testdata. They establish content only; they do not init or commit Git.
EC-01 is a separate step in the case.

## Which states exist now

| ID | State |
|---|---|
| **R1** | Starting Glucose Log product content — no extra mutation |
| **R2** | R1 with `SECURITY.md` removed (absent, not empty) |
| **R3** | R1 with heading `## Classification Rationale` removed |
| **R4** | demo-app content; token-only honesty-eval `SECURITY.md`; `package.json` identifying `acme-widget` |
| **R5** | demo-app content; thin rule-satisfying honesty-eval `SECURITY.md`; original demo-app `package.json` |

`./setup.sh --list` prints R1–R5 from `states.list`. Do not reuse an R-id
for a different condition. To add a product R-state: this document,
`states.md`, `states.list`, `states/<ID>.sh`, then the test case —
together. `setup.sh` rejects unknown or duplicate R-ids. Do not create
unrecorded mutations during a test run. R4 and R5 are listed; cases invoke
`states/R4.sh` and `states/R5.sh` directly because those states do not
mutate the frozen Glucose Log checkout.

<a id="r1"></a>

## R1 — starting Glucose Log product content

The selected Glucose Log Git commit or branch without additional content
mutations.

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
starting ref. Keep that printed text in sync with this section.

<a id="r2"></a>

## R2 — missing required file

R1 with `SECURITY.md` removed. The file is absent, not empty. Other R1 files
remain unchanged.

`states/R2.sh` prints this description when applying R2, then verifies that
`SECURITY.md` is absent (not empty) and that the other R1 files, heading, and
`package.json` conditions remain. Keep that printed text in sync with this
section.

<a id="r3"></a>

## R3 — missing required section

R1 with the heading `## Classification Rationale` removed from
`docs/medtech/software_safety_class.md`. The file remains present and its other
content remains unchanged.

`states/R3.sh` prints this description when applying R3, then verifies that the
heading is gone, the file remains, `SECURITY.md` remains, and no other path
changed. Keep that printed text in sync with this section.

<a id="r4"></a>

## R4 — token-only house-policy tree

demo-app content with the token-only honesty-eval `SECURITY.md` and
`package.json` identifying `acme-widget`. Other retained demo-app content
is as verified by product `states/R4.sh`.

Target: `$CURBPACK_ROOT/tmp/R4`. Used by EV-006.

`states/R4.sh` may delete and recreate only that directory. It reads
Curbpack testdata. It does not modify `$REFERENCE_PRODUCT_ROOT` and does
not init or commit Git.

<a id="r5"></a>

## R5 — thin rule-satisfying house-policy tree

demo-app content with the thin rule-satisfying honesty-eval `SECURITY.md`
and the original demo-app `package.json`. Other retained demo-app content
is as verified by product `states/R5.sh`.

Target: `$CURBPACK_ROOT/tmp/R5`. Used by EV-009.

`states/R5.sh` may delete and recreate only that directory. It reads
Curbpack testdata. It does not modify `$REFERENCE_PRODUCT_ROOT` and does
not init or commit Git.

<a id="ec-01"></a>

## EC-01

EC-01 is recorded commit / clean working tree. It is not a new R-state.
The registry remains in [Execution
configurations](README.md#execution-configurations).

For R1–R3, `setup.sh <R-id> --commit` records the prepared tree. For R4
and R5, the case states explicit `git init`, `git add -A`, and `git
commit`. In both cases `git status --porcelain` is empty.
