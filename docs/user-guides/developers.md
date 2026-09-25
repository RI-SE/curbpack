# Using Curbpack as a Developer in a Product Repository

This guide is for developers using Curbpack in a real product repository.

If you have not used Curbpack before, start with the reference-product walkthrough.
This lets you install Curbpack and inspect packs, claims, evidence, and check results
without first adding Curbpack artifacts to your own repository.

For installation, see [`install.md`](install.md).

## 1. Inspect Your Repository with `scan`

Go to the Git root of the product repository:

```bash
cd /path/to/your/product-repo
```

Start with a read-only scan:

```bash
curbpack scan
```

`scan` inspects the repository without initializing Curbpack or changing repository
files.

Its purpose is diagnosis: it shows what Curbpack can observe in the repository and
what configuration and evidence it currently finds. A completed scan is not the same
thing as a passing Curbpack check.

For example, a scan may report that expected material has not yet been found even
though the scan command itself completes successfully.

If the repository already contains `.curbpack.json`, inspect it before continuing.
The file identifies which packs are selected for this product.

## 2. Initialize Curbpack

Before initializing, you can see the packs currently available to Curbpack:

```bash
curbpack packs list
```

To initialize the repository with the default pack selection:

```bash
curbpack init
```

Or select packs explicitly:

```bash
curbpack init --packs <pack-id>[,<pack-id>...]
```

Initialization creates `.curbpack.json` and prepares the repository for the current
Curbpack workflow.

Afterwards, inspect the configuration:

```bash
cat .curbpack.json
```

The `packs` entry is the pack selection that `curbpack check` will evaluate.

Also inspect any other files created by `init`. The current implementation may add
scaffold or repository integrations in addition to `.curbpack.json`. Scaffold is
only starter material and must not be treated as real product evidence until it has
been reviewed and replaced with product-specific content.

For more detail about packs and configuration, see:

- [`../concepts/packs.md`](../concepts/packs.md)
- [`../reference/configuration.md`](../reference/configuration.md)

## 3. Run the First Check

Now evaluate the repository against the selected packs:

```bash
curbpack check
```

This is different from `scan`.

`scan` is a read-only diagnostic view of the repository.

`check` evaluates the current repository against the selected pack rules and reports
the pass/fail result used by the current Curbpack workflow.

On a newly initialized real repository, you should expect findings until the
required product evidence has actually been provided.

For example, output may contain a finding such as:

```text
○ [high] HOUSE-ANTI-PLACEHOLDER — SECURITY.md
  (not started — fill this in)
```

Read this as:

- the selected pack contains the rule `HOUSE-ANTI-PLACEHOLDER`;
- the rule concerns `SECURITY.md`;
- the current repository does not yet contain acceptable evidence for that check.

You do not need to reconstruct the complete pack/claim/evidence model at this point.
The practical question is simply: **what does this finding refer to, and what needs
to change in the product repository?**

## 4. Investigate and Fix a Finding

When `curbpack check` reports a finding, start by asking Curbpack for a suggested
fix (proposal only):

```bash
curbpack ask .github/curbpack/cache/latest_failure.json --propose
```

This does not establish that the proposed text is correct for your product. Use the
proposal to understand what information is missing, then edit the relevant product
file with information that is actually true.

For example, if the finding concerns `SECURITY.md`:

1. inspect the finding and proposed remediation;
2. edit `SECURITY.md`;
3. save the change;
4. run the same check again:

```bash
curbpack check
```

The finding should disappear only when the repository satisfies the corresponding
pack check.

If needed, inspect the corresponding rule in the selected pack to understand what
the check expects.

For cases where files or scaffold are completely missing, Curbpack can also create
starter material:

```bash
curbpack check --heal
```

`--heal` may write stubs or scaffold. Review everything it creates and replace
placeholder material with product-specific content before considering the finding
resolved.

The normal developer workflow is therefore:

```text
curbpack check
      ↓
inspect a finding
      ↓
ask for guidance if useful
      ↓
make and review the product change
      ↓
curbpack check again
```

Repeat this after each relevant change until the current findings have been handled.

## 5. Use Curbpack during Normal Development

After initialization, you normally only need:

```bash
curbpack check
```

Run it after changes that may affect checked evidence, such as documentation,
dependencies, manifests, or files referenced by selected pack rules.

If a new finding appears, handle it as described above and run `curbpack check`
again.

A previous passing result only describes the repository state that was checked at
that time.

## 6. Create Review Material

When you want to hand the current result over for review, run:

```bash
curbpack share
```

This creates the current review material from the repository state and Curbpack
results.

Optional exports include:

```bash
curbpack export --context-pack
curbpack export --buyer-questions
```

These outputs are intended to support review and discussion.

Keep track of which repository state they were generated from if the result must be
reproduced later.

For details about generated artifacts, see [`../reference/outputs.md`](../reference/outputs.md).


## 7. Next: CI/CD

Once the local workflow works in your repository, the next step is to run the same
Curbpack checks automatically in CI.

Continue with [`ci-cd.md`](ci-cd.md).
