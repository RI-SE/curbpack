# First-run cohort scorecard (3 → 10 → 20 → 100)

Manual adoption validation for the first-run path only: install → `cd` → `curbpack scan`. **Not** product-market fit. **Not** conformity assessment.

**Rollout:** 3 RISE → 10 friendly → 20 strangers → 100 strangers (**133** testers total).

**Public vs internal**

| Where | What |
|-------|------|
| **This committed file** | Empty template + **aggregate** counts only |
| **RISE access-controlled file** (not in git) | Tester-level rows; identified owner; retention period set by humans |

Do **not** commit names, contact details, repository identifiers, scan findings, or identifiable notes.

Entry link for invitees: [rise-tryout.md](rise-tryout.md). Feedback (optional): canonical [first_run_feedback.yml](https://github.com/RI-SE/curbpack/issues/new?template=first_run_feedback.yml) on **RI-SE/curbpack** only.

## Aggregate results (public)

Update counts only — no individual rows.

| Metric | rise-3 | friendly-10 | stranger-20 | stranger-100 | Total |
|--------|--------|-------------|-------------|--------------|-------|
| Invited | 1 | | | | 1 |
| Completed install + scan | 1 | | | | 1 |
| Blocked | | | | | |
| Feedback issues filed | | | | | |
| Support interventions (sum) | | | | | |
| Interventions per completed tester | | | | | |
| Returned / recommended / filed feedback | | | | | |

### Repeated friction categories (sanitised)

| Category | Count | Status (acknowledged / fixed / planned / not pursuing) |
|----------|-------|--------------------------------------------------------|
| Scan `Next:` read as required vs tryout “stop after scan” | 1 | fixed in tree / pending merge + next binary (CLI: `Next (optional):` + tryout ignore note; ships after v0.5.3) |
| Wrong install host (non-RI-SE URL → 404) | 1 | acknowledged (tryout: RI-SE only) |
| PATH stale until new shell / export | 1 | acknowledged (tryout + install PATH hint) |

### Cohort gate checklist

| Cohort | Proceed when | Met? |
|--------|--------------|------|
| 3 RISE | All three complete without a maintainer running commands for them; top blockers recorded; critical dead ends fixed | |
| 10 friendly | Most complete without live support; friction categories clear; feedback route works; no one reads scan exit 0 as certification or gate approval | |
| 20 strangers | Clear majority self-serve; support effort per tester lower than friendly cohort; no serious privacy/trust/install confusion; top repeated blocker fixed or explicitly accepted | |
| 100 strangers | Completion repeatable; support effort does not rise materially; issues cluster into few fixable categories; some return, recommend, or file feedback (issues / Teams / ADOPTERS PR — Discussions not enabled) | |

Record exact observed counts. Do not invent percentages where data is incomplete. Do not claim untested OS platforms passed.

## Internal tester-level columns (RISE file only — do not commit)

```text
cohort
invite_date
os
install_worked
scan_completed
next_clear
almost_stopped_reason
support_interventions
feedback_channel
follow_up_via_github_issue
future_tests_interest
returned_or_recommended
notes_sanitised
```

Owner: _________________ Retention: _________________

## Operating rule

> One RI-SE entry link. Canonical installation source. Canonical feedback form. Internal tester-level scorecard. Public aggregate learning. Fix the top blocker before expanding.

## Stop conditions

Stop and report rather than expanding if feedback requires repository data or raw findings; if the tryout duplicates install pins; if HPURL/signing/telemetry/backend is proposed for this path; if public wording implies certification or approval.
