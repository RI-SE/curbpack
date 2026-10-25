# Curbpack catalogue under tests/check

Every id from `curbpack/testing/test_suites/` is here once. `make test-curbcheck` runs the seven carried checks. It prints manual rows and does not count them. A row marked outside is not a pass.

`curbpack check` fields `outcome`, `readiness_score`, and `evaluated_rules` are not the observation.

The outside reason, unless a row says otherwise: Curbpack runs that row with `curbpack check` and reads those fields. curbcheck does not emit them.

| id | Curbpack status | Here |
| --- | --- | --- |
| PK-001 | Covered by EV-001 | The seven carried checks are that pass |
| PK-002 | Executable | outside |
| PK-003 | Partial | outside. The partial steps are not a pass |
| PK-004 | Executable | outside |
| PK-005 | Executable | outside |
| EV-001 | Executable | The seven carried checks |
| EV-002 | Executable | outside |
| EV-003 | Executable | outside |
| EV-004 | Executable | outside |
| EV-005 | Executable | outside |
| EV-006 | Executable | outside |
| EV-007 | Executable | outside |
| EV-008 | Partial (A executable; B blocked) | outside. Pack-order fixtures stay in the Curbpack procedure |
| EV-009 | Executable | outside |
| FS-001 | Executable | outside |
| FS-002 | To be specified | To be specified |
| FS-003 | To be specified | To be specified |
| FS-004 | To be specified | To be specified |
| FS-005 | To be specified | To be specified |
| FS-006 | To be specified | To be specified |
| FS-007 | To be specified | To be specified |
| DT-001 | Executable | outside |
| DT-002 | To be specified | To be specified |
| DT-003 | Executable | outside |
| DT-004 | Executable | outside |
| PV-001 | Executable | outside |
| PV-002 | Executable | outside |
| PV-003 | Executable | outside |
| PV-004 | To be specified | To be specified |
| PV-005 | Executable | outside |
| PV-006 | Executable | outside |
| PV-007 | Executable | outside |
| RP-001 | Executable | outside |
| RP-002 | Executable | outside |
| RP-003 | Executable | outside |
| RP-004 | Executable | outside |
| RP-005 | Executable | outside |
| RP-006 | To be specified | To be specified |
| RP-007 | To be specified | To be specified |
| OP-001 | To be specified | To be specified |
| OP-002 | To be specified | To be specified |
| OP-003 | To be specified | To be specified |
| OP-004 | To be specified | To be specified |
| OP-005 | To be specified | To be specified |
| OP-006 | To be specified | To be specified |
| NB-001 | To be specified | To be specified |
| NB-002 | To be specified | To be specified |
| RB-001 | To be specified | To be specified |
| RB-002 | To be specified | To be specified |
| RB-003 | To be specified | To be specified |
| RB-004 | To be specified | To be specified |
| RL-001 | To be specified | To be specified |
| RL-002 | To be specified | To be specified |
| RL-003 | To be specified | To be specified |
| RL-004 | Executable | outside |
| RL-005 | To be specified | To be specified |
| CL-001 | Executable | outside |
| CL-002 | Executable | outside |
| CL-003 | To be specified | To be specified |
| CL-004 | To be specified | To be specified |
| UV-001 | Executable | outside |
| UV-002 | Executable | outside |
| UV-003 | Executable | outside |
| UV-004 | To be specified | To be specified |
| UV-005 | To be specified | To be specified |
| UV-006 | To be specified | To be specified |
| UV-007 | To be specified | To be specified |
| UV-008 | To be specified | To be specified |
| CR-01 | Manual | manual, see manual.md |
| CR-02 | Manual | manual, see manual.md |
| CR-03 | Manual | manual, see manual.md |
| CR-04 | Manual | manual, see manual.md |
| CR-05 | Manual | manual, see manual.md |
| CR-06 | Manual | manual, see manual.md |
| CR-07 | Manual | manual, see manual.md |
| CR-08 | Manual | manual, see manual.md |
| CR-09 | Manual | manual, see manual.md |
| CR-10 | Manual | manual, see manual.md |
| CR-11 | Manual | manual, see manual.md |
