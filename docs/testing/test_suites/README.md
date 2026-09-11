# Test suites

A verification run applies the suites and test classes selected by the
[Verification Plan](../verification_plan.md) to one frozen baseline. Each
suite contains:

- one suite-level **Objective**;
- its requirements and other legitimate **Test basis**;
- a catalogue of existing **Test cases**;
- the written procedures that are currently executable; and
- a **Suite verdict** rule.

The suite objective is owned by the suite. It has no separate identifier.
**Test class** A/B/C/D on each case is a selection property from the
Verification Plan; it is not the suite objective or an execution result.

A test case retains its own objective or purpose, requirements or test basis,
prerequisites/setup, steps and expected results, teardown, and Pass/Fail
criteria when those parts have been specified. The intended written form is
ID/title, objective, test basis, prerequisites/setup, numbered steps with
action and expected result, teardown, and Pass/Fail criteria. Existing written
cases keep their current layout until they are executed. A catalogue row
marked **To be specified** is not an executable procedure and must not be
expanded by inference.

Fill the Run section of the
[test record template](../generated_test_record_template.md) once, then use
one copy per case execution.

Before executing a case, read the
[controlled test prerequisites](../procedures/README.md). Every Executable
case starts by confirming the Curbpack checkout is still the recorded
baseline (see Start of every independent case in that file). Execute only
rows whose Procedure status is **Executable**. Each such case states its
repository state (`R-*`), pack input (`PF-*`), execution configuration
(`EC-*`), exact setup, stimulus, expected response, and teardown. A row
marked **To be specified** is catalogue scope, not an executable procedure.

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
[../procedures/2_code_review_procedures.md](../procedures/2_code_review_procedures.md).
Protocol: [../generated_code_review_protocol_template.md](../generated_code_review_protocol_template.md).
