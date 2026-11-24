# Using Studio in a product repository

This guide is for product teams using Studio on their own repository. To develop Curbpack itself, see [Development](../development/README.md).

[Getting started](getting-started.md) is the first pass through Pack Editor, Discovery & Claims, Check, and Review. This guide gives the longer procedure on a real product repository. For the downloaded program, see [Install](install.md).

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

For human review, open **Review** (`/review`) in Studio and choose the same repository. The report brings together the Check results, Claim evidence arguments, and signature information. See section 6 for compiling and opening saved reports.

## 4. Investigate and fix a finding

Read the failed Check's detail and its configured arguments. In Studio, Review provides the Claim context; **Open the Claim** opens the Claims editor. Nothing writes a proposed file from a failure.

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

## 6. Create review material

On **Review** (`/review`), choose the product under **Repo** and open a Check result. **Save** writes the decisions and notes into that Check's `review_items.json` and leaves the review open. **Sign** locks those decisions and writes `review-report_<YYYYMMDDTHHMMSSZ>.json`. Remediation starts from that signed review. An older flat run writes its signed snapshot under `reports_dir`.

To open a saved report, use `/review?repo=<repo-id>&report=<URL-encoded-absolute-report-path>`. A snapshot inside a Check directory, or a `review-report_*.json` inside `reports_dir`, both open read-only. The current page has a repository selector but no report picker.

Save and Sign do not run Checks and do not commit. You may commit a snapshot afterwards. That commit is a later revision of the product repository. It is not `run_result.commit`.

When a Check is marked Retire, Save stores that disposition and its comment on the review work, and stores whether signing a report should remove the Check from the live Claim. The Check result itself stays `pass`, `fail`, or `skipped`.

Keep the pack id, version, directory digest, commit, and worktree value with the report if someone has to reproduce the run.

## 7. Human decision and review-sign

On the review page the reviewer writes `decision` in their own words and then review-sign. The signature covers the report, including that sentence, the assessments, `items_digest`, and `remove_retired_checks`. It is not the Requirement seal. The same action signs `review-report_<stamp>.items.json`. `items_digest` is that file's version digest. The signed `review_items.decision` values are what reporting reads.

When `remove_retired_checks` is false, or absent, review-sign does not change Claim files. When it is true, the same step then removes the retired Checks from the live Claims. A Claim that still has a Check is signed again by the report signer. A Claim with none left is deleted. The Claim copied into the report is left as it was. A passing Check does not by itself sign a Claim.

```text
Check
  -> Check result
  -> Review: Retire, with a comment
  -> report
  -> review-sign
  -> remove the Checks from the Claim files, only if the report said so
```

The page states that a passing Check does not mean the legal requirement is fulfilled, and that the report has no field for a conclusion that the product meets CRA.

## 8. Re-check after later changes

Run Check again on the new tree.

The earlier signed report and the new run result are two snapshots. When both are loaded, Review says whether they are the same run. An older saved report is labeled `This saved report is an older run.` Do not describe it as the current run. **Sign** creates a new dated snapshot and preserves the earlier file. The previous decision is not copied forward.

A failed row can stay on the review page while you open Discovery for that Requirement, add a new Claim, and delete the old Claim yourself in Claims Editor.

## 9. Next: run the Check where the repository changes

Continue with [CI/CD](ci-cd.md). The Check you automate is `curbcheck`.
