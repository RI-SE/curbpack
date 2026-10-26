# Testing curbcheck

This is curbcheck's verification. Studio's functional suite is `make test`; start there from [Development](../development/README.md).

Follow the documents in this order. Do not start in a suite file.

1. [Verification strategy](strategy.md)
2. [Requirement traceability](requirements_traceability.md)
3. [Test setup](procedures/README.md) — start the verification run here
4. [Carried cases](procedures/cases.md)
5. [Outside ids](outside.md)
6. Copied suite procedures under [tests/check/suites/](../../tests/check/suites/) and [tests/check/docs/](../../tests/check/docs/)

## Start a verification run

From the Studio repository root, once per run:

```sh
make start-verification-run
# or non-interactive:
CONFIRM_TMP_WIPE=1 make start-verification-run
```

That clones the pin in `tests/cyberready-test-product.pin` into `tmp/cyberready-test-product` and writes `tmp/verification-run.sh`. Then, still from the Studio root:

```sh
source tmp/verification-run.sh
```

That prints `Verification run configuration: OK`, deletes the clone, and clones it again at the pin. Do not export `CURBPACK_PACKS_DIR`. Do not run `curbpack check`. Do not archive a local product checkout. Do not edit the reference product. `tmp/` is not committed.

## Run the carried checks

After the source above, the mechanical steps are in [procedures/README.md](procedures/README.md). In short: apply R1 with the Studio fixture `setup.sh`, write `curbpack.json`, copy the seven claim files from the fixture's `claims/`, and run:

```sh
python3 -m checks \
  --repo "$REFERENCE_PRODUCT_ROOT" \
  --packs "$REFERENCE_PRODUCT_ROOT/external_test/curbpack-studio/packs" \
  --out "$REFERENCE_PRODUCT_ROOT/run-result.json"
```

Exit 0 for that slice requires stdout `claims 7 exit 0` and no claim status `fail`. Manual rows are in [tests/check/manual.md](../../tests/check/manual.md). They are not a pass.

`make test-curbcheck` runs that same sequence for CI after it starts the verification run. A person testing by the book starts with `make start-verification-run` and `source tmp/verification-run.sh` first.

[Test records](generated_test_record_template.md) are blank copies kept outside this repository. [Code review](procedures/2_code_review_procedures.md) is not a carried case.
