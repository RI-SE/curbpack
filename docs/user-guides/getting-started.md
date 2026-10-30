# Getting started

Start Curbpack Studio with [Install](install.md) and open the local URL printed by the program.

If you run Extract or Discovery assessment, Studio expects a local [Ollama](https://ollama.com) at `http://127.0.0.1:11434` with the model `qwen3-coder:30b` (`ollama pull qwen3-coder:30b`). This walkthrough's Check and Review path does not call it. The defaults live in `curbpack-studio.json` when that file is present; see [Configuration](../reference/configuration.md).

This walkthrough uses the Curbpack reference product. It is deliberately prepared so that you can first see a passing Check, then remove known evidence and see the same Check fail. The reference product has previously been used for this purpose: `SECURITY.md` is part of its expected evidence, and removing it changes the corresponding result.

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

The cover links the four activities you will use:

1. **Pack Editor** — inspect the Packs and Requirements.
2. **Discovery & Claims** — inspect how product evidence is connected to Requirements.
3. **Check** — evaluate the Checks defined by the Claims.
4. **Review** — compile the run for human review.

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

## 7. Remove known evidence

Now make one deliberate product change. Move `SECURITY.md` out of the way without deleting it permanently:

```bash
mv SECURITY.md SECURITY.md.bak
```

Nothing about the Requirement or Claim has changed. Only the product evidence has changed. This exact kind of reference-product exercise has previously been used to demonstrate the evidence relationship.

Run **Check** again in Studio.

Find the row associated with the missing `SECURITY.md` evidence. Compare it with the baseline result from the previous run.

Then run the command-line Check again:

```bash
curbcheck --repo .
```

The useful observation is not merely that something became red. Follow the failed row back through the model:

```text
Requirement
  -> Claim
      -> SECURITY.md
          -> Check
              -> fail
```

The Check tells you which configured technical condition no longer held. A person still decides what needs to be done about it.

## 8. Restore the evidence

Restore the file:

```bash
mv SECURITY.md.bak SECURITY.md
```

Run the Check once more:

```bash
curbcheck --repo .
```

The affected result should return to its prepared baseline state. The earlier reference-product exercise describes the same restore-and-rerun behaviour.

You have now exercised the central Curbpack loop:

```text
known product state
        -> Check
        -> change evidence
        -> Check again
        -> inspect the changed result
        -> restore or update the product
        -> Check again
```

## 9. Review the run

Return to Studio and open **Review**.

Compile the run into review material and inspect how the Requirement, Claim, and Check result are presented together.

The automated result stops at what the Check observed. Review is where a person records what that result means in context.

## 10. What to try next

At this point you have used a controlled repository where the expected relationship between Requirements, Claims, and evidence is already known. The reference product was created specifically to make that relationship testable and demonstrable.

Next, either:

- explore another Requirement and trace it to its Claims and evidence; or
- follow the [Developer guide](developers.md) to configure Curbpack for one of your own product repositories.

To create or maintain reusable Requirements, see [Create a Requirements Pack](pack-developers.md).
