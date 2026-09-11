# Generated test record template

Copy this file **outside this repository** (or into the assignment’s record
store) for each execution instance. Name copies `{run-id}_{case-id}.md`. Do
not check filled records into the public Curbpack tree. Do not add record
columns to the suite tables.

Campaign baseline and scope are in the
[Verification Plan](verification_plan.md). Controlled test setup is in
[procedures/README.md](procedures/README.md). Fill one copy per case
execution.

Word Test Records, if the assignment archives in Word, are filled from these
copies.

## Run

| Field | Value |
|---|---|
| Run ID | |
| Date | |
| Reviewer | |
| Curbpack commit | |
| Reference-product commit (`tests/cyberready-test-product.pin` or `main`) | |
| Reference-product path | |
| `--as-of` date | |
| Pack files used | |
| Strategy / procedures / suite file commits | |

## Case

| Field | Value |
|---|---|
| Test case ID | (e.g. EV-002 — see the suite file) |
| Test class | |
| Repository state (R-id), if used | |
| Pack input (PF-id), if used | |
| Execution configuration (EC-id), if used | |
| Other prerequisite / fixture, if used | |
| Exact prepared commit / branch where relevant | |
| Platform / environment | |

## Result

| Field | Value |
|---|---|
| Expected | As declared on the case. Do not rewrite it here unless the run had to narrow it. |
| Observed | |
| Evidence / output references | |
| Disposition | Pass / Fail / Blocked / Not applicable / Inconclusive |
| Finding reference | |
| Notes | |
