# Reviewing

This guide is for anyone reading a Studio result: QA, security, compliance, buyers, auditors, authorities.

The review page compiles the Check run that happened, stores the reviewer's own words, and can sign that report. It does not re-run Check.

Keep a received report unchanged if you need the original handoff. Studio does not commit the report for you. If the team committed `docs/reports/review-report.json`, that commit is their later revision. The run's commit is `run_result.commit`.

## 1. What is in the report?

A compiled report is one JSON object. The server writes it at `<product-repo>/docs/reports/review-report.json`.

| Field | What it is for |
| --- | --- |
| `run_result` | The Check run under review. Pack id, `version`, directory digest, Claim rows, and, when Git was used, `commit` and `worktree`. |
| `requirements` | Copies of the Requirements the Claims name, including `references[].law_text` and the Requirement seal. |
| `claims` | Copies of the Claims that ran, in row order, including `checks[]` and the Claim seal. |
| `appendix` | Executed Claims that are unsigned or whose signature does not verify, with Claim id and Requirement id. This is not a failed Check. |
| `decision` | The reviewer's words. Absent until they are saved. |
| `signed` | review-sign. Absent until the report is signed. |

Studio does not write a separate findings file, an executive summary, an SBOM, a VEX document, or SARIF from this compile. A dependency question is a `dep_ban` Check when someone configured one. This build does not implement that Check as a pass. The report JSON is the handoff. `tool` and `tool_version` sit on the run result. The exit code is not a JSON field.

## 2. Start with the page

Open `/review`. Read the status, the selected run, `commit`, `worktree`, and the warnings before you write a decision.

When a saved report and a current run result are both loaded, the page says `same run: yes` or `same run: no. This saved report is an older run.` Do not describe an older report as the current result. Compile over that file requires the checkbox `Replace the saved report. The previous decision is not copied.`

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

Compile, save a decision, and sign. **Run checks** on that page is navigation back to the Check page. A replacement Claim is not a pass until that new run has been rendered.

Signature checks you can do with the file:

- report `signed`: who, when, which version digest, whether it verifies as a review report;
- embedded Requirement `signed`: a different digest;
- embedded Claim `signed`: a different digest again.

A Git-signed commit of a Claim file can count as that Claim's seal when the product repository is available and the Claim has no `signed` block. The Git author string is not the signer. A reviewer who only has the report file sees the `signed` block that was copied.

## 5. Inspect the evidence

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

## 6. What a green result means

A green result means the Checks that ran passed for that tree.

It does not by itself establish legal compliance, certification, CE marking, notified-body approval, or a regulator or RISE endorsement.

If a Claim failed and the evidence moved, use **Discover again** for that Requirement. The failed Claim stays visible. Add a new Claim for the new path. Retire the old Claim after you have confirmed the replacement. Run Checks again. Sign the new Claim in Claims if you approve it. Sign the report separately. Closing the popup changes nothing.

## Technical reference

* [Packs v2](../reference/packs2.md) §3.1 and §6
* [Evidence](../concepts/evidence.md)
* [Architecture](../arch/ARCHITECTURE.md)
* [Compile and review](../../review/ARCHITECTURE.md)
