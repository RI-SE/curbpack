# Test suites

A verification run applies the suites and test classes from the
[Verification Strategy](../../docs2/testing/strategy.md) default scope to one frozen baseline.
Each suite contains:

- one suite-level **Objective**;
- its requirements and other legitimate **Test basis**;
- a catalogue of existing **Test cases**;
- the written procedures that are currently executable; and
- a **Suite verdict** rule.

The suite objective is owned by the suite. It has no separate identifier.
**Test class** A/B/C/D on each case is a selection property from the
Verification Strategy default scope; it is not the suite objective or an
execution result.

The intended written form for an executable case is:

- **Requirements** — every specified requirement the case verifies, or an
  explicit statement that it does not verify a specified requirement plus
  the other test basis;
- **SETUP** — the named `R-*` / `PF-*` / `EC-*` identifiers, the `setup.sh`
  invocation, and checks that the prepared state is the intended one; and
- **TEST STEPS** — stimulus and observations only.

SETUP verifies prepared state. It does not reproduce the internal operations
of the R-state script, and it does not use `git init`, `git add`, or
`git commit` to construct that state. A one-off stimulus stays in TEST STEPS
and does not require a new R-id.

Do not add a TEARDOWN section. After a case, leave the repository and
evidence for inspection. The next independent case starts by sourcing
`tmp/verification-run.sh`, which deletes and recreates the disposable
reference-product checkout. Older written cases may still show other
headings; the shared procedure already defines this behaviour.

A catalogue row marked **To be specified** is not an executable procedure
and must not be expanded by inference.

Fill the Run section of the
[test record template](../../docs2/testing/generated_test_record_template.md) once, then use
one copy per case execution.

Before executing a case, read the
[controlled test prerequisites](../../docs2/testing/procedures/README.md). Start the
verification run once, then start every independent case from the Curbpack
root with `source tmp/verification-run.sh` (see Start of every independent
case in that file). Execute only rows whose Procedure status is
**Executable**. Each such case states its repository state (`R-*`), pack
input (`PF-*`), execution configuration (`EC-*`), exact setup, stimulus, and
expected response. A row marked **To be specified** is catalogue scope, not
an executable procedure.

| Suite | File | What it asks |
|---|---|---|
| **PK** | [PK.md](PK.md) | Good pack vs bad pack |
| **EV** | [EV.md](EV.md) | Specified check outcome for a known state |
| **FS** | [FS.md](FS.md) | Path escape |
| **DT** | [DT.md](DT.md) | Same inputs, same result |
| **PV** | [PV.md](PV.md) | Named git state and pack |
| **RP** | [RP.md](RP.md) | Review Pack vs machine result |
| **OP** | [OP.md](OP.md) | Write failure and kill mid-run |
| **NB** | [NB.md](NB.md) | Offline and data boundary |
| **RB** | [RB.md](RB.md) | Large input and two checks at once |
| **RL** | [RL.md](RL.md) | Shipped binary vs frozen source |
| **CL** | [CL.md](CL.md) | Overclaim |
| **UV** | [UV.md](UV.md) | User handoff and interpretation |

`CR` is independent code and release review, not a functional suite. Procedure:
[2. Code and release review](../../docs2/testing/procedures/2_code_review_procedures.md).
Protocol: [code review protocol template](../../docs2/testing/generated_code_review_protocol_template.md).
