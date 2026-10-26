# Getting Started: the reference product

Never used Studio and want to see what a Check observes before touching your own repository?

## Start here

Glucose Log (`cyberready-test-product`) is a small product with documentation you can edit. This walkthrough builds a disposable workspace, selects one Pack, and writes two Claims. One watches `SECURITY.md`. The other watches a heading in `docs/medtech/software_safety_class.md`. You then break each file and watch the matching row move.

**Prepare sample workspace** on the Studio cover creates a different tiny demo. It does not clone Glucose Log and it does not replace this walkthrough.

The browser Check always reads the workspace you started with: `packs/` for Packs and `product/` for the repository. A clone that sits somewhere else is not the tree the button evaluates. The shell command below uses those same two directories.

The steps that move and edit files work on Windows, macOS and Linux. The examples use a shell. The same edits can be made in an editor.

This walkthrough is a guided experiment. A written pilot record still needs the product revision, the Pack, the Claims, and the observed rows. Opening the pages is not that record. The JSON below was checked with `python3 -m checks` against copies of `SECURITY.md` and `docs/medtech/software_safety_class.md` from a local Glucose Log tree. It is not a claim that a particular upstream revision, or a published Studio binary, was exercised.

## 1. Create the workspace and clone the product

```bash
mkdir -p ~/curbpack-playground/packs/walkthrough
git clone https://github.com/RI-SE/cyberready-test-product.git ~/curbpack-playground/product
cd ~/curbpack-playground/product
git rev-parse HEAD
git status
```

Use a URL you can actually clone. Record the commit. Keep the checkout disposable.

If `product/claims/` already contains JSON files, move them aside before you add the two Claims in the next section. A Claim whose Requirement is not in the selected Pack makes Check stop with an error and write no result.

```bash
mkdir -p ~/curbpack-playground/product/claims/_aside
find ~/curbpack-playground/product/claims -maxdepth 1 -name '*.json' -exec mv {} ~/curbpack-playground/product/claims/_aside/ \;
```

Studio reads `curbpack.json`. A file named `.curbpack.json` in the clone is not the selection file.

## 2. Write the Pack, the Requirements, and the Claims

The Pack is metadata. Each Requirement names one provision. Each Claim names the file and the questions.

`~/curbpack-playground/packs/walkthrough/pack.json`:

```json
{
  "id": "walkthrough",
  "name": "Walkthrough",
  "version": "0.1.0",
  "description": "Two requirements for the Glucose Log exercise."
}
```

`~/curbpack-playground/packs/walkthrough/WALK-SECURITY.json`:

```json
{
  "id": "WALK-SECURITY",
  "pack_id": "walkthrough",
  "source": {
    "framework": "example",
    "instrument": "Glucose Log exercise",
    "identifier": "WALK-SECURITY",
    "language": "en",
    "url": "https://example.invalid/walkthrough"
  },
  "references": [
    {
      "nr": 1,
      "locator": "security-reporting",
      "law_text": "The product describes how to report a vulnerability."
    }
  ]
}
```

`~/curbpack-playground/packs/walkthrough/WALK-SAFETY-CLASS.json`:

```json
{
  "id": "WALK-SAFETY-CLASS",
  "pack_id": "walkthrough",
  "source": {
    "framework": "example",
    "instrument": "Glucose Log exercise",
    "identifier": "WALK-SAFETY-CLASS",
    "language": "en",
    "url": "https://example.invalid/walkthrough"
  },
  "references": [
    {
      "nr": 1,
      "locator": "safety-class",
      "law_text": "The product records its software safety classification rationale."
    }
  ]
}
```

`~/curbpack-playground/product/curbpack.json`:

```json
{
  "packs": ["walkthrough"]
}
```

`~/curbpack-playground/product/claims/walk-security.json`:

```json
{
  "id": "walk-security",
  "requirement_id": "WALK-SECURITY",
  "source": "documents",
  "args": { "path": "SECURITY.md" },
  "description": "SECURITY.md is the product's vulnerability reporting note.",
  "checks": [
    { "check": "exist", "args": { "paths": ["SECURITY.md"] } },
    {
      "check": "contents",
      "args": {
        "path": "SECURITY.md",
        "probes": [{ "kind": "headers", "headers": ["# Security"] }]
      }
    }
  ]
}
```

`~/curbpack-playground/product/claims/walk-safety-class.json`:

```json
{
  "id": "walk-safety-class",
  "requirement_id": "WALK-SAFETY-CLASS",
  "source": "documents",
  "args": { "path": "docs/medtech/software_safety_class.md" },
  "description": "The safety-class note contains the classification rationale heading.",
  "checks": [
    {
      "check": "exist",
      "args": { "paths": ["docs/medtech/software_safety_class.md"] }
    },
    {
      "check": "contents",
      "args": {
        "path": "docs/medtech/software_safety_class.md",
        "probes": [{ "kind": "headers", "headers": ["## Classification Rationale"] }]
      }
    }
  ]
}
```

These objects are unsigned. Check evaluates them anyway. `source.edition` is required only when a Requirement is published. The exercise does not publish this Pack.

The new files make the product worktree dirty until you commit them in the disposable clone. A dirty tree can still pass. The result then says it is not verification of that commit's content.

## 3. Start Studio on that workspace

Follow [Install](install.md). From the Studio checkout:

```sh
python3 -m app --workspace "$HOME/curbpack-playground"
```

Open `http://127.0.0.1:8770` unless you set another port. The cover is the check that the application started.

## 4. Read the three parts before you change a file

On `walk-security`, find these by hand:

1. Requirement `WALK-SECURITY` and its `references[].law_text` in `packs/walkthrough/WALK-SECURITY.json`.
2. The path `SECURITY.md` on the Claim and on both Checks.
3. The two rows **Run curbcheck** will print for that Claim.

```text
Requirement
   ↓
Claim about this product
   ↓
repository file
   ↓
Check row
```

The product tree also contains `src/`, `tests/`, `README.md`, `docs/`, and other notes. The two Claims above do not watch those files. Editing them will not move these rows.

## 5. Run on the unchanged tree

On the cover, **Check** (`/check`) → **Run curbcheck**.

The same evaluation from a shell, without the browser:

```sh
python3 -m checks \
  --repo "$HOME/curbpack-playground/product" \
  --packs "$HOME/curbpack-playground/packs" \
  --out "$HOME/curbpack-playground/product/.curbpack/run-result.json"
```

`--packs` is the directory that contains `<pack-id>/pack.json`. It is not a list of ids. The ids come from `product/curbpack.json`.

On the files this exercise uses, the first run prints:

```text
pass    walk-safety-class
  pass    [0] exist
  pass    [1] contents
pass    walk-security
  pass    [0] exist
  pass    [1] contents
```

Exit 0 means at least one Check ran and every row passed. No rows is exit 1. A dirty worktree can still exit 0. The command then says the result is not verification of that commit's content.

Record the commit from section 1, `walkthrough` version `0.1.0`, both Claim ids, and these rows.

Discovery (`/discover`) searches for candidate files. A candidate is not a result, and this exercise does not need it. The Claims are already saved.

## 6. Remove evidence and run again

Move `SECURITY.md` aside in this disposable checkout only:

```bash
cd ~/curbpack-playground/product
mv SECURITY.md SECURITY.md.bak
```

Run the same Check again. The Pack and `curbpack.json` have not changed. Only the tree changed.

`walk-security` fails on both Checks. The detail on each is `SECURITY.md is absent`. The contents row does not add a missing-header complaint. `walk-safety-class` still passes. The process exits 1.

Restore it and run again:

```bash
mv SECURITY.md.bak SECURITY.md
```

Both Claims pass again. Avoid `git restore .` if you have any other uncommitted work.

## 7. Change evidence without removing the file

A file can exist and still fail a content probe.

Open:

```text
docs/medtech/software_safety_class.md
```

The file contains:

```text
## Classification Rationale
```

Temporarily remove that heading. Leave the rest of the file in place.

Run Check again.

`walk-safety-class` passes `exist` and fails `contents`. The contents detail is `docs/medtech/software_safety_class.md is missing header '## Classification Rationale'`. `walk-security` still passes. The process exits 1.

Restore only that file:

```bash
git restore docs/medtech/software_safety_class.md
```

Run Check again. Both Claims pass.

## 8. Inspect the configuration behind the row

For the row you just watched, open:

- the Requirement's `source` and `references[]` in `packs/walkthrough/`;
- the Claim's `requirement_id`, `description`, source `args`, and `checks[]`;
- the Check row's index, check id, arguments, status, and detail.

`severity` on a Claim, when present, is the product's triage label. It is not the Requirement's legal `strength`.

## 9. What you have tested

Two changes, same Pack, same Claims, same command:

- `SECURITY.md` was removed, and both Checks on `walk-security` failed because the file was absent;
- `docs/medtech/software_safety_class.md` remained, `exist` passed, and `contents` failed because the heading was gone.

```text
selected Packs
     +
Claims and their checks[]
     +
current product tree
     ↓
curbcheck
     ↓
rows for the Checks that ran
```

A full pilot demonstration also includes a permitted skip and a signed review. Skip is a reason passed to the runner (`--skip claim-id=reason`). An empty reason is a usage error and writes nothing. The Check page has no skip form. The shell command does. After the run, Review compiles the report, the reviewer writes their own sentence, and review-sign seals that report. The Requirement file is not modified by that signature.

## 10. Restore the reference product

```bash
git status --short
```

Undo only the edits you made. Run the same Check again. Keep the earlier signed report if you created one. Check does not delete it. The server writes the report at `product/docs/reports/review-report.json`. Review then says `same run: no. This saved report is an older run.` when the loaded run result differs. Compiling a replacement asks you to confirm that the previous decision is not copied.

## 11. Next: your own repository

The reference product exists so the relationships stay small enough to inspect. On your own repository you choose which Requirements apply, write Claims for evidence that is actually true of that product, and have a person review the observations.

Do not copy these two Claims across and treat a pass as coverage of an instrument.

Continue with the [developer guide](developers.md).
