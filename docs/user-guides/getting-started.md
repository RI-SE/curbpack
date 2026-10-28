# Getting started

Start Curbpack Studio with [Install](install.md) and open the URL the program prints. The usual one is `http://127.0.0.1:8770`.

The cover is the pilot. Four links, in the order you use them the first time:

1. **Pack Editor** turns a source into Requirements.
2. **Discovery & Claims** finds candidate files and saves the Claims a person accepts.
3. **Check** runs curbcheck against the packs named for that repository.
4. **Review** compiles that run, records a decision, and can sign the report.

You can come back to any of them. A later Check does not require a new Extract.

A green row is what the questions on that Claim observed. A person still decides what that means.

## 1. Pack Editor

Open **Pack Editor**.

**Pack Sources** lists the documents. **Sections** opens one document. **Add** registers a section from its adapter. Registering a section does not extract it.

**Extract** writes a separate working copy. If you are already editing a copy, you choose which fields to bring in. Fields you leave out stay as they are. A failed extract does not replace Requirements you already accepted.

Each Requirement still needs a person. **Edit** and **Sign** are that review. Signing a Requirement is not a check of a product, and it is not the signature on a review report.

## 2. Discovery & Claims

Open **Discovery & Claims**.

Pick a repository, then the working copy or the published release. The table is one row per section: how many Requirements, how many Claims, and how many Requirements have no Claim.

Open a section to see candidate files. **Useful** and **Poor** mark a finding. That mark is not stored on the Claim, and a candidate is not a check result.

A discovery sentence can differ from the motivation already saved on a Claim. Keep the saved motivation, or take the new sentence. Taking it replaces the motivation and removes the Claim signature.

The Claim you save, with its checks, is what Check will run.

## 3. Check

Open **Check**.

Choose the repository, tick the packs it uses, and **Save**. That writes `curbpack.json` into the repository. The file is not signed. A file named `.curbpack.json` is not the selection.

**Check** runs curbcheck. The report lists each Claim and each check: status and, when it did not pass, a detail. No rows is not a successful verification.

Read a failed row as "these arguments did not hold." The next step is the file and the question, and whether the product or the Claim should change. The page does not write a fix for you.

## 4. Review

Open **Review**.

**Compile** writes one report from the run that just happened, including the Requirements and Claims that run named. Compile does not run the checks again.

**Save decision** stores the reviewer's own words. **review-sign** seals that report, including that sentence. The signature is not the Requirement seal and not the Claim seal.

The page says there is no field for a conclusion that the product meets a regulation.

## 5. After the first pass

Change the product, or change a Claim, and run **Check** again. The previous report stays the record of the earlier run. Compiling a replacement asks you to confirm that the previous decision is not copied.

The same four pages are the work on your own repository. The longer procedure for a real product tree, including what to do with one failed row, is the [developer guide](developers.md).
