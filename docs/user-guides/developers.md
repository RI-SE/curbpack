# Using Studio in a product repository

This guide is for product teams using Studio on their own repository. To develop Curbpack itself, see [Development](../development/README.md).

[Getting started](getting-started.md) is the first pass through Pack Editor, Discovery & Claims, Check, Review, and Remediation. This guide gives the longer procedure on a real product repository. For the downloaded program, see [Install](install.md).

You can rerun Discovery, Claim edits, or Check without repeating Extract.

## 1. Inspect the product repository

Go to the Git root:

```bash
cd /path/to/your/product-repo
git status --short
git rev-parse HEAD
```

Note which evidence files exist. A dirty tree can be checked. A result from that tree does not verify the commit named in the result.

Discovery is the read of the tree that looks for candidates. It writes a candidate list and does not write a Check result. Opening Discovery does not mean the product passed.

Studio reads `curbpack.json`. A file named `.curbpack.json` is not the selection file.

## 2. Select the Pack and repository configuration

Pack Editor (`/requirements`) lists editable Packs by Pack name, official name and adapter. The Pack name shown is the namespace. **Add Pack Source** asks for the adapter, the Pack name and the official document name and the URL. The Pack name field shows `namespace_base` from `curbpack.json` in front of the name. That prefix is not editable. A Pack name whose namespace or id is already listed in that file is refused. Saving does not extract, sign, or publish. A second adapter means a second Pack.

**Edit Pack Source** opens that Pack's fields. **Edit Sections** opens that Pack's sources. **Add section** registers a section from the adapter. Registering a section does not extract it. **Extract** runs on the selected source and produces unsigned Requirement candidates in a dated working copy. Failure must not replace Requirements you already accepted. **Compare** and **Consolidate** are how a later extraction is applied: you see additions, modifications and possible removals, and you choose what to write. Cancel leaves the working copy as it was.

A product repository selects Packs by writing `curbpack.json`:

```json
{
  "packs": ["cra-baseline"],
  "search_hints": {
    "sources": [{ "source": "documents" }],
    "exclude_path_globs": ["**/node_modules/**", "*FUTURE_*"],
    "prefer_path_globs": ["**/docs/**", "**/SECURITY*", "**/README*"]
  },
  "packs_dir": "curbpack/packs",
  "claims_dir": "curbpack/claims",
  "results_dir": ".curbpack",
  "reports_dir": "curbpack/reports",
  "namespace_base": "RISE"
}
```

Check reads these paths relative to the product repository. Packs live at `<packs_dir>/<pack-id>/<pack-version>/pack.json`, with the Requirement JSON files beside `pack.json`. Claims live directly in `claims_dir`. Two ids in `packs` select both Packs. Use `requirements` to select specific Requirement ids, or `exclude_requirements` to leave some out; those two fields are mutually exclusive.

In Studio, choose the product repository with **Repo**. Check, Discovery, Compile, and Review use that repository's `curbpack.json`. Studio's `--workspace` selects its own working area; the product data paths come from the chosen repository's configuration. See [Workspace configuration](../reference/workspace.md) for all fields and the separate `curbpack-studio.json`.

**Prepare sample workspace** is the cover's demo helper. It does not select a Pack for your repository.

## 3. Run the first Check

In Curbpack Studio, open **Check** (`/check`), choose the product under **Repo**, and click **Check**.

From a terminal:

```sh
curbcheck --repo /path/to/your/product-repo
```

That reads the repository's `curbpack.json`, loads Packs from `packs_dir` and Claims from `claims_dir`, and prints a text summary. To save JSON as well, add `-j` for `<results_dir>/run-result_<YYYYMMDDTHHMMSSZ>.json`, or `-o /tmp/run.json` for an explicit output file. Studio's Check saves a dated run result in `results_dir` automatically.

For debugging, `--packs` and `--requirements` take comma-separated id lists that select what this run checks:

```sh
curbcheck --repo /path/to/your/product-repo \
  --packs house-policy,cra-baseline \
  --requirements HOUSE-SECURITY-REPORTING,CRA-ART14-PATH \
  -j
```

Replace the example ids with ids present in your Packs. The filters apply to this run without changing `curbpack.json`. Paths still come from its directory fields. `--out` takes one JSON file path.

A failed run can print:

```text
claims 1 exit 1
fail    HOUSE-SECURITY-MD
  pass    [0] exist
  fail    [1] contents — SECURITY.md is 17 bytes, not >= 80; SECURITY.md has 3 words, not >= 20
```

The first line counts evaluated Claims and gives the process exit code. Each Claim has a status, followed by its Checks with a zero-based index, Check id, status, and any failure or skip detail. Here the file exists, but its content fails the configured minimum byte and word counts. This is a Check result; it does not decide whether the human rationale in the Claim is sound or the Requirement is fulfilled.

Exit 0 requires at least one executed Check and every included Claim and Check to pass. Failure, skip, or no executed Checks gives exit 1. Claims with no Checks are not evaluated. Claims outside the selected Requirements are filtered out. Selecting a Pack alone does not create Claims or verify its Requirements. See [curbcheck](../reference/curbcheck-cli.md) for the full output and exit-code reference.

For human review, open **Check** and use the row in **Checks performed**. **Create** or **Continue** opens the review of that run. See section 6.

## 4. Investigate and fix a finding

Read the failed Check's detail and its configured arguments. The review queue shows the Requirement, the file, and the Check. Nothing writes a proposed file from a failure. Changing the Check, or the path it names, is a remediation action after the review is signed. See section 6.

- Discovery lists candidate paths for a Requirement. A candidate is not a Claim. Useful and Poor marks stay in workspace feedback.
- The Requirement's `remediation_hint` and `law_text` are text you read. They are not applied as a patch.
- Scaffold (`/scaffold`) can write a new file at a relative path and refuses to overwrite. Broader automatic remediation is deferred. A stub that passes `exist` has only shown that the stub exists.

When a row concerns `SECURITY.md`:

1. Read the Check id, the arguments, and the detail.
2. Edit the product file so the statement is true, or edit the Claim if the arguments were wrong.
3. Save the Claim in the Claims editor if you changed it. A payload change drops `signed`.
4. Run the same Check again.

After rerunning, inspect the new result to see whether the configured Check passes. Editing the Claim does not change the published Requirement.

The working loop is:

```text
Run Check
      ↓
read the row
      ↓
read the Requirement text and the file
      ↓
change the product, or explicitly edit the Claim
      ↓
Run Check again
```

## 5. During normal development

After the Pack is selected and the Claims exist, the command you repeat is the Check above.

Run it after changes to files the Claims name. A previous pass describes the tree that was checked. Claim edits and a new Check do not require a new Extract.

## 6. Review and remediation

Work from **Check**. Each run is one directory under `results_dir`, named `run-result_<YYYYMMDDTHHMMSSZ>/`, with `run-result.json` inside it. The table row is that directory. An older flat `run-result_<stamp>.json` stays where it was written.

**Save** on Review writes the decisions and the notes into that directory's `review_items.json` and returns to Check. The review is still open. **Sign** asks for a name, locks those decisions, writes and signs `review-report_<YYYYMMDDTHHMMSSZ>.json` in the same directory, and returns to Check. The signed review opens read-only. Save and Sign do not run Checks and do not commit.

The decisions on a signed review stay as signed. Remediation is a separate copy of the work: **Start** after a signed review, then **Continue** until **Sign Off**. On that copy the decision is a recommendation. A comment is the current note on the Check. History records a re-check that changed the outcome, a retire, or a rebind.

**Retire** in remediation removes that Check from the live Claim immediately, or removes the Claim when no Check remains, and appends `action` `retire`. It does not turn the Check result into `pass`. **Find** writes a chosen same-named path into the Claim and signs that Claim. **Re-check**, whether from the row or from the bottom of the page, runs every Check and projects the original deviations. A new failure outside those deviations is recorded on the remediation when you choose **OK**. It is not added to the queue. **Rollback** restores only the latest Studio change of the Claim.

**Sign Off** seals `remedy-report_<YYYYMMDDTHHMMSSZ>.json` in the Check directory, publishes the readable report, and returns to Check. The seal is a remedy report. It does not replace the signed review and it does not set a new review decision. **Revoke signature** opens the remediation again and leaves the sealed file in place.

```text
Check
  -> review_items.json
  -> Sign locks the review and writes the review report
  -> Remediation: comment, Find, Edit check, Re-check, Retire
  -> Sign Off writes the remedy report
  -> the next Check can take that report in
```

A Check started from an open remediation is stored apart from **Checks performed** and does not become its own row. The next full Check from the Check page is a new row. That review can take in the latest signed remediation: unchanged underlag fills the signed decision, and the history is shown either way. Taking it in does not set `decision` from the history.

`review_item` is defined in [Studio-internal](../reference/studio-internal.md). Paths are in [Workspace](../reference/workspace.md). The page walkthrough is [Reviewing](reviewers.md).

Technical details still state that a passing Check does not mean the legal requirement is fulfilled, and that the report has no field for a conclusion that the product meets CRA.

## 7. What the signature covers

Review-sign seals the review report. It is not the Requirement seal and it is not the Claim seal. The signed `review_items` decisions are what a later review can reuse. Remediation does not edit that sealed decision.

Sign Off seals the remedy document: the items, the history, the round notes, and any acknowledged Check that fell outside the original deviations. Reading that seal uses `what` `remedy report`.

A passing Check does not by itself sign a Claim. Find and a rebound Claim are signed by the person named on that action.

## 8. Re-check after later changes

Run Check again on the new tree. That is a new row.

The earlier signed review and the new run are two snapshots. Technical details say `same run: yes` or `same run: no. This saved report is an older run.` Do not describe the older report as the current run. The previous signed file stays. A decision is filled in again only when the new review takes in a remediation report and the underlag is unchanged.

## 9. Next: run the Check where the repository changes

Continue with [CI/CD](ci-cd.md). The Check you automate is `curbcheck`.
