# Reviewing

This guide is for anyone reading a Studio result: QA, security, compliance, buyers, auditors, authorities.

A round has three parts. **Check** writes a result. **Review** records a decision for each deviation and **Sign** locks those decisions. **Remediation** is the work that follows a signed review. **Sign Off** locks that work and writes a remediation report. A signed review and a signed remediation both open read-only.

Open **Verification-Workflow** in the menu (`/check`). The page is headed **Check**. The table **Checks performed** has one row per Check, newest first. A re-check made while a remediation is open updates that remediation and does not add a row.

| Column | What you do |
| --- | --- |
| Check Result | The time and the pass, fail, and skipped counts. Open it to review that run. |
| Review | **Create** when nobody has saved a review. **Continue** when a review is saved and not signed. **View** when it is signed. |
| Remedy | A dash until the review is signed. Then **Start**, **Continue**, or **Completed**. |
| Report icon | The readable remediation report, after Sign Off. |

The trash control removes that row's files. It asks first and lists the files.

## 1. Review

Open the Check result from the table, or open **Review** (`/review`) and follow the link to the latest result.

The page leads with **Deviations**. A passing Check is folded under **Passed**. A failed or skipped Check, and a Requirement binding that is `stale` or `missing`, is a deviation.

For a deviation the decision is **Not assessed**, **Accept**, or **Must be fixed**. A passing Check is **Passed** or **Must be fixed**. Accept is not offered for a passing Check. The Check result stays `pass`, `fail`, or `skipped`. Retire is not a review decision.

**Notes** are the reviewer's words for the whole review. **Save** writes the decisions and the notes into that Check's `review_items.json` and returns to Check. The review stays open, so the row says **Continue**. **Sign** asks for the signer name, locks the decisions, writes the signed review report beside that Check, and returns to Check. The row then says **View**. A later Save does not reopen a signed review.

If `review_items` for that run already exist, the page asks whether to continue or start over. Continue merges the new Checks with the existing items. Start over keeps only the new Checks.

**Cancel** returns to Check and writes nothing.

**Technical details** opens the run identity: `commit`, `worktree`, and, when a saved report is open, `same run: yes` or `same run: no. This saved report is an older run.` That comparison is the report against the newest Check, not a claim that an older report is the current result. The same dialog states that a passing Check does not mean the legal requirement is fulfilled, and that the report has no field for a conclusion that the product meets CRA.

## 2. Remediation

**Start** or **Continue** on the Check row opens **Remediation** for that signed review. The signed decisions stay as they were signed. On this page `decision` is the recommendation and can change.

Open rows are under **Deviations**. A row that has passed its re-check, or that has been retired, leaves that list. Passed rows are under **Remediated** and have no actions. A retired Check is closed. It is not called a pass.

Each open Check row has one **Actions** menu:

| Action | What it does |
| --- | --- |
| Find | Shown when the evidence file is missing. Lists files in the product tree with the same name. Choosing one writes that path into the Claim, signs the Claim, and runs the Checks. |
| Edit check | Opens the check editor for that row. |
| Add comment | The note on this Check. It replaces the previous note, or clears it. It is not a history entry. |
| Re-check | Runs every Check, then updates the deviations that belong to this review. |
| Retire | Removes that Check from the Claim now. If no Check remains, the Claim file is removed. The history records `action` `retire`. |

**Re-check** at the bottom of the page is the same full run. It stays on this remediation. It does not create a new row on Check.

A full run can fail a Check that was not one of this review's deviations. That is **Checks outside the original report**. Those Checks are not added to the queue. **OK** records the event on this remediation. **Rollback** puts back only the latest Studio change of the Claim, when there is one. A file changed outside Studio is left as it is. There is no Rollback when Studio has no change to restore.

The history column lists what was done: a re-check that changed the outcome, a retire, or a rebind. The comment sits in the Comment column.

**Notes** above the queues are about this round, for example work that a full Check should still cover. They travel with Sign Off.

**Save** keeps the open remediation and stays on the page. **Cancel** returns to Check. **Sign Off** asks for the name of the person who did the work, seals the remediation, writes the readable report, and returns to Check. The Remedy column then says **Completed**. The signature covers the work and the history. It does not change the signed review decisions, and it is not a new review decision.

A completed remediation can be opened read-only. **Run Check** there starts the next Check. **Revoke signature** asks for a name, opens the remediation again, and leaves the signed file in place.

The next Check can offer **Take in the remediation report**. The report keeps its review items. Where the underlag is unchanged, the signed decision is filled in, including a prepared **Accept**. Where the underlag changed, that decision is not reused. The history stays visible either way. **Keep the new decisions** leaves the decisions that the new run filled in. A Check that the remediation report contains and the new run does not is retired only when the history has `action` `retire`.

## 3. What a green result means

A green result means the Checks that ran passed for that tree. A person still decides what that means. A Check that passed during remediation does not rewrite the signed review.

If the evidence moved, use **Find** or **Edit check** on the open remediation row, then re-check. Closing a dialog writes nothing.

## 4. Inspect the evidence

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

A missing file is `fail`. A `skipped` row exists only because someone supplied a reason. Do not treat it as a pass.

This Retire is not the Retire control in Claims Editor. That control deletes the Claim file immediately, with no remediation history and no remediation report.

## Technical reference

* [Studio-internal](../reference/studio-internal.md) — `review_item`
* [Workspace](../reference/workspace.md) — where a Check, its review, and its remedy are stored
* [From the first Check to a closed review](../concepts/check-to-closed-review.md)
* [Packs v2](../reference/packs2.md) §3.1 and §6
* [Evidence](../concepts/evidence.md)
