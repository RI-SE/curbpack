# 1. Pack inputs

This file defines the `PF-*` dimension of the
[controlled test prerequisites](README.md).

Pack-template instantiation is **not yet specified**. Do not invent commands,
fields or instantiation steps. This procedure can be completed after pack
templates exist as a documented, runnable mechanism.

Until then, verification runs the **reference test product** setup in [0_controlled_repo_setup.md](0_controlled_repo_setup.md). Applying the same suites to another target repository is part of the verification model but is NOT CURRENTLY EXECUTABLE until a documented, repeatable pack-instantiation mechanism exists. Record pack-template instantiation as Not applicable until that mechanism exists.

How to start a verification run is [Prepare a verification run](README.md#prepare-a-verification-run).

## Intended template procedure (not executable)

1. List pack templates delivered with the frozen Curbpack release; identify each by commit hash.
2. Select the target repository.
3. Apply each template’s documented purpose, prerequisites and applicability. Record Applicable or Not applicable on the [test record](../generated_test_record_template.md) copy for that instance, with a reason for every Not applicable.
4. Instantiate only values the template marks as repository-specific. Do not change template semantics.
5. Commit the approved pack instance; record its hash; freeze expected structural results before execution.

The reviewer must not invent a substitute for a missing template mechanism.

<a id="pf-01"></a>

## PF-01

Glucose Log carries frozen pack *copies* and claim maps under `external_test/curbpack/packs/` (`house-policy`, `cra-baseline`, `medtech-iec62304`). Same pack ids as embed, so:

```bash
export CURBPACK_PACKS_DIR=/path/to/cyberready-test-product/external_test/curbpack/packs
curbpack check
```

That is the reference-product pack set. It is not instantiation onto a third repository and not a pack-template product.

`.curbpack.json` on Glucose Log still lists `house-policy` and `medtech-iec62304` (CRA via `extends`).

## Pack input registry

Pack inputs stay separate from R-states. Malformed variants are created only when a named test case requires them.

| ID | Pack input | Preparation status | Implementation |
|---|---|---|---|
| PF-01 | Reference-product pack set | SCRIPTED | Reference-product copies above; select them with `CURBPACK_PACKS_DIR` |
| PF-02 | Second representative instantiated product pack | NOT YET SPECIFIED | Composition exists as medtech extends CRA, but no second product instance or template mechanism exists |
| PF-03 | Invalid or modified variant named by a case | SCRIPTED where a named fixture exists; otherwise NOT YET SPECIFIED | PK-004, PK-005, and FS-001 use `testdata/adversarial/packs/` (`unknown-check`, `bad-regex`, `path-traversal`) |

## When templates land

Replace the not-yet-specified procedure with documented instantiate-and-adapt
steps only after that mechanism exists. Do not copy Glucose Log files into a
customer repository as a substitute for templates.
