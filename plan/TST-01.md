# TST-01 — Migrate the suite, then run the carried cases

## Summary

- **Story:** `docs/agile/epics/06-migrated-test-suite/stories/TST-01-migrate-testing-docs.md`
- **Goal:** `docs/testing/README.md` states a `python3 -m checks` argv that exits 0 when every carried case has its expected status.
- **Scope / exclusions:** Write `plan/TST-01.md` and files under `docs/testing/` only. Do not edit application code, `docs/reference/packs2.md`, `docs/reference/test-packs/`, `daniel/ny_sdd/`, `docs/req/`, or `cyberready-test-product`. Derived requirement rows stay in this plan because an extra `docs/req/` file would violate that commit set. No new Packs v2 field. No edit to an `R*` or `PF*` script.
- **Baseline:** Source tree `/Users/DanielFl/Documents/aProjects/aslak/curbpack/docs/testing/` has 9 files (Curbpack `b07b8de`). Reference product HEAD `dee885ffb421e4646fea07fbb4a629616c09efc6`. Studio HEAD `971b1ae`. Probe on 2026-10-24: a temporary archive of that product HEAD, plus `curbpack.json` selecting `cra-baseline`, `house-policy`, and `medtech-iec62304`, plus all 9 claim files from `docs/reference/test-packs/claims/`, run as `python3 -m checks --repo <temp> --packs docs/reference/test-packs --out <temp>/all.json`. Result: claims 9, exit 1. Seven claims `pass`. `HOUSE-DEP-AXIOS-PIN` fails because `curbcheck-dep-ban` is unavailable. `HOUSE-SECRET-PATHS` fails because `.env`, `.env.local`, `credentials.json`, `service-account.json`, and `id_rsa` are absent. The same tree with only the seven passing claim files exits 0. That probe directory sat inside the Studio work tree, so Git reported the Studio worktree dirty. The acceptance run must use a checkout outside this repository.

## Current checkpoint

| Field | Value |
| --- | --- |
| Plan status | DONE |
| Approved by | Maintainer, 2026-10-24, plan revision 2026-10-24.1 |
| Current task | Task 3 — closed |
| Last completed task | Task 3 — checkpoint passed, then status set to DONE |
| Last verified tests | 2026-10-24: python3 -m checks --repo /tmp/tst01-suite.tqJXSt/repo --packs docs/reference/test-packs --out /tmp/tst01-suite.tqJXSt/repo/run-result.json — claims 7 exit 0, pass 7, fail 0, worktree clean. Nine-claim probe the same day exited 1. |
| Last checkpoint commit | 441d143e2f74f17653ffd885beb3e9e1b7952291 |
| Requirements | TST-R01–TST-R07 in this plan |
| Packs v2 | `docs/reference/packs2.md` at Studio `971b1ae`. This story does not edit it. |
| Blockers | None |
| **Exact next action** | No implementation step remains. |

Plan revision: 2026-10-24.1. Maintainer: Maintainer, 2026-10-24.

## Requirements and acceptance mapping

| Requirement ID | Story | Test / observed evidence | Status |
| --- | --- | --- | --- |
| TST-R01 | TST-01 | `docs/testing/README.md` argv is `python3 -m checks` with `--repo`, `--packs docs/reference/test-packs`, and `--out`. The prepared repo has `curbpack.json`. The argv does not read `.curbpack.json` or `CURBPACK_PACKS_DIR`. | APPROVED |
| TST-R02 | TST-01 | This plan's source-file table has 9 rows. Carried plus outside equals 9. | APPROVED |
| TST-R03 | TST-01 | Each carried case id in `docs/testing/procedures/cases.md` has expected status `pass`, and the same `checks[].check` and `checks[].args` as `docs/reference/test-packs/claims/<id>.json`. | APPROVED |
| TST-R04 | TST-01 | `docs/testing/outside.md` has one `id` column and the outside ids in this plan. A row there is not a pass. | APPROVED |
| TST-R05 | TST-01 | `docs/testing/procedures/0_controlled_repo_setup.md` and `1_pack_template_instantiation.md` keep R1–R7 and PF-01–PF-17 with the product effects copied below. They name `external_test/curbpack/states/<id>.sh` and `mutate_pack.sh`. They do not replace those scripts. | APPROVED |
| TST-R06 | TST-01 | R8, R9, PF-18, and PF-19 stay the ids in `ctam/docs/testing/procedures.md`. They are outside. No reference-product script is edited. | APPROVED |
| TST-R07 | TST-01 | Work log records the argv, the date, pass count 7, fail count 0, and the outside ids. Exit 0 is recorded only for that result. | APPROVED |

## Source files

Count 9. Carried 9. Outside 0. Carried plus outside equals 9.

| Source file under `curbpack/docs/testing/` | Mark | Studio path |
| --- | --- | --- |
| `README.md` | carried | `docs/testing/README.md` |
| `strategy.md` | carried | `docs/testing/strategy.md` |
| `requirements_traceability.md` | carried | `docs/testing/requirements_traceability.md` |
| `generated_test_record_template.md` | carried | `docs/testing/generated_test_record_template.md` |
| `generated_code_review_protocol_template.md` | carried | `docs/testing/generated_code_review_protocol_template.md` |
| `procedures/README.md` | carried | `docs/testing/procedures/README.md` |
| `procedures/0_controlled_repo_setup.md` | carried | `docs/testing/procedures/0_controlled_repo_setup.md` |
| `procedures/1_pack_template_instantiation.md` | carried | `docs/testing/procedures/1_pack_template_instantiation.md` |
| `procedures/2_code_review_procedures.md` | carried | `docs/testing/procedures/2_code_review_procedures.md` |

Rewritten text is carried. Catalogue ids from the Curbpack suites (`PK-*`, `EV-*`, `FS-*`, `DT-*`, `PV-*`, `RP-*`, `OP-*`, `NB-*`, `RB-*`, `RL-*`, `CL-*`, `UV-*`, `CR-*`) are not cases of this suite. This plan does not mark them outside, and `outside.md` does not list them. OUT-01 disposes only ids that `outside.md` lists.

## Carried cases

Seven. Repository state R1. Pack input PF-01, meaning pack ids `cra-baseline`, `house-policy`, and `medtech-iec62304` loaded from `docs/reference/test-packs`. Expected claim status `pass`. The process exits 0 only when all seven are `pass`.

| Case id | Expected status |
| --- | --- |
| CRA-ANNEX-VII-MANUAL | pass |
| CRA-ANNEX-VII-RISK | pass |
| CRA-ANNEX-VII-SUPPORT | pass |
| CRA-ART14-PATH | pass |
| HOUSE-ANTI-PLACEHOLDER | pass |
| HOUSE-SECURITY-MD | pass |
| HOUSE-SECURITY-TXT | pass |

`docs/testing/procedures/cases.md` is new. It is not one of the nine source files. For each id it copies `checks[].check` and `checks[].args` from that claim file and writes `pass` next to the id.

## Outside ids

`docs/testing/outside.md` columns: `id` only.

Claims that cannot be carried:

- `HOUSE-DEP-AXIOS-PIN` — `dep_ban` fails because `curbcheck-dep-ban` is not installed. Application code is out of scope.
- `HOUSE-SECRET-PATHS` — Packs v2 §4: `contents` fails when a listed path is absent. On R1 the five paths `.env`, `.env.local`, `credentials.json`, `service-account.json`, and `id_rsa` are absent. A pass on that absence needs another registered Check. This story does not add one, and it does not edit an R script to create those files.

CTAM ids, not run:

- `R8`, `R9`, `PF-18`, `PF-19`

Every `MUST-*` from `daniel/ny_sdd/docs/REQUIREMENTS.md` (the 55 matrix ids). No carried case names one:

`MUST-01` `MUST-02` `MUST-03` `MUST-04` `MUST-10` `MUST-11` `MUST-12` `MUST-13` `MUST-14` `MUST-20` `MUST-21` `MUST-22` `MUST-23` `MUST-24` `MUST-25` `MUST-30` `MUST-31` `MUST-32` `MUST-33` `MUST-34` `MUST-35` `MUST-40` `MUST-41` `MUST-42` `MUST-43` `MUST-44` `MUST-45` `MUST-46` `MUST-47` `MUST-48` `MUST-50` `MUST-51` `MUST-52` `MUST-53` `MUST-60` `MUST-61` `MUST-62` `MUST-63` `MUST-70` `MUST-71` `MUST-72` `MUST-73` `MUST-74` `MUST-80` `MUST-81` `MUST-82` `MUST-83` `MUST-84` `MUST-90` `MUST-91` `MUST-92` `MUST-93` `MUST-94` `MUST-95` `MUST-96`

Outside count: 2 + 4 + 55 = 61. An id in that file is not a pass. Disposition is OUT-01.

## Product effects kept

R1–R7, from `curbpack/docs/testing/procedures/0_controlled_repo_setup.md`. The script path stays `external_test/curbpack/states/<id>.sh` invoked by `external_test/curbpack/setup.sh <id> --commit` on the reference-product checkout. This story does not run that script against the live product and does not edit it.

| ID | Product effect |
| --- | --- |
| R1 | Starting Glucose Log content. Present: `SECURITY.md`, `.well-known/security.txt`, `docs/annex-vii/risk_assessment.md`, `docs/annex-vii/support_period.md`, `docs/annex-vii/user_manual_security.md`, `docs/incident/art14-path.md`, `docs/medtech/software_safety_class.md`, `docs/medtech/soup_list.md`, `docs/medtech/problem_resolution.md`, `package.json`. Heading `## Classification Rationale` is present. `package.json` dependency maps are empty and contain no banned axios pin. |
| R2 | R1 with `SECURITY.md` absent, not empty. |
| R3 | R1 with heading `## Classification Rationale` removed from `docs/medtech/software_safety_class.md`. The file remains. |
| R4 | demo-app content, token-only honesty-eval `SECURITY.md`, `package.json` name `acme-widget`. Same checkout, not a separate repository. |
| R5 | demo-app content, thin rule-satisfying honesty-eval `SECURITY.md`, original demo-app `package.json`. Same checkout. |
| R6 | R1 plus `docs/review-log.md` and `docs/owned-policy.md` committed as `Owner <owner@example.com>` dated `2022-01-01T00:00:00Z`. |
| R7 | R1 plus `docs/review-log.md` and `docs/owned-policy.md` committed as `Wrong Author <wrong@example.com>` dated `2026-09-13T12:00:00Z`. |

PF-01–PF-17, from `curbpack/docs/testing/procedures/1_pack_template_instantiation.md`. The selector stays `external_test/curbpack/mutate_pack.sh <PF-id>`. Studio's runner does not read `CURBPACK_PACKS_DIR` or `.curbpack.json`. PF-01's pack ids are passed as `--packs docs/reference/test-packs`.

| ID | Product effect |
| --- | --- |
| PF-01 | Pack ids `house-policy`, `cra-baseline`, `medtech-iec62304`. |
| PF-02 | Reserved. Not specified. `mutate_pack.sh PF-02` is refused. |
| PF-03 | Unknown check type `llm_judge` in `packs/unknown-check/pack.json`. |
| PF-04 | Invalid regular expression in `packs/bad-regex/pack.json`. |
| PF-05 | Relative path traversal in `packs/path-traversal/pack.json`. |
| PF-06 | PF-01 with one trailing space on `house-policy/pack.json`. |
| PF-07 | `fresh-owned-test` pack. |
| PF-08 | EV-008 pack, ALPHA before BETA. |
| PF-09 | EV-008 pack, BETA before ALPHA. |
| PF-10 | Review Pack whose `expected_parent_commit_sha` is 40 `b` characters, under `external_test/curbpack/review-pack-input/`. |
| PF-11 | Review Pack with the `HOUSE-SECURITY-MD` line removed from the executive summary. |
| PF-12 | Review Pack with truncated `01-gate-failures.json` (`{` and a newline). |
| PF-13 | Malformed `house-policy` JSON: the comma after `"version"` removed. |
| PF-14 | Truncated `house-policy` JSON: first 120 bytes of the PF-01 file. |
| PF-15 | PF-01 `house-policy` with `HOUSE-SECURITY-MD` duplicated. |
| PF-16 | Conflicting `HOUSE-SECURITY-MD` definitions, original then `docs/pk003-absent.md`. |
| PF-17 | Same conflicting definitions as PF-16, order reversed. |

R8 is R1 with `src/app.py` present and `does not calculate insulin` replaced once by `does not calculate insulin (edited)`. R9 is R1 with `src/app.py` absent, not empty. PF-18 copies `external_test/ctam/pf-fixtures/PF-18/context-pack.json` onto `external_test/ctam/context-pack.json`. PF-19 copies `buyer-questions.json` and `context-pack.json` from `external_test/ctam/pf-fixtures/PF-19/` onto `external_test/ctam/`. Those four are outside. The sentences stay in `ctam/docs/testing/procedures.md`.

## Tasks

### Task 0 — derive and approve requirements and plan

**Inputs / contracts:** the nine source files, `ctam/docs/testing/procedures.md`, `daniel/ny_sdd/docs/REQUIREMENTS.md`, `docs/reference/test-packs/claims/`, `docs/reference/packs2.md`
**Change files:** `plan/TST-01.md`
**Acceptance / stop:** plan review reports no blocking issue; then set Plan status to APPROVED. Stop if a blocking issue remains after one re-review.

- [x] Requirements written in this plan.
- [x] Baseline probe recorded.
- [x] Plan review complete and Plan status set to APPROVED.

### Task 1 — write the carried documents

**Requirements:** TST-R01, TST-R02, TST-R03, TST-R04, TST-R05, TST-R06
**Files:** the nine Studio paths above, plus `docs/testing/procedures/cases.md` and `docs/testing/outside.md`
**Test first:** the nine-claim probe already exited 1. Do not treat that as acceptance.
**Validation:** `docs/testing/README.md` contains the argv flags; `outside.md` has 61 ids and no second column; `cases.md` check args match the seven claim files; R and PF tables match the product-effect tables in this plan; `rg` finds no `CURBPACK_PACKS_DIR` and no `.curbpack.json` under `docs/testing/`.
**Stop if:** matching a claim would add a Packs v2 field, or a carried case would pass only after an R or PF script edit. Mark that case outside instead.

- [x] README states the suite argv.
- [x] Cases, outside list, and R/PF product effects written.
- [x] The other carried files rewritten onto the same runner. Code review text says it is not a carried case.

### Task 2 — run the carried cases

**Requirements:** TST-R07
**Files:** `plan/TST-01.md` work log only
**Test first:** The nine-claim probe already exited 1. Acceptance is the command in this task, after Task 1.
**Validation:** stdout contains `claims 7 exit 0`, seven `pass` lines, and no `fail` line. Then delete the temporary repo.
**Stop if:** exit is not 0, or a pass appears only after a script or application edit.

Prepare a temporary repo outside this Studio work tree. Read-only source is reference-product commit `dee885ffb421e4646fea07fbb4a629616c09efc6`. Do not edit that product.

1. `git -C /Users/DanielFl/Documents/aProjects/aslak/cyberready-test-product archive dee885ffb421e4646fea07fbb4a629616c09efc6` extracted into the temp repo.
2. Write `<temp>/curbpack.json` with exactly `{"packs":["cra-baseline","house-policy","medtech-iec62304"]}`.
3. Copy only these seven files into `<temp>/claims/`: `CRA-ANNEX-VII-MANUAL.json`, `CRA-ANNEX-VII-RISK.json`, `CRA-ANNEX-VII-SUPPORT.json`, `CRA-ART14-PATH.json`, `HOUSE-ANTI-PLACEHOLDER.json`, `HOUSE-SECURITY-MD.json`, `HOUSE-SECURITY-TXT.json`, from `docs/reference/test-packs/claims/`. `python3 -m checks` reads that `claims/` directory (`checks/run.py`).
4. `git init` and one commit in the temp repo so its worktree is clean. That commit is not a Studio commit.
5. From the Studio root:

```sh
python3 -m checks --repo <temp> --packs docs/reference/test-packs --out <temp>/run-result.json
```

6. Record argv, date, pass count, fail count, and the 61 outside ids in the work log. Delete `<temp>`.

- [x] Acceptance argv recorded with date, pass count 7, fail count 0, and outside ids.
- [x] Temporary repo deleted. Reference product scripts unchanged.

### Task 3 — close

**Requirements:** TST-R01–TST-R07
**Files:** `plan/TST-01.md` only. Do not create `impl/TST-01.md`.
**Test first:** `python3 scripts/check_story_plan.py TST-01 --phase checkpoint` while Plan status is still APPROVED and the work log has the Task 2 evidence.
**Validation:** Story commits touch only `plan/TST-01.md` and paths under `docs/testing/`.
**Stop if:** a requirement has no recorded evidence.

The epic allows commits to contain only `plan/TST-01.md` and paths under `docs/testing/`. `scripts/check_story_plan.py --phase done` reads `impl/TST-01.md`. Moving the plan there would put `impl/TST-01.md` in a commit this epic forbids. This story therefore stays at `plan/TST-01.md`. After the checkpoint check passes, set Plan status to DONE in that same file. Do not run `--phase done`.

- [x] Checkpoint check exited 0.
- [x] Plan status DONE. Exact next action says no implementation step remains.

## Work log

- **2026-10-24 / Task 0:** Dependencies DOC-01, DOC-02, DOC-03, and PK2-01 are Status Done in their stories and epic tables. `cmp docs/reference/packs2.md daniel/ny_sdd/docs/architecture/packs2.md` exited 0. `find daniel/ny_sdd -type f` printed the 17 DOC-03 paths and nothing else. Source file count under `curbpack/docs/testing/` is 9. Probe command: `python3 -m checks --repo <temp> --packs docs/reference/test-packs --out <temp>/all.json` on an archive of product `dee885ffb421e4646fea07fbb4a629616c09efc6` with all 9 claim files. Output: `claims 9 exit 1`; seven `pass`; `HOUSE-DEP-AXIOS-PIN` fail (`curbcheck-dep-ban` unavailable); `HOUSE-SECRET-PATHS` fail (five paths absent). Second probe with those two claim files omitted: `claims 7 exit 0`. Temp directory removed. No reference-product file edited. First plan review found two blocking issues: Task 2 did not state `curbpack.json` and the seven files under `claims/`, and Task 3 moved the plan to `impl/`, which the epic commit list forbids. Both are corrected in revision 2026-10-24.1. Re-review status: Approved. No blocking issues. Advisory notes kept: acceptance signal is `claims 7 exit 0` and no `fail` status; traceability names no catalogue case id. Plan status set to APPROVED. IMPL-START Task 1. Requirements TST-R01–TST-R06. Files: the nine carried paths, `docs/testing/procedures/cases.md`, `docs/testing/outside.md`.
- **2026-10-24 / Task 1:** Wrote the nine carried files, `docs/testing/procedures/cases.md`, and `docs/testing/outside.md`. Check arrays in `cases.md` match the seven claim files. `outside.md` has 61 ids and one column.
- **2026-10-24 / Task 2:** Prepared `/tmp/tst01-suite.tqJXSt/repo` from `git archive dee885ffb421e4646fea07fbb4a629616c09efc6`, `curbpack.json` packs `cra-baseline`, `house-policy`, `medtech-iec62304`, and the seven claim files under `claims/`. Own commit, porcelain empty. Command from the Studio root: `python3 -m checks --repo /tmp/tst01-suite.tqJXSt/repo --packs docs/reference/test-packs --out /tmp/tst01-suite.tqJXSt/repo/run-result.json`. Stdout: `claims 7 exit 0`. Pass count 7. Fail count 0. Worktree clean. Process exit 0. Reference-product `git status --porcelain` unchanged. Temporary repo deleted. REVIEW-START for Task 1 and Task 2. First code review: Important findings fixed — PF-08 and PF-09 name the EV-008 packs and destination paths; `HOUSE-DEP-AXIOS-PIN` and `HOUSE-SECRET-PATHS` have their `checks` arrays in `docs/testing/procedures/cases.md` and are marked outside, not pass. Minor, left as written: traceability cites the requirements file rather than quoting each sentence; the strategy table calls a non-pass `fail`. Second code review: no Critical or Important findings. Outside ids: `HOUSE-DEP-AXIOS-PIN`, `HOUSE-SECRET-PATHS`, `R8`, `R9`, `PF-18`, `PF-19`, and `MUST-01`, `MUST-02`, `MUST-03`, `MUST-04`, `MUST-10`, `MUST-11`, `MUST-12`, `MUST-13`, `MUST-14`, `MUST-20`, `MUST-21`, `MUST-22`, `MUST-23`, `MUST-24`, `MUST-25`, `MUST-30`, `MUST-31`, `MUST-32`, `MUST-33`, `MUST-34`, `MUST-35`, `MUST-40`, `MUST-41`, `MUST-42`, `MUST-43`, `MUST-44`, `MUST-45`, `MUST-46`, `MUST-47`, `MUST-48`, `MUST-50`, `MUST-51`, `MUST-52`, `MUST-53`, `MUST-60`, `MUST-61`, `MUST-62`, `MUST-63`, `MUST-70`, `MUST-71`, `MUST-72`, `MUST-73`, `MUST-74`, `MUST-80`, `MUST-81`, `MUST-82`, `MUST-83`, `MUST-84`, `MUST-90`, `MUST-91`, `MUST-92`, `MUST-93`, `MUST-94`, `MUST-95`, `MUST-96`.
- **2026-10-24 / Task 3:** `python3 scripts/check_story_plan.py TST-01 --phase checkpoint` exited 0 while Plan status was APPROVED. Plan status then set to DONE in `plan/TST-01.md`. `impl/TST-01.md` was not created. `--phase done` was not run. No implementation step remains.
