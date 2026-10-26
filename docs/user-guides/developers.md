# Using Studio in a product repository

This guide is for people working in a real product repository.

If you have not seen a Check fail because a file moved, do the [reference-product walkthrough](getting-started.md) first. For how to start the application, see [Install](install.md).

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

## 2. Select the Pack and the workspace

Pack Editor (`/requirements`) lists editable Packs. **Add document** asks for the adapter, the document name, the official name and the URL. Saving that document does not extract, sign, or publish. The page says the adapter cannot be changed later. A second adapter means a second document.

**Edit** opens that Pack's sources. **Add section** registers a section from the adapter. Registering a section does not extract it. **Extract** runs on the selected source and produces unsigned Requirement candidates in a dated working copy. Failure must not replace Requirements you already accepted. **Compare** and **Consolidate** are how a later extraction is applied: you see additions, modifications and possible removals, and you choose what to write. Cancel leaves the working copy as it was.

A product repository selects Packs by writing `curbpack.json`:

```json
{
  "packs": ["cra-baseline"],
  "hunt": {
    "sources": [{ "source": "documents" }],
    "exclude_path_globs": ["**/node_modules/**", "*FUTURE_*"],
    "prefer_path_globs": ["**/docs/**", "**/SECURITY*", "**/README*"]
  }
}
```

Check loads those ids from the packs root. Two ids select both Packs. They are not merged, and one does not override the other. Start Studio with `--workspace` when this product should not share the default `data/workspace`. The browser Check reads that workspace's `product/` and `packs/`.

**Prepare sample workspace** is the cover's demo helper. It does not select a Pack for your repository.

## 3. Run the first Check

```text
/check → Run curbcheck
```

or:

```sh
python3 -m checks --repo /path/to/your/product-repo \
  --packs /path/to/packs-root \
  --out /path/to/your/product-repo/.curbpack/run-result.json
```

On a repository that has just been pointed at a Pack, expect failures until Claims name evidence the product actually has, and until that evidence meets the probes.

A row names the Claim id, each Check index, the Check id, the status, and a detail when the status is not `pass`. Read it as: this Claim's arguments did not hold. The practical question is which file and which probe, and whether the product or the Claim should change.

An empty row list is not a successful verification. The process exits 1. A Claim whose `requirement_id` is not in the selected Pack makes the runner stop with an error and write no result.

A `contents` row whose `placeholder` probe failed, or an `exist` row whose path is absent, is the observation. `severity` is on the Claim when you set it. It is not printed as a gate badge.

## 4. Investigate and fix a finding

Read the row. Nothing writes a proposed file from a failure.

- Discovery lists candidate paths for a Requirement. A candidate is not a Claim. Useful and Poor marks stay in workspace feedback.
- The Requirement's `remediation_hint` and `law_text` are text you read. They are not applied as a patch.
- Scaffold (`/scaffold`) can write a new file at a relative path and refuses to overwrite. Broader automatic remediation is deferred. A stub that passes `exist` has only shown that the stub exists.

When a row concerns `SECURITY.md`:

1. Read the Check id, the arguments, and the detail.
2. Edit the product file so the statement is true, or edit the Claim if the arguments were wrong.
3. Save the Claim in the Claims editor if you changed it. A payload change drops `signed`.
4. Run the same Check again.

The row clears only when the arguments hold. Editing the Claim does not change the published Requirement.

The working loop is:

```text
Run curbcheck
      ↓
read the row
      ↓
read the Requirement text and the file
      ↓
change the product, or explicitly edit the Claim
      ↓
Run curbcheck again
```

## 5. During normal development

After the Pack is selected and the Claims exist, the command you repeat is the Check above.

Run it after changes to files the Claims name. A previous pass describes the tree that was checked. Claim edits and a new Check do not require a new Extract.

## 6. Create review material

On **Review** (`/review`), **Compile** writes one report from the run result and the Requirement and Claim files that run named. The server writes `<product-repo>/docs/reports/review-report.json`.

Compile does not run Checks and does not commit. You may commit the report afterwards. That commit is a later revision of the product repository. It is not `run_result.commit`.

Keep the pack id, version, directory digest, commit, and worktree value with the report if someone has to reproduce the run.

## 7. Human decision and review-sign

On the review page the reviewer writes `decision` in their own words and then review-sign. The signature covers the report, including that sentence. It is not the Requirement seal and not the Claim seal. Claim sealing is a separate action in Claims, after the person has looked at the evidence and the configured Checks. A passing Check does not sign a Claim.

The page states that a passing Check does not mean the legal requirement is fulfilled, and that the report has no field for a conclusion that the product meets CRA.

## 8. Re-check after later changes

Run Check again on the new tree.

The earlier signed report and the new run result are two snapshots. When both are loaded, Review says whether they are the same run. An older saved report is labeled `This saved report is an older run.` Do not describe it as the current run. Replacing it is a Compile with the confirmation checkbox. The previous decision is not copied forward.

A failed row can stay on the review page while you open Discovery for that Requirement, add a new Claim, and retire the old Claim yourself.

## 9. Next: run the Check where the repository changes

Continue with [CI/CD](ci-cd.md). The Check you automate is `python3 -m checks`.
