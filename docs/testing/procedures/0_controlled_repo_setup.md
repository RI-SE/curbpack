# 0. Repository content states

An R-id is the prepared repository content a case starts from. R1–R7 are Curbpack states. The script that applies one of them on a reference-product checkout is `external_test/curbpack/setup.sh <id> --commit`, which runs `external_test/curbpack/states/<id>.sh`. This file does not replace that script. This suite does not edit it, and the carried cases do not invoke it.

The carried cases use the file content of reference-product commit `dee885ffb421e4646fea07fbb4a629616c09efc6`, extracted with `git archive`. That content is R1. Preparation is in [procedures/README.md](README.md).

R8 and R9 are not in this file. Their product effects stay in `../ctam/docs/testing/procedures.md`. Both ids are in [outside.md](../outside.md).

## R1 — Starting Glucose Log content

Present:

- `SECURITY.md`
- `.well-known/security.txt`
- `docs/annex-vii/risk_assessment.md`
- `docs/annex-vii/support_period.md`
- `docs/annex-vii/user_manual_security.md`
- `docs/incident/art14-path.md`
- `docs/medtech/software_safety_class.md`
- `docs/medtech/soup_list.md`
- `docs/medtech/problem_resolution.md`
- `package.json`

`docs/medtech/software_safety_class.md` contains the heading `## Classification Rationale`. The dependency maps in `package.json` are empty and contain no banned axios pin.

`states/R1.sh` verifies those files, that heading, and those `package.json` conditions. A carried case consumes this content. It does not remove or rewrite those files.

Used by: the seven carried cases.

## R2 — Missing required file

R1 with `SECURITY.md` removed. The file is absent, not empty. Other R1 files stay.

`states/R2.sh` verifies that `SECURITY.md` is absent and that the other R1 files remain. This suite does not run R2.

Used by: Curbpack. Not a carried case.

## R3 — Missing required section

R1 with the heading `## Classification Rationale` removed from `docs/medtech/software_safety_class.md`. The file remains. Its other content stays.

`states/R3.sh` verifies that the heading is gone and that `SECURITY.md` remains. This suite does not run R3.

Used by: Curbpack. Not a carried case.

## R4 — Token-only house-policy tree

demo-app content with the token-only honesty-eval `SECURITY.md` and `package.json` identifying `acme-widget`. The `acme-widget` name is required. This state is the same checkout, not a separate repository.

`states/R4.sh` verifies the token-only `SECURITY.md` and the `acme-widget` package name. This suite does not run R4.

Used by: Curbpack. Not a carried case.

## R5 — Thin rule-satisfying house-policy tree

demo-app content with the thin rule-satisfying honesty-eval `SECURITY.md` and the original demo-app `package.json`. This state is the same checkout, not a separate repository.

`states/R5.sh` verifies that thin `SECURITY.md` and the original demo-app `package.json`. This suite does not run R5.

Used by: Curbpack. Not a carried case.

## R6 — Stale owner and date

R1 plus `docs/review-log.md` and `docs/owned-policy.md` committed as `Owner <owner@example.com>` with author and committer date `2022-01-01T00:00:00Z`.

`states/R6.sh` creates those two files and commits them with that author and date. This suite does not run R6.

Used by: Curbpack. Not a carried case.

## R7 — Wrong author

R1 plus `docs/review-log.md` and `docs/owned-policy.md` committed as `Wrong Author <wrong@example.com>` with author and committer date `2026-09-13T12:00:00Z`.

`states/R7.sh` creates those two files and commits them with that author and date. This suite does not run R7.

Used by: Curbpack. Not a carried case.
