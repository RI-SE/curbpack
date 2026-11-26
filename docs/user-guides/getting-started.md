# Getting started

Start Curbpack Studio with [Install](install.md) and open the local URL printed by the program.

If you run Extract or Discovery assessment, Studio expects a local [Ollama](https://ollama.com) at `http://127.0.0.1:11434` with the model `qwen3-coder:30b` (`ollama pull qwen3-coder:30b`). This walkthrough's Check, Review, and Remediation path does not call it. Those defaults are the built-in values until `~/.curbpack/curbpack-studio.json` sets them; a product `curbpack-studio.json` can override the model and prompts for that repository. See [Configuration](../reference/configuration.md).

This walkthrough uses the Curbpack reference product. It is deliberately prepared so that you can first see a passing Check, then delete known evidence, sign a review of the failure, restore the file during remediation, re-check, and sign the remediation report. `SECURITY.md` is part of the reference product's expected evidence, and removing it changes the corresponding result.

You will use the same repository in Studio and from the command line so that the relationship between Packs, Requirements, Claims, evidence, and Checks is concrete before you try Curbpack on your own product.

## 1. Clone the reference product

Clone the reference product and enter the repository:

```bash
git clone git@github.com:RI-SE/cyberready-test-product.git
cd cyberready-test-product
```

Before changing anything, take a quick look through the repository.

Find:

- `curbpack.json`, which selects the Packs used for this product;
- the Pack data selected for the product;
- the Claims belonging to the product;
- `SECURITY.md`, which is evidence used by one of the Claims.

Do not edit anything yet. The point of the first run is to establish the known baseline.

## 2. Open the repository in Curbpack Studio

Open the Curbpack Studio cover page and choose the cloned `cyberready-test-product` repository.

The cover links Pack Editor, Discovery & Claims, and Check. Review and Remediation are opened from a row under **Checks performed**, not from the cover.

1. **Pack Editor** — inspect the Packs and Requirements.
2. **Discovery & Claims** — inspect how product evidence is connected to Requirements.
3. **Check** — evaluate the Checks defined by the Claims.
4. **Review** — record a decision for the failed Check and **Sign**.
5. **Remediation** — open that signed review, restore the evidence, **Re-check**, and **Sign Off**.

You do not need to create or extract a new Pack for this walkthrough. The reference product is already prepared.

## 3. Inspect the Packs and Requirements

Open **Pack Editor**.

Use it to inspect the Packs selected for the reference product and open some of their Requirements.

At this stage, concentrate on the relationship rather than the file format:

```text
Pack
  -> Requirement
```

A Requirement describes what must be fulfilled. The Pack makes a reusable set of Requirements available to products.

Return to the Studio cover page when you have seen where the Requirements come from.

## 4. Inspect the Claims and evidence

Open **Discovery & Claims** for the same repository.

Look at how Requirements have Claims in the product repository. Open the Claim that uses `SECURITY.md` as evidence and inspect its configured Checks.

The important relationship is now:

```text
Requirement
  -> Claim
      -> evidence
      -> Checks
```

Discovery may suggest candidate evidence, but the saved Claim is the product team's maintained assertion about the evidence and the Checks to perform.

Do not change the Claim yet.

## 5. Run the baseline Check

Open **Check** and run the prepared Check against the reference product.

The first run should show the prepared baseline. Read a few rows and identify:

- the Claim being evaluated;
- the Check that was performed;
- the evidence it refers to;
- the result.

A green row means that the configured Check passed for the repository state that was evaluated. It does not mean that Curbpack has decided that the product is compliant.

## 6. Run the same Check from the command line

From the cloned reference-product repository, run the command-line Check against the same product configuration:

```bash
curbcheck --repo .
```

Compare the command-line result with the Check you just ran in Studio. Studio and the command line are two ways of running the same checking model against the product repository.

## 7. Delete known evidence and run Check

Now make one deliberate product change. Delete `SECURITY.md` from the working tree:

```bash
rm SECURITY.md
```

Nothing about the Requirement or Claim has changed. Only the product evidence has changed. The committed copy is still in Git. You put that copy back in a later step. Do not run `git restore .`. That can discard other work in the tree.

Run **Check** again in Studio.

Find the row associated with the missing `SECURITY.md` evidence. Compare it with the baseline result from the previous run. Follow the failed row back through the model:

```text
Requirement
  -> Claim
      -> SECURITY.md
          -> Check
              -> fail
```

The Check tells you which configured technical condition no longer held. A person still decides what needs to be done about it.

## 8. Review and sign

On **Check**, the run is a row under **Checks performed**. The Review column says **Create**. Open it.

The page leads with **Deviations**. Set the missing `SECURITY.md` deviation to **Must be fixed**. **Sign** asks for the signer name, locks that decision, writes the review report beside the Check, and returns to Check.

The Review column then says **View**. The Check result itself stays `fail`. Signing does not put the file back and does not start the fix.

## 9. Look at the remediation

The Remedy column now says **Start**. Open it.

This is the remediation for the review you just signed. The deviation is still open, because `SECURITY.md` is still absent. The signed decision stays **Must be fixed**. On this page that decision is the recommendation. It is not a new review decision.

Read the row: the Requirement, the missing file, and the failed Check. Do not retire the Check and do not point the Claim at a different file. The fix in this walkthrough is to put the evidence back.

## 10. Put the file back and re-check

Restore only that file from Git:

```bash
git restore -- SECURITY.md
```

Return to the open remediation and choose **Re-check**. Use **Re-check** on the row's **Actions** menu, or **Re-check** at the bottom of the page. Both run every Check and stay on this remediation. The run does not add a row under **Checks performed**.

The `SECURITY.md` Check should pass. That row leaves **Deviations** and appears under **Remediated**. The signed review still records the original failure and the **Must be fixed** decision. A pass during remediation does not rewrite that review.

## 11. Sign the remediation report

**Sign Off** asks for the name of the person who did the work, seals the remediation, writes the readable remediation report, and returns to Check.

The Remedy column says **Completed**. The report icon opens that report. The signature covers the restoration and the re-check. It does not replace the signed review, and it does not decide that the product is compliant.

You have now exercised the loop:

```text
known product state
        -> delete SECURITY.md
        -> Check
        -> Review and Sign
        -> open Remediation and read the deviation
        -> put the file back
        -> Re-check
        -> Sign Off the remediation report
```

The longer page walkthrough, including Find, Retire, and a later Check that takes the remediation report in, is [Reviewing](reviewers.md).

## 12. What to try next

At this point you have used a controlled repository where the expected relationship between Requirements, Claims, and evidence is already known. The reference product was created specifically to make that relationship testable and demonstrable.

Next, either:

- explore another Requirement and trace it to its Claims and evidence; or
- follow the [Developer guide](developers.md) to configure Curbpack for one of your own product repositories.

To create or maintain reusable Requirements, see [Create a Requirements Pack](pack-developers.md).
