# Migrated verification suite

Run this from the Studio repository root. `<prepared-repo>` is a checkout outside this repository.

```sh
python3 -m checks --repo <prepared-repo> --packs docs/reference/test-packs --out <prepared-repo>/run-result.json
```

`--packs` is the directory `docs/reference/test-packs`. The pack ids are in `<prepared-repo>/curbpack.json`, not in that flag. The runner reads `curbpack.json` and `<prepared-repo>/claims/`. It does not read `.curbpack.json` or `CURBPACK_PACKS_DIR`.

Exit 0 is a pass of the suite only when stdout contains `claims 7 exit 0` and no claim status is `fail`. The pass count is 7. The fail count is 0. Those seven ids, and the expected status `pass` next to each one, are in [procedures/cases.md](procedures/cases.md).

## Prepare the repo

The steps are in [procedures/README.md](procedures/README.md). In short: archive reference-product commit `dee885ffb421e4646fea07fbb4a629616c09efc6` into a temporary directory outside this repository, write `curbpack.json` with packs `cra-baseline`, `house-policy`, and `medtech-iec62304`, copy the seven carried claim files into `claims/`, and commit that tree in the temporary repo. Delete the temporary repo after the run. Do not edit the reference product.

## Reading order

1. [Verification strategy](strategy.md) — what this suite runs.
2. [Requirement traceability](requirements_traceability.md) — every `MUST-*` id, and that no carried case names it.
3. [Test setup](procedures/README.md) — R1–R7, PF-01–PF-17, and how the suite repo is prepared.
4. [Carried cases](procedures/cases.md) — the seven ids, expected status `pass`, and the check arguments.
5. [Outside ids](outside.md) — ids this suite does not pass. That list is not a pass.

[Test records](generated_test_record_template.md) are blank copies kept outside this repository. [Code review](procedures/2_code_review_procedures.md) is not a carried case.
