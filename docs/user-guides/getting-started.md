# Getting Started: Try Curbpack on the Reference Product

Never used Curbpack and want to understand what it does before touching your own repository?

## Start Here

Curbpack checks a repository for evidence against a selected set of rules. The idea is simple: a pack defines claims that should be satisfied, the product repository contains evidence, and Curbpack reports whether the current repository state satisfies those claims. This kind of repository-level evidence is increasingly useful as software teams need to demonstrate security and regulatory work in a repeatable way, including for requirements arising from the EU Cyber Resilience Act (CRA).

This walkthrough uses the Curbpack reference product, **Glucose Log**, instead of your own code. Glucose Log is a fake product created for demonstration purposes. It contains a small software project with some code, documentation, a few simple packs with claims, and matching evidence.

This gives you a safe place to see how Curbpack works end to end. You can run the checks and see a passing result, inspect the pack rules and how they relate to the evidence in the repository, and then remove or change that evidence to see how Curbpack detects the change.

The goal is not to learn every Curbpack command. The goal is to understand how to make claims about a software product, support them with evidence, and automatically re-check those claims as the repository changes — for example, to catch when required evidence is accidentally removed in a later commit.

This walkthrough works on Windows with WSL2, macOS, and Linux. Some prepared demo states use shell scripts, but the same changes can also be made manually.

## 1. Create a Disposable Workspace

In the example below, we use the arbitrary name `curbpack-playground` and create it in your home directory. You can place the workspace anywhere you like.

```bash
# Create the disposable folder for your workspace
mkdir -p ~/curbpack-playground
cd ~/curbpack-playground

# Get the reference product repository
git clone git@github.com:RI-SE/cyberready-test-product.git
cd cyberready-test-product
```

## 2. Install the Curbpack Executable

Install Curbpack using the supported installer:

```bash
curl -fsSL https://raw.githubusercontent.com/RI-SE/curbpack/main/scripts/install.sh | sh
```

The installer places the `curbpack` executable in a user-local bin directory. If that directory is not already on your `PATH`, follow the PATH instruction printed by the installer before continuing.

Check that Curbpack was installed properly:

```bash
curbpack doctor
curbpack --help
```

## 3. Inspect the Reference Product

```bash
cd ~/curbpack-playground/cyberready-test-product
```

Besides the product source code and tests, the repository also contains the material used to exercise Curbpack, for example:

| Path | What it is |
| --- | --- |
| `src/` | Source code for the Glucose Log demo product. |
| `tests/` | Tests for the Glucose Log demo product. |
| `Makefile` | Build and test commands for the Glucose Log product. It belongs to the product itself and is not part of Curbpack. |
| `README.md` | README for the Glucose Log reference product. |
| `docs/` | Product documentation. Some of this documentation is also used as evidence for claims checked by Curbpack. |
| **`.curbpack.json`** | The product's Curbpack configuration. This is the main connection between the product repository and Curbpack and identifies the packs selected for this product. |
| **`curbpack-ref.txt`** | Points to the Curbpack version this reference product is intended to be compatible with. |
| **`external_test/curbpack/packs/`** | Frozen copies of the pack definitions used for these exercises. The other parts of `external_test/` contain Curbpack-specific test material and can be ignored during this walkthrough. |

The file `.curbpack.json` tells Curbpack to use `house-policy` and `medtech-iec62304`.

`medtech-iec62304` extends another pack, `cra-baseline`, so that pack is also included in the checks.

For this reference product, the corresponding pack definitions are available here:

```text
external_test/curbpack/packs/
├── house-policy/
├── cra-baseline/
└── medtech-iec62304/
```

Tell Curbpack to use these local pack definitions:

```bash
export CURBPACK_PACKS_DIR="$PWD/external_test/curbpack/packs"
```

Before running a check, look at the pack definitions and the claims they define, and try to relate those claims manually to the evidence available in the product.

For example, the reference product contains evidence in files such as:

```text
SECURITY.md
.well-known/security.txt
docs/annex-vii/risk_assessment.md
docs/annex-vii/support_period.md
docs/annex-vii/user_manual_security.md
docs/incident/art14-path.md
docs/medtech/software_safety_class.md
docs/medtech/soup_list.md
docs/medtech/problem_resolution.md
package.json
```

The idea is to see the relationship between a rule in a pack, the claim made for this product, and the repository evidence used to support that claim.

## 4. Run Curbpack on the Unchanged Reference Product

The repository is currently in its known-good reference state. Before changing anything, run Curbpack once so that you have a baseline to compare with.

First let Curbpack inspect the repository:

```bash
curbpack scan
```

The scan shows what Curbpack can find in the current repository and which evidence is available for the selected packs.

Then evaluate the repository against those packs:

```bash
curbpack check
```

At this point, nothing has been deliberately broken.

Pick one rule from the output and try to connect the three parts manually:

1. Find the rule in one of the selected packs.
2. Find the repository file or other evidence associated with that rule.
3. Find the corresponding result reported by Curbpack.

The important relationship is:

```text
pack rule
   ↓
claim about the product
   ↓
repository evidence
   ↓
check result
```

Now you know how it looks when everything is fine. Next, change the repository to break one of the rules and run exactly the same check again to see how Curbpack reports missing evidence.

## 5. Remove Evidence and Run the Check Again

Start with a very simple change: remove one piece of evidence.

`SECURITY.md` is part of the evidence in the reference product. Move it out of the way:

```bash
mv SECURITY.md SECURITY.md.bak
```

Run Curbpack again:

```bash
curbpack scan
curbpack check
```

Compare the result with the baseline.

The packs have not changed. The Curbpack configuration has not changed. Only the repository evidence has changed.

Look for the rule whose result changed because `SECURITY.md` is no longer available.

Restore the file:

```bash
mv SECURITY.md.bak SECURITY.md
```

Run the check once more:

```bash
curbpack check
```

The corresponding result should return to its original state.

This is the basic idea behind continuously checking repository evidence: if required evidence is accidentally removed in a later change, Curbpack can detect that the repository no longer satisfies the corresponding rule.

## 6. Change Evidence without Removing the File

A file can still exist while no longer containing the evidence expected by a rule.

Open:

```text
docs/medtech/software_safety_class.md
```

Find the section:

```text
## Classification Rationale
```

Temporarily remove that heading so that it no longer matches the expected structure.

Now run:

```bash
curbpack scan
curbpack check
```

Compare the result with the baseline.

This time the file still exists, but some of its expected content has changed.

When you are done, restore the original file:

```bash
git restore docs/medtech/software_safety_class.md
```

Then check again:

```bash
curbpack check
```

## 7. Inspect the Rule Behind the Result

Now go back to the pack definitions under:

```text
external_test/curbpack/packs/
```

Find the rule involved in one of the experiments above.

Compare what the rule asks for with:

- the claim made for the product;
- the repository evidence used to support that claim;
- the result reported by Curbpack.

The purpose of the reference product is to make these relationships small enough to inspect manually.

## 8. What You Have Tested

You have now changed the repository in two simple ways:

- evidence was removed completely;
- evidence remained, but expected content was changed.

In both cases, the packs stayed the same and you ran the same Curbpack checks.

Only the repository changed.

That is the central experiment:

```text
selected packs
     +
current product repository
     ↓
Curbpack
     ↓
results showing whether the current evidence satisfies the selected rules
```

## 9. Restore the Reference Product

If you have made other changes during the walkthrough, restore the repository to its checked-in state:

```bash
git restore .
```

Then verify the baseline again:

```bash
curbpack check
```

## 10. Next: Try Curbpack on Your Own Repository

The reference product already contains example packs, claims, and evidence so that their relationships can be inspected safely.

The next step is to use Curbpack with a real product repository and decide which packs apply and how the product's real evidence relates to their rules.

Continue with the [Developer guide](developers.md).
