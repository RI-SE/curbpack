# Testing curbcheck

This is curbcheck's verification. Studio's functional suite is `make test`; start there from [Development](../development/README.md).

From the Studio repository root:

```sh
make test-curbcheck
```

That clones the pin in `tests/cyberready-test-product.pin` into `tmp/cyberready-test-product`, sources `tmp/verification-run.sh`, applies `./external_test/curbpack/setup.sh R1 --commit` on the clone, writes `curbpack.json`, copies the seven claim files, and runs `python3 -m checks`. Exit 0 for that slice requires stdout `claims 7 exit 0` and no claim status `fail`. It prints the manual rows in [tests/check/manual.md](../../tests/check/manual.md). Those rows are not a pass. The copied procedures are [tests/check/suites/](../../tests/check/suites/) and [tests/check/docs/procedures/](../../tests/check/docs/procedures/). A procedure that still calls `curbpack` is reported outside and is not a pass.

Do not export `CURBPACK_PACKS_DIR`. Do not run `curbpack check`. Do not archive a local product checkout. Do not edit the reference product. `tmp/` is not committed.

The steps are also in [procedures/README.md](procedures/README.md).

## Reading order

1. [Verification strategy](strategy.md) — what this suite runs.
2. [Requirement traceability](requirements_traceability.md) — every `MUST-*` id, and that no carried case names it.
3. [Test setup](procedures/README.md) — R1–R7, PF-01–PF-17, and how the suite repo is prepared.
4. [Carried cases](procedures/cases.md) — the seven ids, expected status `pass`, and the check arguments.
5. [Outside ids](outside.md) — ids this suite does not pass. That list is not a pass.

[Test records](generated_test_record_template.md) are blank copies kept outside this repository. [Code review](procedures/2_code_review_procedures.md) is not a carried case.
