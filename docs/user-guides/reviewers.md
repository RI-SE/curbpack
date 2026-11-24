# Reviewing

This guide is for anyone reading a Studio result: QA, security, compliance, buyers, auditors, authorities.

The review page compiles the Check run that happened, stores the reviewer's own words, and can sign that report. It does not re-run Check.

A review of a Run Result fills decisions from that run: Passed where the Check passed, otherwise Not assessed. Remediation history is empty. If `review_items` for that run already exists, the page asks whether to continue or start over. Continue merges the new Checks with the existing items. Start over keeps only the new Checks. A signed review offers Start. That opens the remediation for the same Check, where Check editing, Rebind, and Re-Discover are available, and each of those actions is recorded in the remediation history. Re-run Checks stays in that remediation and records the new result there. Sign Remediation locks that work. The signer is taking responsibility for the work that was done. The report views are placeholders until the reports are generated. The reviewer can still sign the review that already exists. Run Check writes a new Run Result and opens it as a review. That review asks whether to resume a review already started for the run, or to take in the latest signed Remedy Report. Taking it in fills a signed decision only where the underlag is unchanged, and keeps the remediation history. A Check or Claim that is in the Remedy Report and missing from the new run is retired only when the history has `action` `retire`.

Keep a received report unchanged if you need the original handoff. Studio does not commit the report for you. If the team committed `docs/reports/review-report.json`, that commit is their later revision. The run's commit is `run_result.commit`.

## 1. What is in the report?

A compiled report is one JSON object. The server writes it at `<product-repo>/docs/reports/review-report.json`.

| Field | What it is for |
| --- | --- |
| `run_result` | The Check run under review. Pack id, `version`, directory digest, Claim rows, and, when Git was used, `commit` and `worktree`. |
| `requirements` | Copies of the Requirements the Claims name, including `references[].law_text` and the Requirement seal. |
| `claims` | Copies of the Claims that ran, in row order, including `checks[]` and the Claim seal. |
| `appendix` | Executed Claims that are unsigned or whose signature does not verify, with Claim id and Requirement id. This is not a failed Check. |
| `assessments` | The reviewer's disposition for a Check on this run. `accept` applies to a failed or skipped Check, or a `stale` or `missing` binding. `must_fix` applies to those and also to a Check whose technical status is `pass`. `text` is required when `accept` records a failing Check. Absent means Not assessed. An assessment does not change the recorded Check status. The signed `review_items` decisions are what this reporting uses. |
| `remove_retired_checks` | Present only when a Check is retired. `true` means review-sign will remove those Checks from the live Claim files. `false` records the decision and leaves the Claim files alone. |
| `decision` | The reviewer's words. Absent until they are saved. |
| `signed` | review-sign. Absent until the report is signed. The signature covers the assessments and `remove_retired_checks`. |

Studio does not write a separate findings file, an executive summary, an SBOM, a VEX document, or SARIF from this compile. A dependency question is a `dep_ban` Check when someone configured one. This build does not implement that Check as a pass. The report JSON is the handoff. `tool` and `tool_version` sit on the run result. The exit code is not a JSON field.

## 2. Start with the page

Open `/review`. The page names the latest Check run and does not open it until you choose that run, an earlier run, or a report. Read the status, `commit`, `worktree`, and the warnings before you write a decision.

When a saved report is open, the page says `same run: yes` or `same run: no. This saved report is an older run.` That compares the report with the newest Check run. Do not describe an older report as the current result. Compile writes a new `review-report_<UTC>.json` and leaves the earlier report in place. An unsigned draft can still be edited. After review-sign, that file is read-only: a new decision is a new report.

The two sentences on the page are part of reading it: a passing Check does not mean the legal requirement is fulfilled, and the report has no field for a conclusion that the product meets CRA.

## 3. Understand what was checked

```text
Requirement, with law_text
     ↓
Claim: requirement_id, source, description, checks[]
     ↓
Run curbcheck against the working tree
     ↓
pass / fail / skipped, with detail when not pass
```

A pass means the arguments held. An `exist` Check and a `contents` Check on the same file are separate questions. Either one can fail alone.

A missing file is `fail`. Do not read a header complaint into that detail. A `skipped` row exists only because someone supplied a reason. Do not treat it as a pass.

Selected Requirements with no row were not checked. If that matters, it belongs in `decision`. The runner does not invent a failing row for them.

## 4. The page does not re-run Check

The order is Check, then the Check result, then Review. **Re-run Checks** is on Remediation. It goes back to the Check page. A replacement Claim is not a pass until that new run has been rendered.

## 5. Retire a Check

In review, a failed or skipped Check can be Not assessed, Accept, or Must be fixed. A passing Check is Passed or Must be fixed. Accept on a failing Check needs a comment. Must be fixed does not. The recorded status stays as the Check left it. Accept is not available for a passing Check. Retire is not a review verdict.

In remediation, Retire removes that Check from the Claim, or removes the Claim when no Check remains, and writes a history entry with `action` `retire`. A remediation comment is a history entry with `date` and `remediation` and no `action`. The person who did the work signs the Remedy Report from that workspace before the next review. A Check or Claim that the Remedy Report contains and the next Run Result does not is retired only when that history entry has `action` `retire`.

A report that already carries `disposition` `retire` still needs a comment. The recorded status stays `pass`, `fail`, or `skipped`. A binding cannot be retired.

**Notes** sit on the page and are saved with **Save**, the same way a comment is. **Save** writes the review and leaves it open, so it can be continued later. **Sign** asks for the signer name, locks those decisions, and is the start of Remediation. A later Save does not reopen a signed review. The Remedy Report records the remediation and does not change the signed decisions. Cancel writes nothing. It still asks for confirmation when any Check is Retire and lists those Checks under their Claims. The checkbox **Remove retired Checks from Claims when signing the report** is stored as `remove_retired_checks`. Leave it unchecked to keep the decision in the report and leave the Claim files unchanged.

If the checkbox was checked, signing then removes those Checks from the live Claim files. A Claim that still has a Check is signed again by the person who signed the report. A Claim with no Check left is deleted. The Check result copied into the report does not change. Studio does not commit the report or the Claim files.

If removal was chosen and a Claim file no longer matches the Check run, signing refuses and changes nothing. If a later Claim write fails, the report stays signed and the page names the Claims that were not updated. **Try retirement again** finishes only those Claims.

This is not the Retire control in Claims Editor. That control deletes the Claim file immediately, without this comment and without a report.

Signature checks you can do with the file:

- report `signed`: who, when, which version digest, whether it verifies as a review report;
- embedded Requirement `signed`: a different digest;
- embedded Claim `signed`: a different digest again.

A Git-signed commit of a Claim file can count as that Claim's seal when the product repository is available and the Claim has no `signed` block. The Git author string is not the signer. A reviewer who only has the report file sees the `signed` block that was copied.

## 6. Inspect the evidence

For a row that matters, open the path in the product tree at the revision under review and ask:

- Does this file support the Requirement, or only the probe?
- Is it this product's document, current for this revision?
- Does the content describe the practice, or only the heading the probe names?
- Is there a contradiction outside the paths that were checked?
- Does a domain, legal, safety, or security question remain that no Check asks?

```text
Check:
Did the bytes satisfy the arguments?

Reviewer:
Is that evidence adequate for the decision?
```

When `worktree` is `dirty`, the recorded commit is not proof that every checked byte came from that commit.

Currency of an assessment is often a different Requirement. Say that in `decision` if you mean it. Do not look for a CRA-compliance checkbox. `validate_report` rejects `compliant` and `meets_cra`.

## 7. What a green result means

A green result means the Checks that ran passed for that tree. A person still decides what that means.

If a Claim failed and the evidence moved, use **Discover again** for that Requirement. The failed Claim stays visible. Add a new Claim for the new path. Delete the old Claim in Claims Editor after you have confirmed the replacement. Run Checks again. Sign the new Claim in Claims if you approve it. Sign the report separately. Closing the popup changes nothing.

## Technical reference

* [Packs v2](../reference/packs2.md) §3.1 and §6
* [Evidence](../concepts/evidence.md)
* [Architecture](../arch/ARCHITECTURE.md)
* [Compile and review](../../review/ARCHITECTURE.md)
